import sys
import subprocess
import tempfile
from typing import Dict, Any


class SandboxExecutor:
    """Executes Python code strings safely in an isolated subprocess."""

    def __init__(self, timeout_seconds: int = 10):
        self.timeout_seconds = timeout_seconds

    def run_code(self, code_str: str) -> Dict[str, Any]:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
            tmp_file.write(code_str)
            tmp_file_path = tmp_file.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_file_path],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            success = result.returncode == 0
            return {
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr if not success else "",
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"TimeoutError: Execution exceeded {self.timeout_seconds} seconds.",
                "exit_code": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"SystemError: {str(e)}",
                "exit_code": -1,
            }
