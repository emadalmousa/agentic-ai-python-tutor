import sys
import os

# Ensure the backend package root is on sys.path so that `import agent` works
# regardless of the directory pytest is invoked from.
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# Ensure venv site-packages are on sys.path so dependencies like python-multipart
# are found even when pytest is invoked via the system Python.
VENV_SITE = os.path.join(BACKEND_ROOT, "venv", "lib", "python3.12", "site-packages")
if os.path.isdir(VENV_SITE) and VENV_SITE not in sys.path:
    sys.path.insert(1, VENV_SITE)
