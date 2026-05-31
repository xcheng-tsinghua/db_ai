from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class PlanStep(BaseModel):
    step_id: str = Field(..., description="Unique step identifier like 'step_1', 'step_2'")
    title: str = Field(..., description="Short title of the step")
    worker_name: str = Field(..., description="Name of the worker executing this step (e.g. text_worker, image_gen_worker)")
    instruction: str = Field(..., description="Detailed instructions for the worker")
    depends_on: List[str] = Field(default_factory=list, description="List of step_ids this step depends on")
    input_refs: Dict[str, str] = Field(default_factory=dict, description="Logical input names to artifact/user_input IDs")
    output_type: str = Field(..., description="Expected output type: 'text', 'image', 'file', 'json', 'mixed'")
    status: str = Field("pending", description="Status of the step: pending, running, completed, failed, skipped")

class ExecutionPlan(BaseModel):
    title: str = Field(..., description="Consulting project title")
    objective: str = Field(..., description="High level goal of the execution plan")
    steps: List[PlanStep] = Field(..., description="Ordered list of execution plan steps")

class Artifact(BaseModel):
    artifact_id: str = Field(..., description="Unique ID for the generated output")
    type: str = Field(..., description="Data type: 'text', 'image', 'file', 'json', 'mixed'")
    path_or_url: str = Field(..., description="URL path or relative local path to the artifact")
    source_step_id: Optional[str] = Field(None, description="The step_id that produced this artifact")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extra metadata, e.g. metadata.operation='image_edit'")

class StepError(BaseModel):
    error_type: str = Field(..., description="Type: validation_error, provider_error, worker_error, storage_error, cancelled")
    message: str = Field(..., description="Error explanation message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed dictionary of the error")

class StepResult(BaseModel):
    step_id: str = Field(..., description="Target step_id")
    status: str = Field(..., description="Status: pending, running, completed, failed, skipped")
    output_artifact_ids: List[str] = Field(default_factory=list, description="IDs of generated artifacts")
    error: Optional[StepError] = Field(None, description="Step structured error if failed")
    retry_count: int = Field(0, description="Number of times this step was retried")
    started_at: Optional[str] = Field(None, description="ISO timestamp when started")
    completed_at: Optional[str] = Field(None, description="ISO timestamp when completed")

class TaskState(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    user_query: str = Field(..., description="The user's initial input query")
    status: str = Field(..., description="Task status: planning, pending_approval, executing, completed, failed, cancelled, planning_failed")
    plan: Optional[ExecutionPlan] = Field(None, description="The generated execution plan")
    step_results: Dict[str, StepResult] = Field(default_factory=dict, description="Detailed result for each step ID")
    artifacts: List[Artifact] = Field(default_factory=list, description="Accumulated output artifacts list")
    final_summary: Optional[str] = Field(None, description="Final consolidated consulting report")
    error: Optional[StepError] = Field(None, description="Task-level structured error")
    created_at: str = Field(..., description="Task creation ISO timestamp")
    approved_at: Optional[str] = Field(None, description="Plan approval ISO timestamp")
    started_at: Optional[str] = Field(None, description="Execution start ISO timestamp")
    completed_at: Optional[str] = Field(None, description="Completion ISO timestamp")
    updated_at: str = Field(..., description="Last update ISO timestamp")
