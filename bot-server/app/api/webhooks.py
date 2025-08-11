from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings
from app.models.github import GitHubWebhookPayload
from app.models.commands import CommandRequest, GitHubContext
from app.utils.github import verify_github_signature, extract_slash_command, is_pr_comment_event
from app.services.command_processor import CommandProcessor

router = APIRouter()
logger = structlog.get_logger()

@router.post("/github")
async def handle_github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Handle GitHub webhook events, particularly PR comments."""
    try:
        # Get raw payload for signature verification
        raw_payload = await request.body()
        headers = request.headers
        
        # Verify webhook signature
        signature = headers.get("X-Hub-Signature-256", "")
        if not verify_github_signature(raw_payload, signature, settings.GITHUB_WEBHOOK_SECRET):
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse JSON payload
        payload = await request.json()
        event_type = headers.get("X-GitHub-Event")
        
        logger.info("GitHub webhook received", 
                   event_type=event_type,
                   action=payload.get("action"))
        
        # Process PR comment events
        if event_type == "issue_comment" and is_pr_comment_event(payload):
            background_tasks.add_task(process_pr_comment, payload)
        
        return {"status": "received"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing GitHub webhook", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

async def process_pr_comment(payload: dict):
    """Process PR comment for slash commands."""
    try:
        # Parse webhook payload
        webhook_data = GitHubWebhookPayload(**payload)
        
        if not webhook_data.comment or not webhook_data.pull_request:
            logger.info("Skipping non-PR comment event")
            return
        
        # Extract slash command
        command_text = extract_slash_command(webhook_data.comment.body)
        if not command_text:
            logger.info("No slash command found in comment")
            return
        
        # Create GitHub context
        github_context = GitHubContext(
            repository=webhook_data.repository.full_name,
            pull_request_number=webhook_data.pull_request.number,
            comment_id=webhook_data.comment.id,
            user=webhook_data.comment.user.login,
            installation_id=webhook_data.installation.get("id") if webhook_data.installation else None
        )
        
        # Process command
        processor = CommandProcessor()
        await processor.process_command_from_github(command_text, github_context)
        
    except Exception as e:
        logger.error("Error processing PR comment", error=str(e))