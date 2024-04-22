import pathlib
import sys
import os

root_path = pathlib.Path(__file__).parent.parent.parent
integration_path = os.path.join(root_path, "src/orders/integration")
sys.path.append(integration_path)
