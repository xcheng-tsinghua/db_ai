import os
import shutil
import tempfile
import pytest
from pathlib import Path
from unittest.mock import AsyncMock

from backend.app.company.models import (
    TaskState, ExecutionPlan, PlanStep, Artifact, StepResult, StepError
)
from backend.app.company.store import task_store
from backend.app.company.registry import worker_registry
from backend.app.routes.company import invalidate_downstream_steps

@pytest.fixture
def temp_workspace():
    # Setup temporary directory for test storage
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir)

@pytest.mark.anyio
async def test_plan_node_validation_and_repair(temp_workspace, monkeypatch):
    # Re-route task store to temporary directory
    task_store.workspace_root = Path(temp_workspace).resolve()
    task_store.tasks_root = task_store.workspace_root.joinpath("tasks")
    os.makedirs(task_store.tasks_root, exist_ok=True)

    task_id = "test_task_repair"
    task = TaskState(
        task_id=task_id,
        user_query="Create a website logo and slogan",
        status="planning",
        created_at="2026-05-30T12:00:00",
        updated_at="2026-05-30T12:00:00"
    )
    task_store.save_task(task)

    # Mock model provider
    from backend.app.providers.manager import provider_manager
    mock_provider = AsyncMock()
    
    valid_plan_json = """
    {
      "title": "Logo & Slogan Design",
      "objective": "Design a glowing logo and write slogans",
      "steps": [
        {
          "step_id": "step_1",
          "title": "Write Slogans",
          "worker_name": "text_worker",
          "instruction": "Draft 3 slogans",
          "depends_on": [],
          "input_refs": {},
          "output_type": "text",
          "status": "pending"
        }
      ]
    }
    """
    
    # First returns invalid syntax, second returns valid JSON
    mock_provider.chat.side_effect = [
        {"success": True, "data": {"choices": [{"message": {"content": "Here is plan ```json this is bad { json }}}"}}]}},
        {"success": True, "data": {"choices": [{"message": {"content": valid_plan_json}}]}}
    ]
    
    monkeypatch.setattr(provider_manager, "get_provider", lambda name: mock_provider)

    from backend.app.company.graph import plan_node
    await plan_node({"task_id": task_id})

    # Verify plan was repaired and loaded successfully
    updated_task = task_store.load_task(task_id)
    assert updated_task is not None
    assert updated_task.status == "pending_approval"
    assert updated_task.plan is not None
    assert updated_task.plan.title == "Logo & Slogan Design"
    assert len(updated_task.plan.steps) == 1
    assert mock_provider.chat.call_count == 2


@pytest.mark.anyio
async def test_plan_node_double_failure(temp_workspace, monkeypatch):
    task_store.workspace_root = Path(temp_workspace).resolve()
    task_store.tasks_root = task_store.workspace_root.joinpath("tasks")
    os.makedirs(task_store.tasks_root, exist_ok=True)

    task_id = "test_task_double_fail"
    task = TaskState(
        task_id=task_id,
        user_query="Generate logo",
        status="planning",
        created_at="2026-05-30T12:00:00",
        updated_at="2026-05-30T12:00:00"
    )
    task_store.save_task(task)

    from backend.app.providers.manager import provider_manager
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = {"success": True, "data": {"reply": "This is completely raw text without JSON structure."}}

    monkeypatch.setattr(provider_manager, "get_provider", lambda name: mock_provider)

    from backend.app.company.graph import plan_node
    await plan_node({"task_id": task_id})

    # Verify status transitions to planning_failed
    updated_task = task_store.load_task(task_id)
    assert updated_task is not None
    assert updated_task.status == "planning_failed"
    assert updated_task.error is not None
    assert updated_task.error.error_type == "validation_error"


@pytest.mark.anyio
async def test_sequential_execution_and_invalidation(temp_workspace, monkeypatch):
    task_store.workspace_root = Path(temp_workspace).resolve()
    task_store.tasks_root = task_store.workspace_root.joinpath("tasks")
    os.makedirs(task_store.tasks_root, exist_ok=True)

    # 1. Construct 3-step dependency plan
    plan = ExecutionPlan(
        title="Cafe Marketing Plan",
        objective="Cafe marketing artifacts",
        steps=[
            PlanStep(
                step_id="step_1",
                title="Draft Slogans",
                worker_name="text_worker",
                instruction="Draft 3 cafe slogans",
                depends_on=[],
                input_refs={"prompt": "user_input_text_0"},
                output_type="text",
                status="pending"
            ),
            PlanStep(
                step_id="step_2",
                title="Draw Slogan Logo",
                worker_name="image_gen_worker",
                instruction="Make logo with text",
                depends_on=["step_1"],
                input_refs={"prompt": "artifact_step_1_text_0"},
                output_type="image",
                status="pending"
            ),
            PlanStep(
                step_id="step_3",
                title="Refine Slogan Logo",
                worker_name="image_edit_worker",
                instruction="Add sparkles to logo",
                depends_on=["step_2"],
                input_refs={"base_image": "artifact_step_2_image_0", "prompt": "user_input_text_0"},
                output_type="image",
                status="pending"
            )
        ]
    )

    task_id = "test_seq_exec_task"
    task = TaskState(
        task_id=task_id,
        user_query="Cyber Pie Shop",
        status="executing",
        plan=plan,
        created_at="2026-05-30T12:00:00",
        updated_at="2026-05-30T12:00:00"
    )
    task_store.save_task(task)

    # Mock environment to use Mock generator (pure Python SVG)
    monkeypatch.setenv("ENABLE_MOCK_IMAGE_PROVIDER", "true")

    # Mock LLM for TextWorker
    from backend.app.providers.manager import provider_manager
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = {
        "success": True,
        "data": {
            "choices": [{"message": {"content": "Slogan: Cyber Pie: Slice of tomorrow!"}}]
        }
    }
    monkeypatch.setattr(provider_manager, "get_provider", lambda name: mock_provider)

    # 2. Execute steps
    from backend.app.company.graph import execute_steps_node
    await execute_steps_node({"task_id": task_id})

    # Check execution succeeded
    updated_task = task_store.load_task(task_id)
    assert updated_task is not None
    assert updated_task.plan.steps[0].status == "completed"
    assert updated_task.plan.steps[1].status == "completed"
    assert updated_task.plan.steps[2].status == "completed"
    assert len(updated_task.artifacts) == 3
    
    # 3. Test Invalidation & Retry Propagation
    # Retry step_2. This should reset step_2 and step_3 to pending, clear their results/artifacts, and keep step_1 intact.
    invalidate_downstream_steps(updated_task, "step_2")

    # Reload and assert
    assert updated_task.plan.steps[0].status == "completed" # Remains completed
    assert updated_task.plan.steps[1].status == "pending"   # Target is reset
    assert updated_task.plan.steps[2].status == "pending"   # Dependent downstream is reset
    
    # Check retry counts
    assert updated_task.step_results["step_1"].retry_count == 0
    assert updated_task.step_results["step_2"].retry_count == 1
    assert updated_task.step_results["step_3"].retry_count == 0
    
    # Only 1 artifact remains (from step_1, which was not invalidated)
    assert len(updated_task.artifacts) == 1
    assert updated_task.artifacts[0].artifact_id == "artifact_step_1_text_0"


@pytest.mark.anyio
async def test_worker_execution_error_handling(temp_workspace, monkeypatch):
    task_store.workspace_root = Path(temp_workspace).resolve()
    task_store.tasks_root = task_store.workspace_root.joinpath("tasks")
    os.makedirs(task_store.tasks_root, exist_ok=True)

    plan = ExecutionPlan(
        title="Failing Project",
        objective="Attempt something that fails",
        steps=[
            PlanStep(
                step_id="step_1",
                title="Fail Step",
                worker_name="text_worker",
                instruction="Will throw exception",
                depends_on=[],
                input_refs={},
                output_type="text",
                status="pending"
            )
        ]
    )

    task_id = "test_fail_task"
    task = TaskState(
        task_id=task_id,
        user_query="Run task",
        status="executing",
        plan=plan,
        created_at="2026-05-30T12:00:00",
        updated_at="2026-05-30T12:00:00"
    )
    task_store.save_task(task)

    # Force model provider failure
    from backend.app.providers.manager import provider_manager
    mock_provider = AsyncMock()
    mock_provider.chat.return_value = {
        "success": False,
        "error": "MiniMax model is overloaded right now."
    }
    monkeypatch.setattr(provider_manager, "get_provider", lambda name: mock_provider)

    from backend.app.company.graph import execute_steps_node
    await execute_steps_node({"task_id": task_id})

    # Verify structured StepError details
    updated_task = task_store.load_task(task_id)
    assert updated_task is not None
    assert updated_task.status == "failed"
    assert updated_task.error is not None
    assert updated_task.error.error_type == "provider_error"
    assert "overloaded" in updated_task.error.message


@pytest.mark.anyio
async def test_task_execution_cancellation(temp_workspace, monkeypatch):
    task_store.workspace_root = Path(temp_workspace).resolve()
    task_store.tasks_root = task_store.workspace_root.joinpath("tasks")
    os.makedirs(task_store.tasks_root, exist_ok=True)

    plan = ExecutionPlan(
        title="Long Project",
        objective="Run many steps",
        steps=[
            PlanStep(
                step_id="step_1",
                title="Step 1",
                worker_name="text_worker",
                instruction="Instructions 1",
                depends_on=[],
                input_refs={},
                output_type="text",
                status="pending"
            ),
            PlanStep(
                step_id="step_2",
                title="Step 2",
                worker_name="text_worker",
                instruction="Instructions 2",
                depends_on=["step_1"],
                input_refs={},
                output_type="text",
                status="pending"
            )
        ]
    )

    task_id = "test_cancel_task"
    task = TaskState(
        task_id=task_id,
        user_query="Run task",
        status="executing",
        plan=plan,
        created_at="2026-05-30T12:00:00",
        updated_at="2026-05-30T12:00:00"
    )
    task_store.save_task(task)

    # Mock provider but intercept inside to change task state in store to cancelled
    # so that when execute_steps_node proceeds to step 2, it reads 'cancelled' and terminates.
    from backend.app.providers.manager import provider_manager
    mock_provider = AsyncMock()
    
    async def chat_mock(*args, **kwargs):
        # Cancel the task on first execution
        t = task_store.load_task(task_id)
        t.status = "cancelled"
        task_store.save_task(t)
        return {
            "success": True,
            "data": {"choices": [{"message": {"content": "Step 1 text response"}}]}
        }
        
    mock_provider.chat.side_effect = chat_mock
    monkeypatch.setattr(provider_manager, "get_provider", lambda name: mock_provider)

    from backend.app.company.graph import execute_steps_node
    await execute_steps_node({"task_id": task_id})

    # Verify that step_2 is skipped/remains pending, and loop exits gracefully
    updated_task = task_store.load_task(task_id)
    assert updated_task is not None
    assert updated_task.plan.steps[0].status == "completed"
    assert updated_task.plan.steps[1].status == "pending"  # Skipped because loop exits at cancelled boundary
    assert updated_task.status == "cancelled"
