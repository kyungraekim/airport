import asyncio
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import structlog
import random
import tempfile
import os

from app.models.validation import ModelArtifact, ModelArtifactType
from app.core.config import settings

logger = structlog.get_logger()

class MockJFrogService:
    """Mock JFrog Artifactory service for development and testing."""
    
    def __init__(self):
        self.base_url = settings.MOCK_JFROG_URL
        self._artifacts = self._generate_mock_artifacts()
    
    def _generate_mock_artifacts(self) -> Dict[str, ModelArtifact]:
        """Generate mock model artifacts for testing."""
        artifacts = {}
        
        # Sample model configurations
        models = [
            {
                "name": "bert-base-classifier",
                "version": "v1.2.0",
                "description": "BERT base model for text classification"
            },
            {
                "name": "resnet50-vision", 
                "version": "v2.1.0",
                "description": "ResNet-50 model for image classification"
            },
            {
                "name": "transformer-nlp",
                "version": "v1.0.3", 
                "description": "Transformer model for NLP tasks"
            }
        ]
        
        for model in models:
            for artifact_type in ModelArtifactType:
                artifact_id = f"{model['name']}-{model['version']}-{artifact_type.value}"
                file_extension = self._get_file_extension(artifact_type)
                
                artifacts[artifact_id] = ModelArtifact(
                    artifact_id=artifact_id,
                    artifact_type=artifact_type,
                    file_path=f"/repository/models/{model['name']}/{model['version']}/{artifact_type.value}{file_extension}",
                    file_size=random.randint(1024, 1024*1024*100),  # 1KB to 100MB
                    checksum=hashlib.md5(artifact_id.encode()).hexdigest(),
                    name=model['name'],
                    version=model['version'],
                    description=model['description'],
                    tags={
                        "model_type": "ml_model",
                        "framework": random.choice(["pytorch", "tensorflow", "sklearn"]),
                        "domain": random.choice(["nlp", "vision", "tabular"])
                    },
                    source_repository="github.com/company/ml-models",
                    source_branch="main",
                    source_commit=hashlib.sha1(artifact_id.encode()).hexdigest()[:7],
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
                )
        
        return artifacts
    
    def _get_file_extension(self, artifact_type: ModelArtifactType) -> str:
        """Get file extension for artifact type."""
        extensions = {
            ModelArtifactType.CONFIG: ".json",
            ModelArtifactType.WEIGHTS: ".bin",
            ModelArtifactType.ARCHITECTURE: ".py",
            ModelArtifactType.METADATA: ".yaml"
        }
        return extensions.get(artifact_type, ".dat")
    
    async def authenticate(self, username: str, api_key: str) -> bool:
        """Mock authentication with JFrog."""
        # Simulate authentication delay
        await asyncio.sleep(0.5)
        
        # Mock authentication logic (always succeeds in mock mode)
        logger.info("Mock JFrog authentication", username=username, success=True)
        return True
    
    async def list_repositories(self) -> List[Dict[str, Any]]:
        """List available repositories."""
        await asyncio.sleep(0.3)  # Simulate API delay
        
        repositories = [
            {
                "key": "ml-models-local",
                "type": "LOCAL",
                "description": "Local ML models repository",
                "url": f"{self.base_url}/ml-models-local"
            },
            {
                "key": "ml-models-cache", 
                "type": "CACHE",
                "description": "ML models cache repository",
                "url": f"{self.base_url}/ml-models-cache"
            }
        ]
        
        logger.info("Listed JFrog repositories", count=len(repositories))
        return repositories
    
    async def list_artifacts(
        self, 
        repository: str, 
        path: str = "", 
        artifact_type: Optional[ModelArtifactType] = None
    ) -> List[ModelArtifact]:
        """List artifacts in a repository path."""
        await asyncio.sleep(0.5)  # Simulate API delay
        
        # Filter artifacts based on criteria
        filtered_artifacts = []
        for artifact in self._artifacts.values():
            if artifact_type and artifact.artifact_type != artifact_type:
                continue
            
            if path and not artifact.file_path.startswith(f"/repository/{repository}/{path}"):
                continue
            
            filtered_artifacts.append(artifact)
        
        logger.info("Listed JFrog artifacts", 
                   repository=repository, 
                   path=path,
                   artifact_type=artifact_type,
                   count=len(filtered_artifacts))
        
        return filtered_artifacts
    
    async def get_artifact_info(self, artifact_id: str) -> Optional[ModelArtifact]:
        """Get detailed information about an artifact."""
        await asyncio.sleep(0.2)  # Simulate API delay
        
        artifact = self._artifacts.get(artifact_id)
        if artifact:
            logger.info("Retrieved artifact info", artifact_id=artifact_id)
        else:
            logger.warning("Artifact not found", artifact_id=artifact_id)
        
        return artifact
    
    async def download_artifact(
        self, 
        artifact_id: str, 
        destination_path: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Download an artifact and return local file path."""
        artifact = self._artifacts.get(artifact_id)
        if not artifact:
            raise ValueError(f"Artifact not found: {artifact_id}")
        
        # Create temporary file if no destination specified
        if not destination_path:
            temp_dir = tempfile.mkdtemp()
            file_extension = self._get_file_extension(artifact.artifact_type)
            destination_path = os.path.join(temp_dir, f"{artifact_id}{file_extension}")
        
        logger.info("Starting artifact download", 
                   artifact_id=artifact_id,
                   destination=destination_path)
        
        # Simulate download with progress
        total_chunks = 20
        chunk_size = artifact.file_size // total_chunks
        
        # Create mock file content based on artifact type
        content = self._generate_mock_content(artifact)
        
        with open(destination_path, 'w') as f:
            for i in range(total_chunks):
                # Simulate download delay
                await asyncio.sleep(0.1)
                
                # Write chunk
                if i == total_chunks - 1:
                    f.write(content)  # Write all content in last chunk
                
                # Call progress callback if provided
                if progress_callback:
                    progress = ((i + 1) / total_chunks) * 100
                    await progress_callback(progress, artifact_id)
        
        # Update artifact with download timestamp
        artifact.downloaded_at = datetime.utcnow()
        
        logger.info("Artifact download completed", 
                   artifact_id=artifact_id,
                   file_path=destination_path)
        
        return destination_path
    
    def _generate_mock_content(self, artifact: ModelArtifact) -> str:
        """Generate mock file content based on artifact type."""
        if artifact.artifact_type == ModelArtifactType.CONFIG:
            return json.dumps({
                "model_name": artifact.name,
                "version": artifact.version,
                "architecture": "transformer",
                "hidden_size": 768,
                "num_layers": 12,
                "num_attention_heads": 12,
                "vocab_size": 30522,
                "max_sequence_length": 512,
                "dropout": 0.1,
                "activation": "gelu",
                "training": {
                    "batch_size": 32,
                    "learning_rate": 2e-5,
                    "epochs": 3,
                    "optimizer": "adam"
                },
                "metadata": {
                    "created_at": artifact.created_at.isoformat(),
                    "framework": artifact.tags.get("framework", "pytorch"),
                    "domain": artifact.tags.get("domain", "nlp")
                }
            }, indent=2)
        
        elif artifact.artifact_type == ModelArtifactType.ARCHITECTURE:
            return f'''
import torch
import torch.nn as nn

class {artifact.name.replace('-', '_').title()}Model(nn.Module):
    """Mock model architecture for {artifact.name}."""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.hidden_size = config.get("hidden_size", 768)
        self.num_layers = config.get("num_layers", 12)
        
        # Mock layers
        self.embeddings = nn.Embedding(config.get("vocab_size", 30522), self.hidden_size)
        self.transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=self.hidden_size,
                nhead=config.get("num_attention_heads", 12),
                batch_first=True
            ),
            num_layers=self.num_layers
        )
        self.classifier = nn.Linear(self.hidden_size, config.get("num_classes", 2))
    
    def forward(self, input_ids, attention_mask=None):
        embeddings = self.embeddings(input_ids)
        transformer_output = self.transformer(embeddings)
        pooled_output = transformer_output.mean(dim=1)
        logits = self.classifier(pooled_output)
        return logits
            '''
        
        elif artifact.artifact_type == ModelArtifactType.METADATA:
            return f'''
model_name: {artifact.name}
version: {artifact.version}
description: {artifact.description}

artifact_info:
  artifact_id: {artifact.artifact_id}
  file_size: {artifact.file_size}
  checksum: {artifact.checksum}
  created_at: {artifact.created_at.isoformat()}

source_info:
  repository: {artifact.source_repository}
  branch: {artifact.source_branch}
  commit: {artifact.source_commit}

tags:
  framework: {artifact.tags.get("framework", "unknown")}
  domain: {artifact.tags.get("domain", "unknown")}
  model_type: {artifact.tags.get("model_type", "ml_model")}

performance_metrics:
  accuracy: {random.uniform(0.85, 0.95):.3f}
  f1_score: {random.uniform(0.80, 0.93):.3f}
  inference_time_ms: {random.randint(10, 100)}
            '''
        
        else:  # ModelArtifactType.WEIGHTS
            return f"# Mock binary weights file for {artifact.name}\n# File size: {artifact.file_size} bytes\n# Checksum: {artifact.checksum}"
    
    async def upload_artifact(
        self, 
        file_path: str, 
        repository: str, 
        target_path: str,
        properties: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload an artifact (mock implementation)."""
        await asyncio.sleep(1.0)  # Simulate upload delay
        
        # Generate mock artifact ID
        artifact_id = f"uploaded-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info("Mock artifact uploaded", 
                   file_path=file_path,
                   repository=repository,
                   target_path=target_path,
                   artifact_id=artifact_id)
        
        return artifact_id
    
    async def delete_artifact(self, artifact_id: str) -> bool:
        """Delete an artifact (mock implementation)."""
        await asyncio.sleep(0.3)
        
        if artifact_id in self._artifacts:
            del self._artifacts[artifact_id]
            logger.info("Mock artifact deleted", artifact_id=artifact_id)
            return True
        else:
            logger.warning("Artifact not found for deletion", artifact_id=artifact_id)
            return False
    
    async def search_artifacts(
        self, 
        query: str, 
        repository: Optional[str] = None,
        limit: int = 50
    ) -> List[ModelArtifact]:
        """Search artifacts by query."""
        await asyncio.sleep(0.4)
        
        # Simple text search in artifact names and descriptions
        results = []
        query_lower = query.lower()
        
        for artifact in self._artifacts.values():
            if (query_lower in artifact.name.lower() or 
                query_lower in artifact.description.lower() or
                any(query_lower in tag_value.lower() for tag_value in artifact.tags.values())):
                
                if repository and repository not in artifact.file_path:
                    continue
                
                results.append(artifact)
                
                if len(results) >= limit:
                    break
        
        logger.info("Artifact search completed", 
                   query=query,
                   repository=repository,
                   results_count=len(results))
        
        return results