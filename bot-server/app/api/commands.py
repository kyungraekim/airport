from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
import structlog

from app.services.command_processor import CommandProcessor

router = APIRouter()
logger = structlog.get_logger()

class CommandExecuteRequest(BaseModel):
    command: str
    user_id: str = "api-user"

@router.post("/execute")
async def execute_command(
    request: CommandExecuteRequest,
    background_tasks: BackgroundTasks
):
    """Manually execute a slash command."""
    try:
        logger.info("Manual command execution requested", 
                   command=request.command, 
                   user_id=request.user_id)
        
        processor = CommandProcessor()
        job_id = await processor.process_manual_command(
            request.command, 
            request.user_id
        )
        
        if job_id:
            return {
                "status": "accepted",
                "command": request.command,
                "job_id": job_id
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid command format")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error executing command", error=str(e))
        raise HTTPException(status_code=500, detail="Command execution failed")