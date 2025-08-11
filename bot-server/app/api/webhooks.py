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
        
        logger.debug("Raw webhook headers", headers=dict(headers))
        logger.debug("Raw payload size", size=len(raw_payload))
        
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
        
        logger.debug("Webhook payload structure", 
                    keys=list(payload.keys()),
                    repo_name=payload.get("repository", {}).get("full_name"),
                    pr_number=payload.get("pull_request", {}).get("number"),
                    comment_body=payload.get("comment", {}).get("body"))
        
        # Process PR comment events
        if event_type == "issue_comment" and is_pr_comment_event(payload):
            logger.debug("Processing PR comment event")
            background_tasks.add_task(process_pr_comment, payload)
        else:
            logger.debug("Skipping non-PR comment event", 
                        event_type=event_type,
                        is_pr_comment=is_pr_comment_event(payload))
        
        return {"status": "received"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing GitHub webhook", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

async def process_pr_comment(payload: dict):
    """Process PR comment for slash commands."""
    try:
        logger.debug("Starting PR comment processing", payload_keys=list(payload.keys()))
        
        # Parse webhook payload
        webhook_data = GitHubWebhookPayload(**payload)
        logger.debug("Parsed webhook payload successfully")
        
        if not webhook_data.comment:
            logger.debug("Missing comment data")
            logger.info("Skipping event without comment")
            return
            
        # For PR comments, we need either pull_request field or issue with pull_request
        pr_number = None
        if webhook_data.pull_request:
            pr_number = webhook_data.pull_request.number
        elif payload.get('issue', {}).get('pull_request'):
            # This is a PR comment sent as issue_comment
            pr_number = payload['issue']['number']
            
        logger.debug("PR number extraction", 
                    pr_number=pr_number,
                    has_top_level_pr=bool(webhook_data.pull_request),
                    has_issue_pr=bool(payload.get('issue', {}).get('pull_request')))
            
        if not pr_number:
            logger.debug("No PR number found - not a PR comment")
            logger.info("Skipping non-PR comment event") 
            return
        
        logger.debug("Comment data", 
                    comment_id=webhook_data.comment.id,
                    comment_body=webhook_data.comment.body[:100],
                    user=webhook_data.comment.user.login)
        
        # Extract slash command
        command_text = extract_slash_command(webhook_data.comment.body)
        logger.debug("Command extraction result", 
                    found_command=bool(command_text),
                    command_text=command_text)
        
        if not command_text:
            logger.info("No slash command found in comment")
            return
        
        # Create GitHub context
        github_context = GitHubContext(
            repository=webhook_data.repository.full_name,
            pull_request_number=pr_number,
            comment_id=webhook_data.comment.id,
            user=webhook_data.comment.user.login,
            installation_id=webhook_data.installation.get("id") if webhook_data.installation else None
        )
        
        logger.debug("Created GitHub context", 
                    repo=github_context.repository,
                    pr_number=github_context.pull_request_number,
                    user=github_context.user)
        
        # Process command
        processor = CommandProcessor()
        logger.debug("Processing command with CommandProcessor")
        await processor.process_command_from_github(command_text, github_context)
        
    except Exception as e:
        logger.error("Error processing PR comment", error=str(e), exc_info=True)