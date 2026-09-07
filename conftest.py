import sys
import os

# Add src/orders to sys.path so that `order_modules` is importable using the same
# module identity as the production code. This ensures patches and enum comparisons
# in tests operate on the same module instances.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "orders"))
