import os
import pathlib
import sys

root_path = pathlib.Path(__file__).parent.parent.parent
sys.path.append(str(root_path))
sys.path.append(os.path.join(root_path, "src/orders"))
sys.path.append(os.path.join(root_path, "src/orders/integration"))
