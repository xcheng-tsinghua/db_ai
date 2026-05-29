import difflib

def generate_diff(filename: str, original_content: str, new_content: str) -> str:
    """
    Generates a unified diff between two string contents for a given filename.
    Returns a unified diff format string, or empty string if contents are identical.
    """
    original_lines = original_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        new_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        n=3  # Show 3 lines of context around modifications
    )
    
    return "".join(diff)
