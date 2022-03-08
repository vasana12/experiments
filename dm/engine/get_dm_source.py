from pathlib import Path

def util_get_source_message(filename):
    project_dir = Path.cwd().parent
    filepath = project_dir.joinpath("source", "message", filename)
    return filepath.read_text()
