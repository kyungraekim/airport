from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

class GitHubUser(BaseModel):
    """GitHub user information."""
    login: str
    id: Optional[int] = None
    avatar_url: Optional[str] = None
    html_url: Optional[str] = None

class GitHubRepository(BaseModel):
    """GitHub repository information."""
    id: Optional[int] = None
    name: Optional[str] = None
    full_name: str
    html_url: Optional[str] = None
    clone_url: Optional[str] = None
    default_branch: Optional[str] = None

class GitHubPullRequest(BaseModel):
    """GitHub pull request information."""
    id: Optional[int] = None
    number: int
    title: Optional[str] = None
    body: Optional[str] = None
    state: Optional[str] = None
    html_url: Optional[str] = None
    head_ref: Optional[str] = None
    base_ref: Optional[str] = None
    user: Optional[GitHubUser] = None

class GitHubComment(BaseModel):
    """GitHub PR comment information."""
    id: int
    body: str
    user: GitHubUser
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    html_url: Optional[str] = None

class GitHubWebhookPayload(BaseModel):
    """GitHub webhook payload structure."""
    action: str
    repository: GitHubRepository
    pull_request: Optional[GitHubPullRequest] = None
    comment: Optional[GitHubComment] = None
    sender: Optional[GitHubUser] = None
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