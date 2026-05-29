import os
import shutil
import tempfile
import pytest
from pathlib import Path
from backend.app.tools.file_agent import LocalFileAgent

@pytest.fixture
def temp_workspace():
    # Setup temporary directory for workspace
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir)

def test_path_traversal_prevention(temp_workspace):
    agent = LocalFileAgent(workspace_root=temp_workspace)
    
    # Try traversal outside root
    with pytest.raises(ValueError, match="Path traversal detected"):
        agent._resolve_and_validate("../../some_system_file.txt")
        
    with pytest.raises(ValueError, match="Path traversal detected"):
        agent._resolve_and_validate("C:/Windows/System32/cmd.exe")

def test_dry_run_write_and_modify(temp_workspace):
    agent = LocalFileAgent(workspace_root=temp_workspace)
    filepath = "test_doc.txt"
    content = "Hello, world!"
    
    # Write dry run
    write_resp = agent.write_file(filepath, content, dry_run=True)
    assert write_resp["success"]
    assert write_resp["data"]["dry_run"] is True
    assert "Create new file" in write_resp["data"]["plan"]
    
    # Verify file is not actually written in dry run
    full_path = Path(temp_workspace).joinpath(filepath)
    assert not full_path.exists()
    
    # Apply change for real
    write_resp = agent.write_file(filepath, content, dry_run=False)
    assert write_resp["success"]
    assert write_resp["data"]["dry_run"] is False
    assert full_path.exists()
    assert full_path.read_text(encoding="utf-8") == content

    # Modify dry run
    modify_resp = agent.modify_file(filepath, "world", "agent", dry_run=True)
    assert modify_resp["success"]
    assert modify_resp["data"]["dry_run"] is True
    assert "diff" in modify_resp["data"]
    
    # Verify original content is still unchanged
    assert full_path.read_text(encoding="utf-8") == content

def test_backup_creation(temp_workspace):
    agent = LocalFileAgent(workspace_root=temp_workspace)
    filepath = "notes.txt"
    original_content = "First version"
    
    # Create file
    agent.write_file(filepath, original_content, dry_run=False)
    
    # Overwrite file
    agent.write_file(filepath, "Second version", dry_run=False)
    
    # Check if a backup exists in .agent_backups
    backup_dir = Path(temp_workspace).joinpath(".agent_backups")
    assert backup_dir.exists()
    
    backups = list(backup_dir.glob("*.bak"))
    assert len(backups) == 1
    assert backups[0].name.endswith("_notes.txt.bak")
    
    # Check backup content contains original version
    assert backups[0].read_text(encoding="utf-8") == original_content
