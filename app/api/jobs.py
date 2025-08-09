from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List
import structlog
import json
import asyncio

from app.services.job_manager import JobManager
from app.models.jobs import JobStatusUpdate

router = APIRouter()
logger = structlog.get_logger()

# Global job manager instance
job_manager = JobManager()

@router.get("/{job_id}/status")
async def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get the current status of a job."""
    logger.info("Job status requested", job_id=job_id)
    
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "job_type": job.job_type.value,
        "progress": job.progress.dict() if job.progress else None,
        "result": job.result.dict() if job.result else None,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "logs": job.logs[-10:] if job.logs else []  # Last 10 log entries
    }

@router.get("/active")
async def get_active_jobs() -> List[Dict[str, Any]]:
    """Get all active jobs."""
    active_jobs = await job_manager.get_active_jobs()
    return [
        {
            "job_id": job.job_id,
            "status": job.status.value,
            "job_type": job.job_type.value,
            "progress": job.progress.progress_percentage if job.progress else 0,
            "created_at": job.created_at.isoformat()
        }
        for job in active_jobs
    ]

@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str, payload: Dict[str, Any] = None):
    """Cancel a running job."""
    reason = payload.get("reason", "") if payload else ""
    success = await job_manager.cancel_job(job_id, reason)
    
    if success:
        return {"status": "cancelled", "job_id": job_id}
    else:
        raise HTTPException(status_code=404, detail="Job not found or cannot be cancelled")

@router.websocket("/ws/{job_id}")
async def websocket_job_updates(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time job updates."""
    await websocket.accept()
    logger.info("WebSocket connection established", job_id=job_id)
    
    try:
        while True:
            job = await job_manager.get_job(job_id)
            if job:
                update = JobStatusUpdate(
                    job_id=job.job_id,
                    status=job.status,
                    progress=job.progress,
                    message=job.logs[-1] if job.logs else ""
                )
                await websocket.send_text(update.json())
            else:
                await websocket.send_text(json.dumps({
                    "error": "Job not found",
                    "job_id": job_id
                }))
                break
            
            await asyncio.sleep(2)  # Update every 2 seconds
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed", job_id=job_id)

@router.get("/{job_id}/stream")
async def stream_job_updates(job_id: str):
    """Server-sent events endpoint for job updates."""
    async def generate_updates():
        while True:
            job = await job_manager.get_job(job_id)
            if job:
                update = JobStatusUpdate(
                    job_id=job.job_id,
                    status=job.status,
                    progress=job.progress,
                    message=job.logs[-1] if job.logs else ""
                )
                yield f"data: {update.json()}\n\n"
                
                # Stop streaming if job is completed/failed/cancelled
                if job.status.value in ["completed", "failed", "cancelled"]:
                    break
            else:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break
            
            await asyncio.sleep(2)  # Update every 2 seconds
    
    return StreamingResponse(
        generate_updates(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@router.post("/callback/{job_id}")
async def handle_job_callback(job_id: str, payload: Dict[str, Any]):
    """Handle callbacks from external systems."""
    logger.info("Job callback received", job_id=job_id, payload=payload)
    
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Process callback based on payload
    if payload.get("status") == "completed":
        # Handle external job completion
        job.add_log(f"External callback received: {payload.get('message', 'Job completed')}")
    elif payload.get("status") == "failed":
        job.add_log(f"External callback received: {payload.get('error', 'Job failed')}")
    else:
        job.add_log(f"External callback received: {json.dumps(payload)}")
    
    return {"status": "received", "job_id": job_id}