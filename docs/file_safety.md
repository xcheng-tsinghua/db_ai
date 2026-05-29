# File safety validation rules

The local file agent operates under strict sandbox policies to prevent path traversals and accidental data modifications.

## Safety Measures

### 1. Workspace Root Lockdown
All file paths are resolved relative to the configured `FILE_WORKSPACE_ROOT` absolute path. Any path resolving outside of this folder structure (e.g. `../../` or Windows volume routes like `C:/Windows`) will raise a `ValueError` block.

### 2. Proposal Dry-Run Mode
All modification operations (Write, Replace, Delete) run in dry-run mode by default. The file agent generates a modification plan:
*   Summary of actions (Overwrite, Segment replace, Delete).
*   A color-coded unified diff highlighting additions and removals.
*   Modifications are not applied to the disk until the user explicitly clicks the validation approve request.

### 3. Automatic Backups
Before overwriting, modifying, or deleting files, the file agent makes a backup copy under the `.agent_backups/` directory. Backups are timestamped:
`{timestamp}_{original_filename}.bak`

### 4. File Constraint Refusals
*   **Binary Protection:** The agent scans file segments for null bytes (`\x00`). If a file is recognized as binary, the agent refuses edit commands.
*   **Size Constraint:** The agent refuses to process edits on files exceeding the configured limit (e.g., 10MB) to prevent buffer overflows or high memory overheads.
