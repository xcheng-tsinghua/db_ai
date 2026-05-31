import os
import json
import logging
from pathlib import Path
from typing import List, Optional
from backend.app.config import settings
from backend.app.company.models import TaskState

logger = logging.getLogger(__name__)

class TaskStore:
    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = Path(workspace_root or settings.FILE_WORKSPACE_ROOT).resolve()
        self.tasks_root = self.workspace_root.joinpath("tasks")
        os.makedirs(self.tasks_root, exist_ok=True)

    def get_task_dir(self, task_id: str) -> Path:
        """Returns the task specific folder path."""
        task_dir = self.tasks_root.joinpath(task_id)
        os.makedirs(task_dir, exist_ok=True)
        return task_dir

    def get_artifacts_dir(self, task_id: str) -> Path:
        """Returns the folder path for storing task intermediate files/artifacts."""
        art_dir = self.get_task_dir(task_id).joinpath("artifacts")
        os.makedirs(art_dir, exist_ok=True)
        return art_dir

    def save_task(self, state: TaskState) -> None:
        """Saves/Updates the task state to disk as task.json."""
        try:
            task_dir = self.get_task_dir(state.task_id)
            state_file = task_dir.joinpath("task.json")
            
            # Serialize using Pydantic's model_dump_json
            with open(state_file, "w", encoding="utf-8") as f:
                f.write(state.model_dump_json(indent=2))
                
            logger.info(f"Task state saved: {state.task_id} (status: {state.status})")
        except Exception as e:
            logger.exception(f"Failed to save task state: {state.task_id}")
            raise IOError(f"Could not persist task: {str(e)}") from e

    def load_task(self, task_id: str) -> Optional[TaskState]:
        """Loads a task state from task.json if it exists."""
        try:
            task_dir = self.tasks_root.joinpath(task_id)
            state_file = task_dir.joinpath("task.json")
            if not state_file.exists():
                return None
                
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Parse dict into TaskState Pydantic model
            return TaskState.model_validate(data)
        except Exception as e:
            logger.exception(f"Failed to load task state: {task_id}")
            return None

    def list_tasks(self) -> List[TaskState]:
        """Returns all saved tasks sorted by creation date."""
        tasks = []
        try:
            if not self.tasks_root.exists():
                return []
            for item in self.tasks_root.iterdir():
                if item.is_dir():
                    task = self.load_task(item.name)
                    if task:
                        tasks.append(task)
            # Sort by creation timestamp descending
            tasks.sort(key=lambda t: t.created_at, reverse=True)
        except Exception as e:
            logger.exception("Failed listing tasks")
        return tasks

# Global task store singleton
task_store = TaskStore()
