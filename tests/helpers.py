"""Shared helpers for the startai test suite."""
import importlib.util
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(REPO_ROOT, "scripts", "startai.py")
TEMPLATES_DIR = os.path.join(REPO_ROOT, "templates")
CONFIG_EXAMPLE = os.path.join(REPO_ROOT, "config.example.json")

_module = None


def load_module():
    """Load scripts/startai.py once and return it as a module (without running main)."""
    global _module
    if _module is None:
        spec = importlib.util.spec_from_file_location("startai", SCRIPT_PATH)
        _module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_module)
    return _module
