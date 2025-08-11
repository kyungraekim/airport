from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from enum import Enum

class CommandType(str, Enum):
    TRAIN = "train"
    EVAL = "eval"
    TEST = "test"
    PIPELINE = "pipeline"
    STATUS = "status"
    HELP = "help"

class ContextType(str, Enum):
    """Where the command was invoked."""
    ISSUE = "issue"           # Issue comment (for /train, /eval, /pipeline)
    PULL_REQUEST = "pr"       # PR comment (for /test, /status)  
    REPOSITORY = "repo"       # Any context (for /help)

# Command routing rules for hybrid approach
COMMAND_CONTEXT_RULES = {
    CommandType.TRAIN: [ContextType.ISSUE],           # Long-running ML jobs in issues
    CommandType.EVAL: [ContextType.ISSUE],            # Model evaluation in issues  
    CommandType.PIPELINE: [ContextType.ISSUE],        # Multi-step workflows in issues
    CommandType.TEST: [ContextType.PULL_REQUEST],     # Testing specific changes in PRs
    CommandType.STATUS: [ContextType.ISSUE, ContextType.PULL_REQUEST],  # Status anywhere
    CommandType.HELP: [ContextType.ISSUE, ContextType.PULL_REQUEST, ContextType.REPOSITORY]  # Help anywhere
}

def is_command_allowed_in_context(command_type: CommandType, context_type: ContextType) -> bool:
    """Check if a command is allowed in the given context."""
    allowed_contexts = COMMAND_CONTEXT_RULES.get(command_type, [])
    return context_type in allowed_contexts

def get_command_context_suggestion(command_type: CommandType) -> str:
    """Get a human-readable suggestion for where to use a command."""
    allowed_contexts = COMMAND_CONTEXT_RULES.get(command_type, [])
    
    if not allowed_contexts:
        return "nowhere (invalid command)"
    
    suggestions = []
    for context in allowed_contexts:
        if context == ContextType.ISSUE:
            suggestions.append("in Issues")
        elif context == ContextType.PULL_REQUEST:
            suggestions.append("in Pull Requests")
        elif context == ContextType.REPOSITORY:
            suggestions.append("anywhere")
    
    return " or ".join(suggestions)

class CommandConfig(BaseModel):
    """Parsed slash command structure."""
    command_type: CommandType
    raw_command: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    
    # Common parameters
    config: Optional[str] = None
    epochs: Optional[int] = None
    learning_rate: Optional[float] = Field(None, alias="lr")
    gpu: Optional[int] = None
    batch_size: Optional[int] = None
    
    # Evaluation parameters
    model: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    
    # Test parameters
    test_type: Optional[str] = None
    samples: Optional[int] = None
    
    # Pipeline parameters
    steps: Optional[List[str]] = None
    skip: Optional[List[str]] = None
    
    # Status parameters
    job_id: Optional[str] = None
    
    @validator('model', 'metrics', 'steps', 'skip', pre=True)
    def split_comma_separated(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v
    
    @validator('epochs', 'gpu', 'batch_size', 'samples', pre=True)
    def parse_int_params(cls, v):
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise ValueError(f"Invalid integer value: {v}")
        return v
    
    @validator('learning_rate', pre=True)
    def parse_float_params(cls, v):
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Invalid float value: {v}")
        return v

class GitHubContext(BaseModel):
    """GitHub context information for commands."""
    repository: str
    context_type: ContextType
    comment_id: int
    user: str
    
    # Issue context
    issue_number: Optional[int] = None
    
    # Pull request context  
    pull_request_number: Optional[int] = None
    
    # Installation context
    installation_id: Optional[int] = None
    
    @property
    def target_number(self) -> int:
        """Get the target number (issue or PR) for API calls."""
        if self.context_type == ContextType.ISSUE:
            return self.issue_number
        elif self.context_type == ContextType.PULL_REQUEST:
            return self.pull_request_number
        else:
            raise ValueError(f"No target number for context type: {self.context_type}")
    
    @property
    def display_context(self) -> str:
        """Human-readable context description."""
        if self.context_type == ContextType.ISSUE:
            return f"Issue #{self.issue_number}"
        elif self.context_type == ContextType.PULL_REQUEST:
            return f"PR #{self.pull_request_number}"
        else:
            return "Repository"
    
class CommandRequest(BaseModel):
    """Complete command request with context."""
    command: CommandConfig
    github_context: Optional[GitHubContext] = None
    timestamp: str
    user_id: str