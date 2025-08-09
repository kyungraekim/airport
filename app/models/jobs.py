from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime
import uuid

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(str, Enum):
    TRAIN = "train"
    EVAL = "eval"
    TEST = "test"
    PIPELINE = "pipeline"
    MODEL_VALIDATION = "model_validation"

class JobProgress(BaseModel):
    """Job progress information."""
    current_step: str
    total_steps: int
    completed_steps: int
    progress_percentage: float = Field(ge=0, le=100)
    estimated_time_remaining: Optional[int] = None  # seconds

class JobResult(BaseModel):
    """Job execution results."""
    success: bool
    output: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict)

class Job(BaseModel):
    """Job execution state and metadata."""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_type: JobType
    status: JobStatus = JobStatus.PENDING
    
    # Job configuration
    command_config: Dict[str, Any]
    github_context: Optional[Dict[str, Any]] = None
    
    # Execution metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Progress tracking
    progress: Optional[JobProgress] = None
    result: Optional[JobResult] = None
    
    # External job references
    external_job_ids: Dict[str, str] = Field(default_factory=dict)
    
    # Logging and debugging
    logs: List[str] = Field(default_factory=list)
    
    def add_log(self, message: str):
        """Add a log message with timestamp."""
        timestamp = datetime.utcnow().isoformat()
        self.logs.append(f"[{timestamp}] {message}")
    
    def update_progress(self, step: str, completed: int, total: int, message: str = ""):
        """Update job progress."""
        progress_pct = (completed / total) * 100 if total > 0 else 0
        self.progress = JobProgress(
            current_step=step,
            total_steps=total,
            completed_steps=completed,
            progress_percentage=progress_pct
        )
        if message:
            self.add_log(message)
    
    def mark_started(self):
        """Mark job as started."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.add_log("Job started")
    
    def mark_completed(self, result: JobResult):
        """Mark job as completed with results."""
        self.status = JobStatus.COMPLETED if result.success else JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.result = result
        self.add_log(f"Job completed with status: {self.status}")
    
    def mark_cancelled(self, reason: str = ""):
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.add_log(f"Job cancelled: {reason}" if reason else "Job cancelled")

class JobStatusUpdate(BaseModel):
    """Real-time job status update."""
    job_id: str
    status: JobStatus
    progress: Optional[JobProgress] = None
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)