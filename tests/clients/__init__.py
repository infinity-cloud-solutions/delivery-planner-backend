import pathlib
import sys
import os

root_path = pathlib.Path(__file__).parent.parent.parent
clients_path = os.path.join(root_path, "src/clients")
sys.path.append(clients_path)
