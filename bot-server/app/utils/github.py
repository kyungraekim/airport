import hashlib
import hmac
from typing import Optional
import structlog

logger = structlog.get_logger()

def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    if not secret:
        logger.warning("GitHub webhook secret not configured, skipping verification")
        return True
    
    if not signature:
        logger.error("No signature provided in GitHub webhook")
        return False
    
    # GitHub sends signature as 'sha256=<hash>'
    if not signature.startswith('sha256='):
        logger.error("Invalid signature format", signature=signature)
        return False
    
    expected_signature = signature[7:]  # Remove 'sha256=' prefix
    
    # Calculate expected signature
    computed_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(computed_signature, expected_signature)

def extract_slash_command(comment_body: str) -> Optional[str]:
    """Extract slash command from GitHub comment body."""
    lines = comment_body.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('/'):
            # Extract the command (first word after /)
            parts = line.split()
            if len(parts) > 0:
                return line
    
    return None

def detect_comment_context(payload: dict) -> Optional[str]:
    """Detect the context type from GitHub webhook payload.
    
    Returns:
        'issue' for issue comments (not on PRs)
        'pr' for PR comments 
        None if not a valid comment event
    """
    import structlog
    from app.models.commands import ContextType
    logger = structlog.get_logger()
    
    # Must be a comment creation event
    if payload.get('action') != 'created' or 'comment' not in payload:
        logger.debug("Not a comment creation event")
        return None
    
    # Check if this is an issue comment
    if 'issue' in payload:
        issue = payload['issue']
        
        # If issue has pull_request field, it's a PR comment
        if 'pull_request' in issue:
            logger.debug("Detected PR comment via issue.pull_request")
            return ContextType.PULL_REQUEST
        else:
            # Regular issue comment
            logger.debug("Detected Issue comment")
            return ContextType.ISSUE
    
    # Direct PR comment (rare case)
    elif 'pull_request' in payload:
        logger.debug("Detected PR comment via top-level pull_request")
        return ContextType.PULL_REQUEST
    
    logger.debug("Could not determine comment context")
    return None

def is_comment_event(payload: dict) -> bool:
    """Check if webhook payload is any comment event (issue or PR)."""
    return detect_comment_context(payload) is not None

# Legacy function for backward compatibility
def is_pr_comment_event(payload: dict) -> bool:
    """Check if webhook payload is a PR comment event."""
    context = detect_comment_context(payload)
    from app.models.commands import ContextType
    return context == ContextType.PULL_REQUEST