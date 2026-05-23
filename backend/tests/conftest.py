import sys
import os

# Ensure the backend package root is on sys.path so that `import agent` works
# regardless of the directory pytest is invoked from.
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)
