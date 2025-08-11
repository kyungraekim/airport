import structlog
from typing import Optional
from datetime import datetime

from app.models.commands import CommandConfig, CommandRequest, GitHubContext, CommandType
from app.models.jobs import Job, JobType
from app.utils.command_parser import CommandParser
from app.services.github_service import GitHubService
from app.services.job_manager import JobManager
from app.core.config import settings

logger = structlog.get_logger()

class CommandProcessor:
    """Process and execute slash commands."""
    
    def __init__(self):
        self.github_service = GitHubService()
        self.job_manager = JobManager()
    
    async def process_command_from_github(
        self, 
        command_text: str, 
        github_context: GitHubContext
    ):
        """Process a command received from GitHub PR comment."""
        try:
            logger.debug("Starting command processing", 
                        command=command_text,
                        repo=github_context.repository,
                        pr_number=github_context.pull_request_number)
            
            # Parse the command
            command_config = CommandParser.parse_command(command_text)
            logger.debug("Command parsing result", 
                        success=bool(command_config),
                        command_type=command_config.command_type if command_config else None)
            
            if not command_config:
                logger.debug("Invalid command, sending error response")
                await self._send_error_response(
                    github_context, 
                    f"Invalid command format: {command_text}"
                )
                return
            
            # Handle help command
            if command_config.command_type == CommandType.HELP:
                logger.debug("Processing HELP command")
                help_text = CommandParser.get_help_text()
                logger.debug("Generated help text", text_length=len(help_text))
                await self._send_response(github_context, help_text)
                return
            
            # Handle status command
            if command_config.command_type == CommandType.STATUS:
                logger.debug("Processing STATUS command")
                await self._handle_status_command(command_config, github_context)
                return
            
            # Create job for execution
            logger.debug("Creating job for command execution")
            job = await self._create_job_from_command(command_config, github_context)
            
            # Send initial response
            initial_message = f"""
🚀 **Command Accepted**

**Job ID:** `{job.job_id}`
**Command:** `{command_config.raw_command}`
**Status:** Starting execution...

I'll update this comment with progress. You can also check status with `/status --job={job.job_id}`
            """.strip()
            
            logger.debug("Sending initial job response", job_id=job.job_id)
            response = await self.github_service.create_pr_comment(
                repo=github_context.repository,
                pr_number=github_context.pull_request_number,
                body=initial_message
            )
            
            logger.debug("GitHub comment response", 
                        status_code=response.status_code,
                        success=response.status_code == 201)
            
            if response.status_code == 201:
                # Store comment ID for updates
                comment_id = response.data.get("id")
                job.external_job_ids["github_comment_id"] = str(comment_id)
                logger.debug("Stored comment ID for updates", comment_id=comment_id)
            else:
                logger.warning("Failed to create initial comment", 
                             status_code=response.status_code,
                             error=response.data)
            
            # Start job execution
            logger.debug("Starting job execution")
            await self.job_manager.start_job(job)
            
        except Exception as e:
            logger.error("Error processing command from GitHub", error=str(e), exc_info=True)
            await self._send_error_response(
                github_context, 
                f"Internal error processing command: {str(e)}"
            )
    
    async def process_manual_command(
        self, 
        command_text: str, 
        user_id: str
    ) -> Optional[str]:
        """Process a manually submitted command."""
        try:
            # Parse the command
            command_config = CommandParser.parse_command(command_text)
            if not command_config:
                return None
            
            # Handle help command
            if command_config.command_type == CommandType.HELP:
                return CommandParser.get_help_text()
            
            # Handle status command
            if command_config.command_type == CommandType.STATUS:
                return await self._handle_status_command_manual(command_config)
            
            # Create job for execution
            job = await self._create_job_from_command(command_config, None, user_id)
            
            # Start job execution
            await self.job_manager.start_job(job)
            
            return job.job_id
            
        except Exception as e:
            logger.error("Error processing manual command", error=str(e))
            return None
    
    async def _create_job_from_command(
        self, 
        command_config: CommandConfig, 
        github_context: Optional[GitHubContext] = None,
        user_id: Optional[str] = None
    ) -> Job:
        """Create a job from a parsed command."""
        # Determine job type
        job_type_mapping = {
            CommandType.TRAIN: JobType.TRAIN,
            CommandType.EVAL: JobType.EVAL,
            CommandType.TEST: JobType.TEST,
            CommandType.PIPELINE: JobType.PIPELINE,
        }
        
        job_type = job_type_mapping.get(command_config.command_type, JobType.TRAIN)
        
        # Create job
        job = Job(
            job_type=job_type,
            command_config=command_config.dict(),
            github_context=github_context.dict() if github_context else None
        )
        
        # Set user information
        if github_context:
            job.add_log(f"Command received from GitHub user: {github_context.user}")
        elif user_id:
            job.add_log(f"Command received from user: {user_id}")
        
        logger.info("Created job from command", 
                   job_id=job.job_id, 
                   command_type=command_config.command_type)
        
        return job
    
    async def _handle_status_command(
        self, 
        command_config: CommandConfig, 
        github_context: GitHubContext
    ):
        """Handle status command from GitHub."""
        if command_config.job_id:
            job = await self.job_manager.get_job(command_config.job_id)
            if job:
                status_text = self._format_job_status(job)
            else:
                status_text = f"❌ Job `{command_config.job_id}` not found"
        else:
            # Show all active jobs
            active_jobs = await self.job_manager.get_active_jobs()
            if active_jobs:
                status_text = "**Active Jobs:**\n\n" + "\n".join([
                    f"- `{job.job_id}` - {job.job_type} - {job.status}"
                    for job in active_jobs
                ])
            else:
                status_text = "No active jobs found"
        
        await self._send_response(github_context, status_text)
    
    async def _handle_status_command_manual(
        self, 
        command_config: CommandConfig
    ) -> str:
        """Handle status command for manual requests."""
        if command_config.job_id:
            job = await self.job_manager.get_job(command_config.job_id)
            if job:
                return self._format_job_status(job)
            else:
                return f"Job {command_config.job_id} not found"
        else:
            # Show all active jobs
            active_jobs = await self.job_manager.get_active_jobs()
            if active_jobs:
                return "Active Jobs:\n" + "\n".join([
                    f"- {job.job_id} - {job.job_type} - {job.status}"
                    for job in active_jobs
                ])
            else:
                return "No active jobs found"
    
    def _format_job_status(self, job: Job) -> str:
        """Format job status for display."""
        status_emoji = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "⏹️",
        }
        
        emoji = status_emoji.get(job.status.value, "❓")
        
        status_text = f"""
{emoji} **Job Status: `{job.job_id}`**

**Type:** {job.job_type.value}
**Status:** {job.status.value}
**Created:** {job.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
        """.strip()
        
        if job.started_at:
            status_text += f"\n**Started:** {job.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        if job.completed_at:
            status_text += f"\n**Completed:** {job.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        if job.progress:
            status_text += f"\n**Progress:** {job.progress.progress_percentage:.1f}% - {job.progress.current_step}"
        
        if job.result and job.result.error_message:
            status_text += f"\n**Error:** {job.result.error_message}"
        
        # Show recent logs
        if job.logs:
            recent_logs = job.logs[-3:]  # Last 3 log entries
            status_text += "\n\n**Recent Logs:**\n" + "\n".join([f"- {log}" for log in recent_logs])
        
        return status_text
    
    async def _send_response(self, github_context: GitHubContext, message: str):
        """Send a response to the GitHub PR."""
        logger.debug("Sending response to GitHub", 
                    repo=github_context.repository,
                    pr_number=github_context.pull_request_number,
                    message_length=len(message))
        
        response = await self.github_service.create_pr_comment(
            repo=github_context.repository,
            pr_number=github_context.pull_request_number,
            body=message
        )
        
        logger.debug("GitHub response received", 
                    status_code=response.status_code,
                    success=response.status_code == 201)
        
        if response.status_code != 201:
            logger.error("Failed to send GitHub response", 
                        status_code=response.status_code,
                        error=response.data)
        else:
            logger.debug("Successfully sent response to GitHub")
    
    async def _send_error_response(self, github_context: GitHubContext, error_message: str):
        """Send an error response to the GitHub PR."""
        error_text = f"""
❌ **Command Error**

{error_message}

Use `/help` to see available commands.
        """.strip()
        
        await self._send_response(github_context, error_text)