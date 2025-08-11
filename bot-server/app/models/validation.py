from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime

class ModelArtifactType(str, Enum):
    CONFIG = "config"
    WEIGHTS = "weights"
    ARCHITECTURE = "architecture"
    METADATA = "metadata"

class ModelArtifact(BaseModel):
    """Model artifact information and metadata."""
    artifact_id: str
    artifact_type: ModelArtifactType
    file_path: str
    file_size: int
    checksum: str
    
    # Metadata
    name: str
    version: str
    description: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    
    # Source information
    source_repository: str
    source_branch: str
    source_commit: str
    
    # Timestamps
    created_at: datetime
    downloaded_at: Optional[datetime] = None

class ModelComparison(BaseModel):
    """Comparison between two models."""
    reference_model: ModelArtifact
    incoming_model: ModelArtifact
    
    # Comparison results
    config_differences: Dict[str, Any] = Field(default_factory=dict)
    architecture_differences: List[str] = Field(default_factory=list)
    weight_differences: Dict[str, float] = Field(default_factory=dict)
    
    # Summary
    is_compatible: bool
    risk_level: str = Field(default="low")  # low, medium, high
    recommendations: List[str] = Field(default_factory=list)

class ValidationDecision(str, Enum):
    APPROVE_INCOMING = "approve_incoming"
    APPROVE_REFERENCE = "approve_reference"
    MERGE_MODELS = "merge_models"
    REJECT_BOTH = "reject_both"
    REQUEST_CHANGES = "request_changes"

class UserDecision(BaseModel):
    """User decision on model validation."""
    decision: ValidationDecision
    selected_config: Optional[str] = None
    custom_parameters: Dict[str, Any] = Field(default_factory=dict)
    comments: Optional[str] = None
    user: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ValidationResult(BaseModel):
    """Complete validation result with user decisions."""
    validation_id: str
    comparison: ModelComparison
    user_decision: Optional[UserDecision] = None
    
    # Workflow configuration
    training_config: Dict[str, Any] = Field(default_factory=dict)
    evaluation_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Generated artifacts
    model_card_path: Optional[str] = None
    report_path: Optional[str] = None
    
    # Status
    status: str = "pending_review"  # pending_review, approved, rejected, completed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ModelCard(BaseModel):
    """Generated model card information."""
    model_name: str
    version: str
    description: str
    
    # Model details
    architecture: str
    input_spec: Dict[str, Any]
    output_spec: Dict[str, Any]
    
    # Training information
    training_data: str
    training_procedure: str
    hyperparameters: Dict[str, Any]
    
    # Evaluation results
    evaluation_metrics: Dict[str, float]
    test_results: Dict[str, Any]
    
    # Usage guidelines
    intended_use: str
    limitations: List[str]
    ethical_considerations: List[str]
    
    # Metadata
    authors: List[str]
    license: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    references: List[str] = Field(default_factory=list)