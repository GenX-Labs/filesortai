import shutil
from pathlib import Path

def organize(filepath: str, folder_name: str, output_dir: str) -> str:
    dest_folder = Path(output_dir) / folder_name
    dest_folder.mkdir(parents=True, exist_ok=True)
    dest = dest_folder / Path(filepath).name
    shutil.move(filepath, dest)
    return str(dest)