import logging
import json
import re
from datetime import datetime
from typing import TypedDict, Dict, Any, List
from pydantic import ValidationError
from langgraph.graph import StateGraph, END
from backend.app.company.models import (
    TaskState, ExecutionPlan, PlanStep, Artifact, StepResult, StepError
)
from backend.app.company.store import task_store
from backend.app.company.registry import worker_registry
from backend.app.providers.manager import provider_manager

logger = logging.getLogger(__name__)

class CompanyState(TypedDict):
    task_id: str

async def plan_node(state: CompanyState) -> CompanyState:
    """Supervisor Agent: Generates and validates the JSON plan with a one-time repair loop."""
    task_id = state["task_id"]
    task = task_store.load_task(task_id)
    if not task or task.status != "planning":
        return state
        
    logger.info(f"Supervisor Agent planning for task {task_id}")
    
    workers_context = worker_registry.get_supervisor_prompt_context()
    system_prompt = (
        "You are the Supervisor Agent of an AI Consulting Company. Your job is to accept a user request "
        "and create a structured execution plan in JSON.\n\n"
        f"{workers_context}\n"
        "Guidelines for planning:\n"
        "1. Break the request down into ordered logical steps.\n"
        "2. Assign each step to a worker_name from the available list.\n"
        "3. Step IDs must be stable strings like 'step_1', 'step_2'.\n"
        "4. Define dependencies using depends_on: list[str]. For example, if step_2 needs step_1 output, set depends_on=['step_1'].\n"
        "5. Define input_refs: dict[str, str] mapping logical input names to previous step artifact IDs or user input IDs. "
        "User input text is 'user_input_text_0', user input image is 'user_input_image_0'. "
        "Artifact IDs produced by step_N are formatted as 'artifact_step_N_[type]_0'.\n"
        "   Example: {\"prompt\": \"artifact_step_1_text_0\"} or {\"base_image\": \"user_input_image_0\", \"prompt\": \"artifact_step_2_text_0\"}.\n"
        "6. Set output_type to match the output modality of the worker: 'text', 'image', 'file', 'json', 'mixed'.\n"
        "7. Ensure the JSON plan matches this Pydantic schema strictly:\n"
        "{\n"
        "  \"title\": \"Project Name\",\n"
        "  \"objective\": \"Goal description\",\n"
        "  \"steps\": [\n"
        "    {\n"
        "      \"step_id\": \"step_1\",\n"
        "      \"title\": \"Step Title\",\n"
        "      \"worker_name\": \"text_worker\",\n"
        "      \"instruction\": \"Detailed instructions for worker\",\n"
        "      \"depends_on\": [],\n"
        "      \"input_refs\": {},\n"
        "      \"output_type\": \"text\",\n"
        "      \"status\": \"pending\"\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Output ONLY raw JSON code. Do not include markdown code block formatting or explanation text."
    )
    
    provider = provider_manager.active_provider
    plan_json = ""
    parsed_plan = None
    
    # First planning attempt
    try:
        resp = await provider.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task.user_query}
        ])
        if not resp["success"]:
            raise RuntimeError(f"Provider failed: {resp['error']}")
            
        choices = resp["data"].get("choices", [])
        raw_text = choices[0].get("message", {}).get("content", "") if choices else resp["data"].get("reply", "")
        plan_json = re.sub(r"```json|```", "", raw_text).strip()
        parsed_plan = ExecutionPlan.model_validate_json(plan_json)
        
    except Exception as e:
        logger.warning(f"Initial planning attempt failed validation/completion: {str(e)}. Triggering repair loop...")
        
        # Validation repair loop (attempt once)
        try:
            repair_prompt = (
                f"Your previous JSON plan failed validation with error: {str(e)}.\n"
                f"Here is the incorrect JSON you returned:\n{plan_json}\n\n"
                "Please repair the JSON plan, ensuring it strictly matches the schema and has correct Pydantic fields. Return ONLY valid JSON."
            )
            resp = await provider.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": repair_prompt}
            ])
            if not resp["success"]:
                raise RuntimeError(f"Repair provider failed: {resp['error']}")
                
            choices = resp["data"].get("choices", [])
            raw_text = choices[0].get("message", {}).get("content", "") if choices else resp["data"].get("reply", "")
            plan_json = re.sub(r"```json|```", "", raw_text).strip()
            parsed_plan = ExecutionPlan.model_validate_json(plan_json)
            
        except Exception as e2:
            logger.error(f"Planning repair loop failed: {str(e2)}")
            task.status = "planning_failed"
            task.error = StepError(
                error_type="validation_error",
                message=f"Plan generation failed validation: {str(e2)}",
                details={"original_error": str(e), "repair_error": str(e2), "raw_json": plan_json}
            )
            task.updated_at = datetime.now().isoformat()
            task_store.save_task(task)
            return state

    # Save generated plan
    task.plan = parsed_plan
    task.status = "pending_approval"
    task.updated_at = datetime.now().isoformat()
    task_store.save_task(task)
    return state

async def execute_steps_node(state: CompanyState) -> CompanyState:
    """Executes the plan steps sequentially using a simple Python loop with safety checks."""
    task_id = state["task_id"]
    task = task_store.load_task(task_id)
    if not task or task.status != "executing":
        return state
        
    logger.info(f"Starting plan steps execution for task {task_id}")
    
    if not task.started_at:
        task.started_at = datetime.now().isoformat()
    
    # Process steps sequentially
    for step in task.plan.steps:
        # 1. Pre-step check: Verify task hasn't been cancelled by user API call
        db_state = task_store.load_task(task_id)
        if db_state.status == "cancelled":
            logger.warning(f"Task {task_id} execution was cancelled. Stopping.")
            break
            
        # Skip if already completed
        if step.status == "completed":
            continue
            
        # 2. Dependency verification
        dependency_failed_or_skipped = False
        for dep_id in step.depends_on:
            dep_result = task.step_results.get(dep_id)
            if dep_result and dep_result.status in ["failed", "skipped"]:
                dependency_failed_or_skipped = True
                break
                
        if dependency_failed_or_skipped:
            logger.warning(f"Skipping step '{step.step_id}' because dependency failed or was skipped.")
            step.status = "skipped"
            task.step_results[step.step_id] = StepResult(
                step_id=step.step_id,
                status="skipped",
                output_artifact_ids=[]
            )
            task.updated_at = datetime.now().isoformat()
            task_store.save_task(task)
            continue
            
        # 3. Mark step as running
        step.status = "running"
        step_result = StepResult(
            step_id=step.step_id,
            status="running",
            started_at=datetime.now().isoformat()
        )
        task.step_results[step.step_id] = step_result
        task_store.save_task(task)
        
        # 4. Resolve inputs using input_refs
        inputs = {}
        try:
            for input_key, ref_id in step.input_refs.items():
                if ref_id == "user_input_text_0":
                    inputs[input_key] = task.user_query
                elif ref_id == "user_input_image_0":
                    # User-provided base image path (e.g. from task metadata if provided)
                    # We will lookup task details or set placeholder
                    inputs[input_key] = "workspace/user_input_image_0.png"
                elif ref_id.startswith("artifact_"):
                    # Find stable artifact
                    matching_art = next((art for art in task.artifacts if art.artifact_id == ref_id), None)
                    if not matching_art:
                        raise ValueError(f"Required artifact reference '{ref_id}' not found.")
                        
                    if matching_art.type == "text":
                        # Read text file content
                        local_path = task_store.workspace_root.joinpath(matching_art.path_or_url)
                        if local_path.exists():
                            with open(local_path, "r", encoding="utf-8") as f:
                                inputs[input_key] = f.read()
                        else:
                            inputs[input_key] = matching_art.path_or_url
                    else:
                        # Image or file path reference
                        inputs[input_key] = matching_art.path_or_url
                else:
                    inputs[input_key] = ref_id
                    
            # 5. Run the worker capability registry execution
            worker = worker_registry.get_worker(step.worker_name)
            generated_artifacts = await worker.execute(step.instruction, inputs, task.task_id, step.step_id)
            
            # 6. Save results on success
            for art in generated_artifacts:
                task.artifacts.append(art)
                
            step.status = "completed"
            step_result.status = "completed"
            step_result.output_artifact_ids = [art.artifact_id for art in generated_artifacts]
            step_result.completed_at = datetime.now().isoformat()
            
            task.step_results[step.step_id] = step_result
            task.updated_at = datetime.now().isoformat()
            
            # Check if task was cancelled in the background during execution
            db_state = task_store.load_task(task_id)
            if db_state and db_state.status == "cancelled":
                task.status = "cancelled"
                task.error = db_state.error
                task.completed_at = db_state.completed_at
                task_store.save_task(task)
                break
                
            task_store.save_task(task)
            
        except Exception as e:
            logger.exception(f"Step '{step.step_id}' execution failed: {str(e)}")
            step.status = "failed"
            step_result.status = "failed"
            step_result.error = StepError(
                error_type="worker_error" if not isinstance(e, RuntimeError) else "provider_error",
                message=str(e),
                details={}
            )
            step_result.completed_at = datetime.now().isoformat()
            task.step_results[step.step_id] = step_result
            
            # Check if task was cancelled in the background during execution
            db_state = task_store.load_task(task_id)
            if db_state and db_state.status == "cancelled":
                task.status = "cancelled"
                task.error = db_state.error
                task.completed_at = db_state.completed_at
                task_store.save_task(task)
                break
                
            task.status = "failed"
            task.error = step_result.error
            task.updated_at = datetime.now().isoformat()
            task_store.save_task(task)
            break  # Stop sequential loop on failure
            
    return state

async def summary_node(state: CompanyState) -> CompanyState:
    """Generates the final consulting summary consolidating all worker outputs."""
    task_id = state["task_id"]
    task = task_store.load_task(task_id)
    if not task or task.status != "executing":
        return state
        
    logger.info(f"Generating final consulting report summary for task {task_id}")
    
    # Aggregate text outcomes from artifacts
    artifacts_text = ""
    for art in task.artifacts:
        if art.type == "text":
            local_path = task_store.workspace_root.joinpath(art.path_or_url)
            content = ""
            if local_path.exists():
                with open(local_path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = art.path_or_url
            artifacts_text += f"Artifact [{art.artifact_id}]:\n{content}\n\n"
            
    summary_prompt = (
        f"You are the Supervisor Agent summarizing the completed project deliverables.\n\n"
        f"User Query:\n{task.user_query}\n\n"
        f"Delivered Artifacts:\n{artifacts_text}\n"
        "Please provide a polished, executive-level consulting report. Summarize what was accomplished "
        "and synthesize the text deliverables nicely. Keep it professional."
    )
    
    provider = provider_manager.active_provider
    try:
        resp = await provider.chat([
            {"role": "system", "content": "You are the Lead Partner at DB AI Consulting. Write structured, premium executive summaries."},
            {"role": "user", "content": summary_prompt}
        ])
        if resp["success"]:
            choices = resp["data"].get("choices", [])
            reply = choices[0].get("message", {}).get("content", "") if choices else resp["data"].get("reply", "")
            
            task.final_summary = reply
            task.status = "completed"
            task.completed_at = datetime.now().isoformat()
        else:
            raise RuntimeError(f"Summary provider failed: {resp['error']}")
    except Exception as e:
        logger.exception("Summary generation failed")
        task.status = "failed"
        task.error = StepError(
            error_type="provider_error",
            message=f"Consolidated summary generation failed: {str(e)}",
            details={}
        )
        
    task.updated_at = datetime.now().isoformat()
    task_store.save_task(task)
    return state

# Compile LangGraph Workflow
company_workflow = StateGraph(CompanyState)
company_workflow.add_node("plan", plan_node)
company_workflow.add_node("execute_steps", execute_steps_node)
company_workflow.add_node("summary", summary_node)

company_workflow.set_entry_point("plan")

# Sequential flow for MVP: planning leads to summary node once execution is approved
# Graph definition is simple
company_workflow.add_edge("plan", END)  # Stops at planning pending approval
company_workflow.add_edge("execute_steps", "summary")
company_workflow.add_edge("summary", END)

company_graph = company_workflow.compile()

# Separate workflow for execution after approval
execution_workflow = StateGraph(CompanyState)
execution_workflow.add_node("execute_steps", execute_steps_node)
execution_workflow.add_node("summary", summary_node)
execution_workflow.set_entry_point("execute_steps")
execution_workflow.add_edge("execute_steps", "summary")
execution_workflow.add_edge("summary", END)
company_execution_graph = execution_workflow.compile()

