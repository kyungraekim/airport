import asyncio
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from app.models.jobs import Job, JobStatus, JobResult, JobType
from app.models.commands import CommandType
from app.core.config import settings
from app.services.github_service import GitHubService

logger = structlog.get_logger()

class JobManager:
    """Manage job lifecycle and execution."""
    
    def __init__(self):
        # In-memory job storage (TODO: replace with database)
        self._jobs: Dict[str, Job] = {}
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self.github_service = GitHubService()
        self._job_lock = asyncio.Lock()
    
    async def start_job(self, job: Job) -> bool:
        """Start executing a job."""
        try:
            async with self._job_lock:
                if job.job_id in self._jobs:
                    logger.error("Job already exists", job_id=job.job_id)
                    return False
                
                # Store job
                self._jobs[job.job_id] = job
                job.mark_started()
                
                # Create background task
                task = asyncio.create_task(self._execute_job(job))
                self._active_tasks[job.job_id] = task
                
                logger.info("Job started", job_id=job.job_id, job_type=job.job_type)
                return True
        
        except Exception as e:
            logger.error("Error starting job", job_id=job.job_id, error=str(e))
            return False
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self._jobs.get(job_id)
    
    async def get_active_jobs(self) -> List[Job]:
        """Get all active jobs."""
        return [
            job for job in self._jobs.values()
            if job.status in [JobStatus.PENDING, JobStatus.RUNNING]
        ]
    
    async def cancel_job(self, job_id: str, reason: str = "") -> bool:
        """Cancel a running job."""
        try:
            async with self._job_lock:
                job = self._jobs.get(job_id)
                if not job:
                    return False
                
                # Cancel the task
                if job_id in self._active_tasks:
                    self._active_tasks[job_id].cancel()
                    del self._active_tasks[job_id]
                
                # Mark job as cancelled
                job.mark_cancelled(reason)
                
                logger.info("Job cancelled", job_id=job_id, reason=reason)
                return True
        
        except Exception as e:
            logger.error("Error cancelling job", job_id=job_id, error=str(e))
            return False
    
    async def _execute_job(self, job: Job):
        """Execute a job based on its type."""
        try:
            job.add_log(f"Starting {job.job_type} job execution")
            
            if job.job_type == JobType.TRAIN:
                await self._execute_train_job(job)
            elif job.job_type == JobType.EVAL:
                await self._execute_eval_job(job)
            elif job.job_type == JobType.TEST:
                await self._execute_test_job(job)
            elif job.job_type == JobType.PIPELINE:
                await self._execute_pipeline_job(job)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")
        
        except asyncio.CancelledError:
            job.add_log("Job execution cancelled")
            logger.info("Job execution cancelled", job_id=job.job_id)
        except Exception as e:
            error_msg = f"Job execution failed: {str(e)}"
            job.add_log(error_msg)
            job.mark_completed(JobResult(success=False, error_message=error_msg))
            logger.error("Job execution failed", job_id=job.job_id, error=str(e))
            await self._notify_job_completion(job)
        finally:
            # Clean up task reference
            if job.job_id in self._active_tasks:
                del self._active_tasks[job.job_id]
    
    async def _execute_train_job(self, job: Job):
        """Execute a training job."""
        job.update_progress("Initializing training", 0, 5, "Setting up training environment")
        await asyncio.sleep(2)  # Simulate setup time
        
        # Mock training steps
        steps = ["Data loading", "Model setup", "Training", "Validation", "Saving results"]
        
        for i, step in enumerate(steps):
            if job.status == JobStatus.CANCELLED:
                return
            
            job.update_progress(step, i, len(steps), f"Executing {step}")
            await self._notify_job_progress(job)
            
            # Simulate work with varying duration
            await asyncio.sleep(3 + i)  # Simulate varying execution time
        
        # Complete job
        result = JobResult(
            success=True,
            output={
                "model_path": "/tmp/trained_model.bin",
                "config_path": "/tmp/training_config.json"
            },
            metrics={
                "final_loss": 0.0234,
                "accuracy": 0.945,
                "training_time": 300
            },
            artifacts=["model.bin", "config.json", "training_log.txt"]
        )
        
        job.mark_completed(result)
        await self._notify_job_completion(job)
    
    async def _execute_eval_job(self, job: Job):
        """Execute an evaluation job."""
        job.update_progress("Initializing evaluation", 0, 4, "Loading models for evaluation")
        await asyncio.sleep(1)
        
        steps = ["Loading models", "Running evaluation", "Computing metrics", "Generating report"]
        
        for i, step in enumerate(steps):
            if job.status == JobStatus.CANCELLED:
                return
            
            job.update_progress(step, i, len(steps), f"Executing {step}")
            await self._notify_job_progress(job)
            await asyncio.sleep(2 + i)
        
        # Complete job
        result = JobResult(
            success=True,
            output={
                "evaluation_report": "/tmp/eval_report.json",
                "comparison_chart": "/tmp/model_comparison.png"
            },
            metrics={
                "baseline_accuracy": 0.923,
                "incoming_accuracy": 0.945,
                "improvement": 0.022
            },
            artifacts=["eval_report.json", "comparison.png"]
        )
        
        job.mark_completed(result)
        await self._notify_job_completion(job)
    
    async def _execute_test_job(self, job: Job):
        """Execute a test job."""
        job.update_progress("Initializing tests", 0, 3, "Setting up test environment")
        await asyncio.sleep(1)
        
        steps = ["Running smoke tests", "Running integration tests", "Generating test report"]
        
        for i, step in enumerate(steps):
            if job.status == JobStatus.CANCELLED:
                return
            
            job.update_progress(step, i, len(steps), f"Executing {step}")
            await self._notify_job_progress(job)
            await asyncio.sleep(2)
        
        # Complete job
        result = JobResult(
            success=True,
            output={
                "test_report": "/tmp/test_report.xml",
                "coverage_report": "/tmp/coverage.html"
            },
            metrics={
                "tests_passed": 45,
                "tests_failed": 0,
                "coverage": 0.87
            },
            artifacts=["test_report.xml", "coverage.html"]
        )
        
        job.mark_completed(result)
        await self._notify_job_completion(job)
    
    async def _execute_pipeline_job(self, job: Job):
        """Execute a pipeline job."""
        job.update_progress("Initializing pipeline", 0, 1, "Planning pipeline steps")
        await asyncio.sleep(1)
        
        # TODO: Parse pipeline steps from command config and execute them sequentially
        # For now, simulate a simple train->eval pipeline
        
        # Simulate training
        job.update_progress("Training model", 1, 3, "Executing training step")
        await asyncio.sleep(5)
        
        # Simulate evaluation
        job.update_progress("Evaluating model", 2, 3, "Executing evaluation step")
        await asyncio.sleep(3)
        
        # Complete pipeline
        result = JobResult(
            success=True,
            output={
                "pipeline_report": "/tmp/pipeline_report.json",
                "final_model": "/tmp/final_model.bin"
            },
            metrics={
                "pipeline_duration": 480,
                "steps_completed": 2,
                "final_accuracy": 0.952
            },
            artifacts=["pipeline_report.json", "final_model.bin", "logs.txt"]
        )
        
        job.mark_completed(result)
        await self._notify_job_completion(job)
    
    async def _notify_job_progress(self, job: Job):
        """Notify about job progress updates."""
        try:
            # Update GitHub comment if available
            if (job.github_context and 
                job.external_job_ids.get("github_comment_id")):
                
                await self._update_github_comment(job)
            
            logger.info("Job progress updated", 
                       job_id=job.job_id, 
                       progress=job.progress.progress_percentage if job.progress else 0)
        
        except Exception as e:
            logger.error("Error notifying job progress", job_id=job.job_id, error=str(e))
    
    async def _notify_job_completion(self, job: Job):
        """Notify about job completion."""
        try:
            # Update GitHub comment if available
            if (job.github_context and 
                job.external_job_ids.get("github_comment_id")):
                
                await self._update_github_comment(job, final=True)
            
            logger.info("Job completed", 
                       job_id=job.job_id, 
                       status=job.status,
                       success=job.result.success if job.result else False)
        
        except Exception as e:
            logger.error("Error notifying job completion", job_id=job.job_id, error=str(e))
    
    async def _update_github_comment(self, job: Job, final: bool = False):
        """Update GitHub PR comment with job status."""
        try:
            if not job.github_context:
                return
            
            comment_id = int(job.external_job_ids.get("github_comment_id", "0"))
            if not comment_id:
                return
            
            # Format status message
            if final and job.result:
                message = self._format_final_job_message(job)
            else:
                message = self._format_progress_job_message(job)
            
            # Update the comment
            response = await self.github_service.update_pr_comment(
                repo=job.github_context["repository"],
                comment_id=comment_id,
                body=message
            )
            
            if response.status_code != 200:
                logger.error("Failed to update GitHub comment", 
                           status_code=response.status_code,
                           error=response.data)
        
        except Exception as e:
            logger.error("Error updating GitHub comment", job_id=job.job_id, error=str(e))
    
    def _format_progress_job_message(self, job: Job) -> str:
        """Format progress message for GitHub comment."""
        status_emoji = "🔄"
        
        message = f"""
{status_emoji} **Job In Progress**

**Job ID:** `{job.job_id}`
**Command:** `{job.command_config.get('raw_command', 'N/A')}`
**Status:** {job.status.value}
        """.strip()
        
        if job.progress:
            progress_bar = "█" * int(job.progress.progress_percentage // 10) + "░" * (10 - int(job.progress.progress_percentage // 10))
            message += f"""

**Progress:** {job.progress.progress_percentage:.1f}% [{progress_bar}]
**Current Step:** {job.progress.current_step}
**Steps:** {job.progress.completed_steps}/{job.progress.total_steps}
            """.strip()
        
        message += f"\n\n*Last updated: {datetime.utcnow().strftime('%H:%M:%S UTC')}*"
        
        return message
    
    def _format_final_job_message(self, job: Job) -> str:
        """Format final completion message for GitHub comment."""
        if job.result and job.result.success:
            status_emoji = "✅"
            status_text = "Completed Successfully"
        else:
            status_emoji = "❌"
            status_text = "Failed"
        
        message = f"""
{status_emoji} **Job {status_text}**

**Job ID:** `{job.job_id}`
**Command:** `{job.command_config.get('raw_command', 'N/A')}`
**Status:** {job.status.value}
**Duration:** {self._format_duration(job.created_at, job.completed_at)}
        """.strip()
        
        if job.result:
            if job.result.success and job.result.metrics:
                message += "\n\n**Results:**\n" + "\n".join([
                    f"- **{key}:** {value}" for key, value in job.result.metrics.items()
                ])
            
            if job.result.artifacts:
                message += "\n\n**Generated Artifacts:**\n" + "\n".join([
                    f"- {artifact}" for artifact in job.result.artifacts
                ])
            
            if not job.result.success and job.result.error_message:
                message += f"\n\n**Error:** {job.result.error_message}"
        
        message += f"\n\n*Completed at: {job.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}*"
        
        return message
    
    def _format_duration(self, start: datetime, end: Optional[datetime]) -> str:
        """Format job duration."""
        if not end:
            duration = datetime.utcnow() - start
        else:
            duration = end - start
        
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"