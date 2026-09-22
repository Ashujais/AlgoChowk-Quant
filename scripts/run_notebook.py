from pathlib import Path
import nbformat
from nbclient import NotebookClient

path=Path("notebooks/event_study.ipynb")
nb=nbformat.read(path,as_version=4)
NotebookClient(nb,timeout=900,kernel_name="python3",resources={"metadata":{"path":str(Path.cwd())}}).execute()
nbformat.write(nb,path)
print("Executed",path)
