from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

class GitHubUser(BaseModel):
    """GitHub user information."""
    login: str
    id: int
    avatar_url: str
    html_url: str

class GitHubRepository(BaseModel):
    """GitHub repository information."""
    id: int
    name: str
    full_name: str
    html_url: str
    clone_url: str
    default_branch: str

class GitHubPullRequest(BaseModel):
    """GitHub pull request information."""
    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: str
    html_url: str
    head_ref: str
    base_ref: str
    user: GitHubUser

class GitHubComment(BaseModel):
    """GitHub PR comment information."""
    id: int
    body: str
    user: GitHubUser
    created_at: datetime
    updated_at: datetime
    html_url: str

class GitHubWebhookPayload(BaseModel):
    """GitHub webhook payload structure."""
    action: str
    repository: GitHubRepository
    pull_request: Optional[GitHubPullRequest] = None
    comment: Optional[GitHubComment] = None
    sender: GitHubUser
    installation: Optional[Dict[str, Any]] = None

class GitHubAPIResponse(BaseModel):
    """Generic GitHub API response."""
    status_code: int
    data: Dict[str, Any]
    headers: Dict[str, str] = Field(default_factory=dict)

class GitHubCommentCreate(BaseModel):
    """Request to create a GitHub comment."""
    body: str
    
class GitHubCommentUpdate(BaseModel):
    """Request to update a GitHub comment."""
    body: str