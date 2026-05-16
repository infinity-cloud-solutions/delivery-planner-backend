import os
import pathlib
import sys

root_path = pathlib.Path(__file__).parent.parent.parent
sys.path.append(str(root_path))
delivery_path = os.path.join(root_path, "src/orders/delivery")
sys.path.append(delivery_path)
orders_path = os.path.join(root_path, "src/orders")
sys.path.append(orders_path)
