import asyncio
import json
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import structlog
import uuid

logger = structlog.get_logger()

class WorkflowStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class MockWorkflowExecution:
    """Mock workflow execution state."""
    
    def __init__(self, workflow_id: str, workflow_type: str, inputs: Dict[str, Any]):
        self.execution_id = str(uuid.uuid4())
        self.workflow_id = workflow_id
        self.workflow_type = workflow_type
        self.inputs = inputs
        self.status = WorkflowStatus.QUEUED
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.outputs: Dict[str, Any] = {}
        self.logs: List[str] = []
        self.progress = 0.0
        self.current_step = "Queued"
        self.error_message: Optional[str] = None
    
    def add_log(self, message: str):
        """Add a log message with timestamp."""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        self.logs.append(f"[{timestamp}] {message}")

class MockWorkflowService:
    """Mock workflow service for ML platform integration."""
    
    def __init__(self):
        self.base_url = "https://mock-ml-platform.example.com"
        self._executions: Dict[str, MockWorkflowExecution] = {}
        self._workflow_definitions = self._create_workflow_definitions()
    
    def _create_workflow_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Create mock workflow definitions."""
        return {
            "train_model": {
                "name": "Model Training Workflow",
                "description": "Train a machine learning model with specified parameters",
                "inputs": {
                    "model_config": {"type": "object", "required": True},
                    "training_data": {"type": "string", "required": True},
                    "epochs": {"type": "integer", "default": 10},
                    "batch_size": {"type": "integer", "default": 32},
                    "learning_rate": {"type": "number", "default": 0.001}
                },
                "estimated_duration_minutes": 45,
                "resource_requirements": {
                    "cpu": 4,
                    "memory_gb": 16,
                    "gpu": 1
                }
            },
            "evaluate_model": {
                "name": "Model Evaluation Workflow", 
                "description": "Evaluate model performance on test dataset",
                "inputs": {
                    "model_path": {"type": "string", "required": True},
                    "test_data": {"type": "string", "required": True},
                    "metrics": {"type": "array", "default": ["accuracy", "f1_score"]},
                    "batch_size": {"type": "integer", "default": 64}
                },
                "estimated_duration_minutes": 15,
                "resource_requirements": {
                    "cpu": 2,
                    "memory_gb": 8,
                    "gpu": 0
                }
            },
            "model_comparison": {
                "name": "Model Comparison Workflow",
                "description": "Compare multiple models on common test set",
                "inputs": {
                    "baseline_model": {"type": "string", "required": True},
                    "candidate_model": {"type": "string", "required": True},
                    "test_data": {"type": "string", "required": True},
                    "comparison_metrics": {"type": "array", "default": ["accuracy", "precision", "recall"]}
                },
                "estimated_duration_minutes": 20,
                "resource_requirements": {
                    "cpu": 4,
                    "memory_gb": 12,
                    "gpu": 1
                }
            },
            "smoke_test": {
                "name": "Model Smoke Test",
                "description": "Quick validation test for model functionality",
                "inputs": {
                    "model_path": {"type": "string", "required": True},
                    "sample_data": {"type": "string", "required": True},
                    "test_cases": {"type": "integer", "default": 10}
                },
                "estimated_duration_minutes": 5,
                "resource_requirements": {
                    "cpu": 1,
                    "memory_gb": 4,
                    "gpu": 0
                }
            }
        }
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List available workflows."""
        await asyncio.sleep(0.2)
        
        workflows = []
        for workflow_id, definition in self._workflow_definitions.items():
            workflows.append({
                "workflow_id": workflow_id,
                "name": definition["name"],
                "description": definition["description"],
                "estimated_duration_minutes": definition["estimated_duration_minutes"],
                "resource_requirements": definition["resource_requirements"]
            })
        
        logger.info("Listed available workflows", count=len(workflows))
        return workflows
    
    async def get_workflow_definition(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow definition details."""
        await asyncio.sleep(0.1)
        
        definition = self._workflow_definitions.get(workflow_id)
        if definition:
            logger.info("Retrieved workflow definition", workflow_id=workflow_id)
            return {
                "workflow_id": workflow_id,
                **definition
            }
        else:
            logger.warning("Workflow definition not found", workflow_id=workflow_id)
            return None
    
    async def submit_workflow(
        self, 
        workflow_id: str, 
        inputs: Dict[str, Any],
        callback_url: Optional[str] = None
    ) -> str:
        """Submit a workflow for execution."""
        if workflow_id not in self._workflow_definitions:
            raise ValueError(f"Unknown workflow: {workflow_id}")
        
        # Create workflow execution
        execution = MockWorkflowExecution(workflow_id, workflow_id, inputs)
        self._executions[execution.execution_id] = execution
        
        # Start execution in background
        asyncio.create_task(self._execute_workflow(execution, callback_url))
        
        logger.info("Workflow submitted", 
                   execution_id=execution.execution_id,
                   workflow_id=workflow_id)
        
        return execution.execution_id
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status."""
        await asyncio.sleep(0.1)
        
        execution = self._executions.get(execution_id)
        if not execution:
            return None
        
        return {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "workflow_type": execution.workflow_type,
            "status": execution.status.value,
            "progress": execution.progress,
            "current_step": execution.current_step,
            "created_at": execution.created_at.isoformat(),
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "inputs": execution.inputs,
            "outputs": execution.outputs,
            "error_message": execution.error_message,
            "logs": execution.logs[-10:]  # Last 10 log entries
        }
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a workflow execution."""
        await asyncio.sleep(0.2)
        
        execution = self._executions.get(execution_id)
        if not execution:
            return False
        
        if execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            return False
        
        execution.status = WorkflowStatus.CANCELLED
        execution.completed_at = datetime.utcnow()
        execution.add_log("Workflow execution cancelled by user")
        
        logger.info("Workflow execution cancelled", execution_id=execution_id)
        return True
    
    async def _execute_workflow(self, execution: MockWorkflowExecution, callback_url: Optional[str]):
        """Execute workflow (mock implementation)."""
        try:
            # Start execution
            execution.status = WorkflowStatus.RUNNING
            execution.started_at = datetime.utcnow()
            execution.add_log(f"Started {execution.workflow_type} workflow")
            
            # Get workflow definition
            definition = self._workflow_definitions[execution.workflow_id]
            
            # Simulate workflow steps based on type
            if execution.workflow_type == "train_model":
                await self._simulate_training_workflow(execution)
            elif execution.workflow_type == "evaluate_model":
                await self._simulate_evaluation_workflow(execution)
            elif execution.workflow_type == "model_comparison":
                await self._simulate_comparison_workflow(execution)
            elif execution.workflow_type == "smoke_test":
                await self._simulate_smoke_test_workflow(execution)
            else:
                await self._simulate_generic_workflow(execution)
            
            # Complete successfully
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.progress = 100.0
            execution.current_step = "Completed"
            execution.add_log("Workflow execution completed successfully")
            
            # Send callback if provided
            if callback_url:
                await self._send_callback(callback_url, execution, "completed")
        
        except asyncio.CancelledError:
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            execution.add_log("Workflow execution cancelled")
        
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.error_message = str(e)
            execution.add_log(f"Workflow execution failed: {str(e)}")
            
            # Send failure callback if provided
            if callback_url:
                await self._send_callback(callback_url, execution, "failed")
    
    async def _simulate_training_workflow(self, execution: MockWorkflowExecution):
        """Simulate model training workflow."""
        steps = [
            ("Preparing training environment", 10),
            ("Loading training data", 15),
            ("Initializing model", 20),
            ("Training epoch 1-3", 50),
            ("Training epoch 4-6", 70),
            ("Training epoch 7-10", 85),
            ("Validating model", 95),
            ("Saving trained model", 100)
        ]
        
        for step_name, target_progress in steps:
            if execution.status == WorkflowStatus.CANCELLED:
                return
            
            execution.current_step = step_name
            execution.progress = target_progress
            execution.add_log(f"Executing: {step_name}")
            
            # Simulate realistic step duration
            await asyncio.sleep(random.uniform(1, 3))
        
        # Set training outputs
        execution.outputs = {
            "model_path": f"/models/trained_{execution.execution_id}.bin",
            "training_config": f"/configs/training_{execution.execution_id}.json",
            "training_metrics": {
                "final_loss": round(random.uniform(0.01, 0.1), 4),
                "final_accuracy": round(random.uniform(0.88, 0.96), 3),
                "training_epochs": execution.inputs.get("epochs", 10),
                "training_time_minutes": random.randint(30, 60)
            }
        }
    
    async def _simulate_evaluation_workflow(self, execution: MockWorkflowExecution):
        """Simulate model evaluation workflow."""
        steps = [
            ("Loading model", 20),
            ("Loading test data", 40),
            ("Running inference", 70),
            ("Computing metrics", 90),
            ("Generating report", 100)
        ]
        
        for step_name, target_progress in steps:
            if execution.status == WorkflowStatus.CANCELLED:
                return
            
            execution.current_step = step_name
            execution.progress = target_progress
            execution.add_log(f"Executing: {step_name}")
            
            await asyncio.sleep(random.uniform(0.5, 2))
        
        # Set evaluation outputs
        execution.outputs = {
            "evaluation_report": f"/reports/eval_{execution.execution_id}.json",
            "metrics": {
                "accuracy": round(random.uniform(0.85, 0.95), 3),
                "precision": round(random.uniform(0.82, 0.94), 3),
                "recall": round(random.uniform(0.80, 0.92), 3),
                "f1_score": round(random.uniform(0.83, 0.93), 3)
            },
            "test_samples": random.randint(1000, 5000),
            "inference_time_ms": round(random.uniform(10, 50), 2)
        }
    
    async def _simulate_comparison_workflow(self, execution: MockWorkflowExecution):
        """Simulate model comparison workflow."""
        steps = [
            ("Loading baseline model", 15),
            ("Loading candidate model", 30),
            ("Loading test data", 45),
            ("Running baseline evaluation", 65),
            ("Running candidate evaluation", 85),
            ("Comparing results", 100)
        ]
        
        for step_name, target_progress in steps:
            if execution.status == WorkflowStatus.CANCELLED:
                return
            
            execution.current_step = step_name
            execution.progress = target_progress
            execution.add_log(f"Executing: {step_name}")
            
            await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Generate comparison results
        baseline_acc = round(random.uniform(0.82, 0.90), 3)
        candidate_acc = round(random.uniform(0.85, 0.95), 3)
        
        execution.outputs = {
            "comparison_report": f"/reports/comparison_{execution.execution_id}.json",
            "baseline_metrics": {
                "accuracy": baseline_acc,
                "f1_score": round(baseline_acc - random.uniform(0.01, 0.03), 3)
            },
            "candidate_metrics": {
                "accuracy": candidate_acc,
                "f1_score": round(candidate_acc - random.uniform(0.01, 0.03), 3)
            },
            "improvement": {
                "accuracy_delta": round(candidate_acc - baseline_acc, 3),
                "relative_improvement": round((candidate_acc - baseline_acc) / baseline_acc * 100, 1)
            },
            "recommendation": "approve" if candidate_acc > baseline_acc else "reject"
        }
    
    async def _simulate_smoke_test_workflow(self, execution: MockWorkflowExecution):
        """Simulate smoke test workflow."""
        steps = [
            ("Loading model", 25),
            ("Preparing test cases", 50),
            ("Running smoke tests", 75),
            ("Validating outputs", 100)
        ]
        
        for step_name, target_progress in steps:
            if execution.status == WorkflowStatus.CANCELLED:
                return
            
            execution.current_step = step_name
            execution.progress = target_progress
            execution.add_log(f"Executing: {step_name}")
            
            await asyncio.sleep(random.uniform(0.3, 1))
        
        # Generate smoke test results
        test_cases = execution.inputs.get("test_cases", 10)
        failed_cases = random.randint(0, max(1, test_cases // 5))
        
        execution.outputs = {
            "test_report": f"/reports/smoke_test_{execution.execution_id}.json",
            "total_tests": test_cases,
            "passed_tests": test_cases - failed_cases,
            "failed_tests": failed_cases,
            "success_rate": round((test_cases - failed_cases) / test_cases * 100, 1),
            "test_status": "passed" if failed_cases == 0 else "failed",
            "execution_time_seconds": round(random.uniform(5, 30), 1)
        }
    
    async def _simulate_generic_workflow(self, execution: MockWorkflowExecution):
        """Simulate a generic workflow."""
        steps = [
            ("Initializing", 20),
            ("Processing", 50),
            ("Analyzing", 80),
            ("Finalizing", 100)
        ]
        
        for step_name, target_progress in steps:
            if execution.status == WorkflowStatus.CANCELLED:
                return
            
            execution.current_step = step_name
            execution.progress = target_progress
            execution.add_log(f"Executing: {step_name}")
            
            await asyncio.sleep(random.uniform(1, 2))
        
        execution.outputs = {
            "status": "completed",
            "execution_time_seconds": random.randint(60, 300),
            "result": "success"
        }
    
    async def _send_callback(self, callback_url: str, execution: MockWorkflowExecution, status: str):
        """Send callback notification (mock implementation)."""
        callback_payload = {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "status": status,
            "outputs": execution.outputs,
            "error_message": execution.error_message,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None
        }
        
        logger.info("Sending workflow callback", 
                   callback_url=callback_url,
                   execution_id=execution.execution_id,
                   status=status)
        
        # In a real implementation, this would make an HTTP POST to the callback URL
        # For mock, we just log the callback
        await asyncio.sleep(0.1)