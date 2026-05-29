import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from backend.app.config import settings
from backend.app.utils.diff import generate_diff

logger = logging.getLogger(__name__)

class LocalFileAgent:
    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = Path(workspace_root or settings.FILE_WORKSPACE_ROOT).resolve()
        self.backup_dir = self.workspace_root.joinpath(".agent_backups")
        
        # Ensure workspace and backup folders exist
        os.makedirs(self.workspace_root, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

    def _resolve_and_validate(self, file_path: str) -> Path:
        """
        Resolves path and checks for path traversal.
        Raises ValueError if path is outside workspace root.
        """
        target = Path(file_path)
        if not target.is_absolute():
            target = self.workspace_root.joinpath(target)
            
        # Resolve target to absolute path
        try:
            resolved_target = target.resolve()
        except Exception:
            # If resolve fails (e.g. invalid chars), use absolute
            resolved_target = target.absolute()
            
        # Check traversal
        root_str = str(self.workspace_root).lower()
        target_str = str(resolved_target).lower()
        
        # Check if target is inside workspace root
        if not target_str.startswith(root_str):
            raise ValueError(f"Path traversal detected: '{file_path}' is resolved to '{resolved_target}' which is outside workspace root '{self.workspace_root}'")
            
        # Do not allow modifying or reading backup folder files via this tool directly
        backup_str = str(self.backup_dir).lower()
        if target_str.startswith(backup_str) and not target_str == backup_str:
            raise ValueError(f"Access Denied: Direct modifications under backup directory '.agent_backups' are prohibited.")
            
        return resolved_target

    def _is_binary(self, file_path: Path) -> bool:
        """Determines if a file is binary by looking for null bytes."""
        if not file_path.exists():
            return False
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                return b"\x00" in chunk
        except Exception:
            return True  # Treat as binary if we can't read it

    def _check_size(self, file_path: Path) -> bool:
        """Checks if file exceeds configured size limit in MB."""
        if not file_path.exists():
            return True
        size_mb = file_path.stat().st_size / (1024 * 1024)
        return size_mb <= settings.FILE_SIZE_LIMIT_MB

    def create_backup(self, file_path: Path) -> Optional[Path]:
        """Creates a timestamped backup of the file under .agent_backups."""
        if not file_path.exists() or file_path.is_dir():
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        relative_to_root = file_path.relative_to(self.workspace_root)
        backup_filename = f"{timestamp}_{relative_to_root.name}.bak"
        backup_path = self.backup_dir.joinpath(backup_filename)
        
        # Create subdirectories if needed inside backup folder
        os.makedirs(backup_path.parent, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created file backup: '{file_path}' -> '{backup_path}'")
        return backup_path

    def list_dir(self, relative_path: str = "") -> Dict[str, Any]:
        """Lists files and directories under workspace root."""
        try:
            target_path = self._resolve_and_validate(relative_path)
            if not target_path.exists():
                return {"success": False, "error": f"Path '{relative_path}' does not exist."}
            if not target_path.is_dir():
                return {"success": False, "error": f"Path '{relative_path}' is not a directory."}
                
            contents = []
            for item in target_path.iterdir():
                # Skip .agent_backups in main listing for clean views
                if item == self.backup_dir:
                    continue
                    
                relative = item.relative_to(self.workspace_root)
                contents.append({
                    "name": item.name,
                    "relative_path": str(relative),
                    "is_dir": item.is_dir(),
                    "size_bytes": item.stat().st_size if item.is_file() else None,
                    "modified_time": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })
            
            logger.info(f"Listed directory: '{relative_path}'")
            return {"success": True, "data": contents, "error": None}
        except Exception as e:
            logger.exception("Directory list failed")
            return {"success": False, "error": str(e)}

    def read_file(self, relative_path: str) -> Dict[str, Any]:
        """Reads contents of a file in the workspace."""
        try:
            target_path = self._resolve_and_validate(relative_path)
            if not target_path.exists():
                return {"success": False, "error": f"File '{relative_path}' does not exist."}
            if target_path.is_dir():
                return {"success": False, "error": f"Path '{relative_path}' is a directory, not a file."}
            if self._is_binary(target_path):
                return {"success": False, "error": f"Refusing to read binary file '{relative_path}'."}
            if not self._check_size(target_path):
                return {"success": False, "error": f"File '{relative_path}' exceeds size limit of {settings.FILE_SIZE_LIMIT_MB}MB."}
                
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
                
            logger.info(f"Read file: '{relative_path}'")
            return {
                "success": True,
                "data": {
                    "content": content,
                    "size_bytes": len(content.encode("utf-8")),
                    "relative_path": relative_path
                },
                "error": None
            }
        except Exception as e:
            logger.exception("File read failed")
            return {"success": False, "error": str(e)}

    def write_file(self, relative_path: str, content: str, dry_run: bool = True) -> Dict[str, Any]:
        """Writes/creates a file in the workspace with dry-run support."""
        try:
            target_path = self._resolve_and_validate(relative_path)
            if target_path.is_dir():
                return {"success": False, "error": f"Path '{relative_path}' is a directory."}
            
            # Check size on existing file if we're overwriting
            if target_path.exists():
                if self._is_binary(target_path):
                    return {"success": False, "error": f"Refusing to overwrite binary file '{relative_path}'."}
                if not self._check_size(target_path):
                    return {"success": False, "error": f"Existing file '{relative_path}' exceeds size limit."}
            
            original_content = ""
            if target_path.exists():
                with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                    original_content = f.read()
            
            # Generate diff
            diff = generate_diff(target_path.name, original_content, content)
            
            plan = f"Write file '{relative_path}':\n"
            if target_path.exists():
                plan += f"- Type: Overwrite existing file\n"
                plan += f"- Diff:\n{diff if diff else '(No changes)'}"
            else:
                plan += f"- Type: Create new file\n"
                plan += f"- Size: {len(content.encode('utf-8'))} bytes"
                
            if dry_run:
                logger.info(f"Dry-run write file: '{relative_path}'")
                return {
                    "success": True,
                    "data": {
                        "dry_run": True,
                        "plan": plan,
                        "diff": diff,
                        "will_overwrite": target_path.exists()
                    },
                    "error": None
                }
            
            # Non dry-run, execute changes
            os.makedirs(target_path.parent, exist_ok=True)
            
            # Backup first if overwriting
            backup_path = self.create_backup(target_path)
            
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            logger.info(f"Wrote file: '{relative_path}' (backup={bool(backup_path)})")
            return {
                "success": True,
                "data": {
                    "dry_run": False,
                    "relative_path": relative_path,
                    "backup_created": str(backup_path.relative_to(self.workspace_root)) if backup_path else None,
                    "diff": diff
                },
                "error": None
            }
        except Exception as e:
            logger.exception("File write failed")
            return {"success": False, "error": str(e)}

    def modify_file(self, relative_path: str, find_str: str, replace_str: str, dry_run: bool = True) -> Dict[str, Any]:
        """Modifies file by replacing find_str with replace_str with safety checks."""
        try:
            target_path = self._resolve_and_validate(relative_path)
            if not target_path.exists():
                return {"success": False, "error": f"File '{relative_path}' does not exist."}
            if target_path.is_dir():
                return {"success": False, "error": f"Path '{relative_path}' is a directory."}
            if self._is_binary(target_path):
                return {"success": False, "error": f"Refusing to edit binary file '{relative_path}'."}
            if not self._check_size(target_path):
                return {"success": False, "error": f"File '{relative_path}' exceeds size limit."}
                
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                original_content = f.read()
                
            if find_str not in original_content:
                return {
                    "success": False,
                    "error": f"Target content block to replace was not found in '{relative_path}'."
                }
                
            # Replace content
            new_content = original_content.replace(find_str, replace_str)
            diff = generate_diff(target_path.name, original_content, new_content)
            
            plan = f"Modify file '{relative_path}':\n- Replace match block\n- Diff:\n{diff}"
            
            if dry_run:
                logger.info(f"Dry-run modify file: '{relative_path}'")
                return {
                    "success": True,
                    "data": {
                        "dry_run": True,
                        "plan": plan,
                        "diff": diff
                    },
                    "error": None
                }
                
            # Backup first
            backup_path = self.create_backup(target_path)
            
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(new_content)
                
            logger.info(f"Modified file: '{relative_path}' (backup={bool(backup_path)})")
            return {
                "success": True,
                "data": {
                    "dry_run": False,
                    "relative_path": relative_path,
                    "backup_created": str(backup_path.relative_to(self.workspace_root)) if backup_path else None,
                    "diff": diff
                },
                "error": None
            }
        except Exception as e:
            logger.exception("File modify failed")
            return {"success": False, "error": str(e)}

    def delete_file(self, relative_path: str, dry_run: bool = True) -> Dict[str, Any]:
        """Deletes file after taking a backup first."""
        try:
            target_path = self._resolve_and_validate(relative_path)
            if not target_path.exists():
                return {"success": False, "error": f"Path '{relative_path}' does not exist."}
                
            plan = f"Delete path '{relative_path}' (Type: {'directory' if target_path.is_dir() else 'file'})"
            
            if dry_run:
                logger.info(f"Dry-run delete path: '{relative_path}'")
                return {
                    "success": True,
                    "data": {
                        "dry_run": True,
                        "plan": plan
                    },
                    "error": None
                }
                
            # Perform backup and delete
            if target_path.is_file():
                backup_path = self.create_backup(target_path)
                os.remove(target_path)
            else:
                # Directory backup (zip it up or copy all files)
                # For simplicity, we zip the directory inside .agent_backups
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                zip_filename = f"{timestamp}_{target_path.name}"
                backup_zip_path = self.backup_dir.joinpath(zip_filename)
                
                # Make archive
                shutil.make_archive(str(backup_zip_path), 'zip', root_dir=target_path.parent, base_dir=target_path.name)
                backup_path = Path(f"{backup_zip_path}.zip")
                
                shutil.rmtree(target_path)
                
            logger.info(f"Deleted path: '{relative_path}' (backup={bool(backup_path)})")
            return {
                "success": True,
                "data": {
                    "dry_run": False,
                    "relative_path": relative_path,
                    "backup_created": str(backup_path.relative_to(self.workspace_root)) if backup_path else None
                },
                "error": None
            }
        except Exception as e:
            logger.exception("Path delete failed")
            return {"success": False, "error": str(e)}
