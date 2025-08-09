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

def is_pr_comment_event(payload: dict) -> bool:
    """Check if webhook payload is a PR comment event."""
    return (
        payload.get('action') == 'created' and
        'comment' in payload and
        'pull_request' in payload
    )