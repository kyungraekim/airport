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
    """GitHub PR context information."""
    repository: str
    pull_request_number: int
    comment_id: int
    user: str
    installation_id: Optional[int] = None
    
class CommandRequest(BaseModel):
    """Complete command request with context."""
    command: CommandConfig
    github_context: Optional[GitHubContext] = None
    timestamp: str
    user_id: str