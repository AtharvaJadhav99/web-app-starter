
import pathlib
import subprocess
from typing import Tuple

from langchain_core.tools import tool

PROJECT_ROOT = pathlib.Path.cwd() / "generated_project"


def safe_path_for_project(path: str) -> pathlib.Path:
    p = (PROJECT_ROOT / path).resolve()
    if PROJECT_ROOT.resolve() not in p.parents and PROJECT_ROOT.resolve() != p.parent and PROJECT_ROOT.resolve() != p:
        raise ValueError("Attempt to write outside project root")
    return p


def _write_file(path: str, content: str) -> str:
    p = safe_path_for_project(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return f"WROTE:{p}"


def _read_file(path: str) -> str:
    p = safe_path_for_project(path)
    if not p.exists():
        return ""
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def _list_files(directory: str = ".") -> str:
    p = safe_path_for_project(directory)
    if not p.is_dir():
        return f"ERROR: {p} is not a directory"
    files = [str(f.relative_to(PROJECT_ROOT)) for f in p.glob("**/*") if f.is_file()]
    return "\n".join(files) if files else "No files found."


@tool
def write_file(path: str, content: str) -> str:
    """Writes content to a file at the specified path within the project root."""
    return _write_file(path, content)


@tool
def read_file(path: str) -> str:
    """Reads content from a file at the specified path within the project root."""
    return _read_file(path)


@tool
def get_current_directory() -> str:
    """Returns the current working directory."""
    return str(PROJECT_ROOT)


@tool
def list_files(directory: str = ".") -> str:
    """Lists all files in the specified directory within the project root."""
    return _list_files(directory)


@tool("write")
def write_alias(path: str, content: str) -> str:
    """Compatibility alias for write_file."""
    return _write_file(path, content)


@tool("read")
def read_alias(path: str) -> str:
    """Compatibility alias for read_file."""
    return _read_file(path)


@tool("list")
def list_alias(directory: str = ".") -> str:
    """Compatibility alias for list_files."""
    return _list_files(directory)


@tool("repo_browser.read")
def repo_browser_read_alias(path: str) -> str:
    """Compatibility alias for model-generated repo_browser.read tool calls."""
    return _read_file(path)


@tool("repo_browser.list")
def repo_browser_list_alias(directory: str = ".") -> str:
    """Compatibility alias for model-generated repo_browser.list tool calls."""
    return _list_files(directory)


@tool("repo_browser.write")
def repo_browser_write_alias(path: str, content: str) -> str:
    """Compatibility alias for model-generated repo_browser.write tool calls."""
    return _write_file(path, content)

@tool
def run_cmd(cmd: str, cwd: str = None, timeout: int = 30) -> Tuple[int, str, str]:
    """Runs a shell command in the specified directory and returns the result."""
    cwd_dir = safe_path_for_project(cwd) if cwd else PROJECT_ROOT
    res = subprocess.run(cmd, shell=True, cwd=str(cwd_dir), capture_output=True, text=True, timeout=timeout)
    return res.returncode, res.stdout, res.stderr


def init_project_root():
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    return str(PROJECT_ROOT)
