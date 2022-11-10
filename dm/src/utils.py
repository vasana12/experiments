from pathlib import Path
import pandas as pd
import uuid

def get_project_root() -> Path:
    return Path(__file__).parent.parent

def save_file(data:list, directory, file_name =None):
    project_path = Path.cwd().parent
    result_path = project_path.joinpath(directory, file_name)
    df = pd.DataFrame(data)
    file_name = uuid.uuid4() if file_name is None else file_name
    df.to_excel(f"{result_path}/{file_name}.xlsx")

def json_value(data, *args, default=None):
    cur = data
    for a in args:
        try:
            if isinstance(a, int):
                cur = cur[a]
            else:
                cur = cur.get(a)
        except (IndexError, KeyError, TypeError, AttributeError):
            return default
    return cur



if __name__ == "__main__":
    pass
