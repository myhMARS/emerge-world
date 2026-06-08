"""Code sandbox using subprocess isolation. Works without external dependencies."""

import os
import subprocess
import tempfile
import uuid
from pathlib import Path

SANDBOX_TIMEOUT = 10
MAX_OUTPUT_BYTES = 50 * 1024


def execute(code: str, timeout: int = SANDBOX_TIMEOUT) -> dict:
    tmp_dir = tempfile.mkdtemp(prefix="emerge_sandbox_")
    try:
        script_path = os.path.join(tmp_dir, f"script_{uuid.uuid4().hex[:8]}.py")
        with open(script_path, "w") as f:
            f.write(code)

        try:
            proc = subprocess.run(
                ["python3", "-I", "-s", script_path],
                capture_output=True, text=True,
                timeout=timeout, cwd=tmp_dir,
                env={
                    "PATH": os.environ.get("PATH", "/usr/bin"),
                    "HOME": tmp_dir,
                    "PYTHONPATH": "",
                },
            )
            stdout = proc.stdout[:MAX_OUTPUT_BYTES]
            stderr = proc.stderr[:MAX_OUTPUT_BYTES]
            return {"ok": True, "stdout": stdout, "stderr": stderr, "exit_code": proc.returncode}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"代码执行超时（{timeout} 秒）"}
    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


async def close():
    pass
