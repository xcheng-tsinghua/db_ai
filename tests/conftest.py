import os
import sys

# Automatically add the project root directory to the python import path
# so that running `pytest` directly in the project root resolves the `backend` package.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
