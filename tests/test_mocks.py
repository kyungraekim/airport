import pytest
import asyncio
from app.mocks.jfrog_service import MockJFrogService
from app.mocks.workflow_service import MockWorkflowService
from app.models.validation import ModelArtifactType

@pytest.mark.asyncio
async def test_jfrog_authentication():
    """Test JFrog mock authentication."""
    service = MockJFrogService()
    result = await service.authenticate("test_user", "test_key")
    assert result == True

@pytest.mark.asyncio
async def test_jfrog_list_repositories():
    """Test JFrog repository listing."""
    service = MockJFrogService()
    repos = await service.list_repositories()
    assert len(repos) > 0
    assert "ml-models-local" in [r["key"] for r in repos]

@pytest.mark.asyncio
async def test_jfrog_list_artifacts():
    """Test JFrog artifact listing."""
    service = MockJFrogService()
    artifacts = await service.list_artifacts("ml-models-local")
    assert len(artifacts) > 0

@pytest.mark.asyncio
async def test_jfrog_download_artifact():
    """Test JFrog artifact download."""
    service = MockJFrogService()
    artifacts = await service.list_artifacts("ml-models-local", artifact_type=ModelArtifactType.CONFIG)
    assert len(artifacts) > 0
    
    artifact_id = artifacts[0].artifact_id
    file_path = await service.download_artifact(artifact_id)
    assert file_path is not None
    
    # Verify file content
    with open(file_path, 'r') as f:
        content = f.read()
        assert len(content) > 0

@pytest.mark.asyncio
async def test_workflow_list_workflows():
    """Test workflow service listing."""
    service = MockWorkflowService()
    workflows = await service.list_workflows()
    assert len(workflows) > 0
    assert "train_model" in [w["workflow_id"] for w in workflows]

@pytest.mark.asyncio
async def test_workflow_submit_execution():
    """Test workflow execution submission."""
    service = MockWorkflowService()
    
    inputs = {
        "model_config": {"hidden_size": 768},
        "training_data": "/data/train.csv",
        "epochs": 5
    }
    
    execution_id = await service.submit_workflow("train_model", inputs)
    assert execution_id is not None
    
    # Wait a moment for execution to start
    await asyncio.sleep(0.1)
    
    status = await service.get_execution_status(execution_id)
    assert status is not None
    assert status["status"] in ["queued", "running"]

@pytest.mark.asyncio
async def test_workflow_get_definition():
    """Test getting workflow definition."""
    service = MockWorkflowService()
    definition = await service.get_workflow_definition("train_model")
    
    assert definition is not None
    assert definition["workflow_id"] == "train_model"
    assert "inputs" in definition
    assert "resource_requirements" in definition