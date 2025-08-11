import httpx
import structlog
from typing import Dict, Any, Optional
from app.core.config import settings
from app.models.github import GitHubAPIResponse, GitHubCommentCreate, GitHubCommentUpdate

logger = structlog.get_logger()

class GitHubService:
    """Service for GitHub API interactions."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.GITHUB_TOKEN
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    async def create_pr_comment(
        self, 
        repo: str, 
        pr_number: int, 
        body: str
    ) -> GitHubAPIResponse:
        """Create a comment on a pull request."""
        url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/comments"
        comment_data = GitHubCommentCreate(body=body)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=comment_data.dict(),
                    headers=self.headers,
                    timeout=30.0
                )
                
                logger.info(
                    "Created PR comment",
                    repo=repo,
                    pr_number=pr_number,
                    status_code=response.status_code
                )
                
                return GitHubAPIResponse(
                    status_code=response.status_code,
                    data=response.json() if response.content else {},
                    headers=dict(response.headers)
                )
            
            except httpx.RequestError as e:
                logger.error("Failed to create PR comment", error=str(e))
                return GitHubAPIResponse(
                    status_code=500,
                    data={"error": str(e)}
                )
    
    async def update_pr_comment(
        self, 
        repo: str, 
        comment_id: int, 
        body: str
    ) -> GitHubAPIResponse:
        """Update an existing PR comment."""
        url = f"{self.base_url}/repos/{repo}/issues/comments/{comment_id}"
        comment_data = GitHubCommentUpdate(body=body)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(
                    url,
                    json=comment_data.dict(),
                    headers=self.headers,
                    timeout=30.0
                )
                
                logger.info(
                    "Updated PR comment",
                    repo=repo,
                    comment_id=comment_id,
                    status_code=response.status_code
                )
                
                return GitHubAPIResponse(
                    status_code=response.status_code,
                    data=response.json() if response.content else {},
                    headers=dict(response.headers)
                )
            
            except httpx.RequestError as e:
                logger.error("Failed to update PR comment", error=str(e))
                return GitHubAPIResponse(
                    status_code=500,
                    data={"error": str(e)}
                )
    
    async def get_pr_details(self, repo: str, pr_number: int) -> GitHubAPIResponse:
        """Get pull request details."""
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0
                )
                
                logger.info(
                    "Retrieved PR details",
                    repo=repo,
                    pr_number=pr_number,
                    status_code=response.status_code
                )
                
                return GitHubAPIResponse(
                    status_code=response.status_code,
                    data=response.json() if response.content else {},
                    headers=dict(response.headers)
                )
            
            except httpx.RequestError as e:
                logger.error("Failed to get PR details", error=str(e))
                return GitHubAPIResponse(
                    status_code=500,
                    data={"error": str(e)}
                )
    
    async def trigger_workflow(
        self, 
        repo: str, 
        workflow_id: str, 
        inputs: Dict[str, Any], 
        ref: str = "main"
    ) -> GitHubAPIResponse:
        """Trigger a GitHub Actions workflow."""
        url = f"{self.base_url}/repos/{repo}/actions/workflows/{workflow_id}/dispatches"
        
        payload = {
            "ref": ref,
            "inputs": inputs
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                logger.info(
                    "Triggered GitHub workflow",
                    repo=repo,
                    workflow_id=workflow_id,
                    status_code=response.status_code
                )
                
                return GitHubAPIResponse(
                    status_code=response.status_code,
                    data=response.json() if response.content else {},
                    headers=dict(response.headers)
                )
            
            except httpx.RequestError as e:
                logger.error("Failed to trigger workflow", error=str(e))
                return GitHubAPIResponse(
                    status_code=500,
                    data={"error": str(e)}
                )