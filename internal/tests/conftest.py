import sys
from pathlib import Path

# Ensure the repository root is on sys.path so tests can import modules by filename
# When this file lives in `internal/tests`, two parents up is `mid-shadow-priest`.
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
