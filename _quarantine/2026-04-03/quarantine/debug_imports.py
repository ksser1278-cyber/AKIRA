import sys
from pathlib import Path
import traceback

# Mimic the path setup in scripts/songwriter/run_demo_songwriter.py
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))

print(f"DEBUG: sys.path[0] = {sys.path[0]}")

try:
    print("DEBUG: Attempting to import src.akira_engine.demo_runtime...")
    from src.akira_engine.demo_runtime import run_demo_songwriter
    print("DEBUG: SUCCESS! run_demo_songwriter imported.")
except Exception:
    print("DEBUG: FAILURE! Full traceback below:")
    traceback.print_exc()
