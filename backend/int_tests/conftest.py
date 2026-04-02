"""Configure sys.path so that the openstars package is importable
when pytest is invoked directly from the int_tests/ directory."""

import sys
from pathlib import Path

# Ensure the backend package root (parent of this file's directory) is on the path.
sys.path.insert(0, str(Path(__file__).parent.parent))
