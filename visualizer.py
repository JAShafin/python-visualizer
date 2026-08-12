import ast
import builtins
import io
import multiprocessing
import os
import sys
import tempfile
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import Any

try:
    import resource
except ImportError:  # pragma: no cover - unavailable on some platforms
    resource = None

TIMEOUT_SECONDS = 2
MEMORY_LIMIT_BYTES = 128 * 1024 * 1024
MAX_STEPS = 500
MAX_REPR_LENGTH = 120

ALLOWED_IMPORTS = {
    "math",
    "random",
    "statistics",
    "itertools",
    "functools",
    "collections",
}
BLOCKED_BUILTINS = {
    "open",
    "input",
    "exec",
    "eval",
    "compile",
    "globals",
    "locals",
    "vars",
    "help",
    "dir",
    "breakpoint",
    "__import__",
}


class SecurityError(Exception):
    """Raised when user code violates sandbox policy."""


@dataclass
class SecurityVisitor(ast.NodeVisitor):
    """Validate code for prohibited operations before execution."""

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            module = alias.name.split(".", 1)[0]
            if module not in ALLOWED_IMPORTS:
                raise SecurityError(f"Import '{module}' is not allowed.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        module = (node.module or "").split(".", 1)[0]
        if module not in ALLOWED_IMPORTS:
            raise SecurityError(f"Import from '{module}' is not allowed.")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_BUILTINS:
            raise SecurityError(f"Call to '{node.func.id}' is blocked.")
        self.generic_visit(node)


class ExecutionTracer:
    def __init__(self, stdout_buffer: io.StringIO):
        self.stdout_buffer = stdout_buffer
        self.events: list[dict[str, Any]] = []

    def trace(self, frame, event, arg):
        if frame.f_code.co_filename != "<user_code>":
            return self.trace
        if event in {"line", "call", "return", "exception"}:
            if len(self.events) >= MAX_STEPS:
                raise TimeoutError("Execution produced too many trace steps.")
            self.events.append(
                {
                    "event": event,
                    "line": frame.f_lineno,
                    "function": frame.f_code.co_name,
                    "locals": self._serialize_namespace(frame.f_locals),
                    "globals": self._serialize_namespace(frame.f_globals, include_dunder=False),
                    "stack": self._serialize_stack(frame),
                    "stdout": self.stdout_buffer.getvalue(),
                    "exception": self._serialize_exception(arg) if event == "exception" else None,
                }
            )
        return self.trace

    def _serialize_exception(self, arg: Any) -> str:
        if not isinstance(arg, tuple) or len(arg) < 2:
            return ""
        exc_type, exc_value = arg[0], arg[1]
        return f"{getattr(exc_type, '__name__', 'Exception')}: {exc_value}"

    def _serialize_stack(self, frame) -> list[dict[str, Any]]:
        stack: list[dict[str, Any]] = []
        current = frame
        while current is not None:
            if current.f_code.co_filename == "<user_code>":
                stack.append(
                    {
                        "function": current.f_code.co_name,
                        "line": current.f_lineno,
                    }
                )
            current = current.f_back
        stack.reverse()
        return stack

    def _serialize_namespace(self, namespace: dict[str, Any], include_dunder: bool = True) -> dict[str, str]:
        serialized: dict[str, str] = {}
        for key, value in namespace.items():
            if key == "__builtins__":
                continue
            if not include_dunder and key.startswith("__"):
                continue
            serialized[key] = self._safe_repr(value)
        return serialized

    def _safe_repr(self, value: Any) -> str:
        try:
            text = repr(value)
        except Exception:  # pragma: no cover - defensive
            text = f"<{type(value).__name__}>"
        if len(text) > MAX_REPR_LENGTH:
            return f"{text[:MAX_REPR_LENGTH]}..."
        return text


def _limited_import(name, globals=None, locals=None, fromlist=(), level=0):
    module = name.split(".", 1)[0]
    if module not in ALLOWED_IMPORTS:
        raise ImportError(f"Import '{module}' is blocked in sandbox")
    return builtins.__import__(name, globals, locals, fromlist, level)


def _safe_builtins() -> dict[str, Any]:
    safe = {}
    for key in dir(builtins):
        if key.startswith("_"):
            continue
        if key in BLOCKED_BUILTINS:
            continue
        safe[key] = getattr(builtins, key)
    safe["__import__"] = _limited_import
    return safe


def _apply_limits() -> None:
    if resource is None:
        return
    resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT_SECONDS, TIMEOUT_SECONDS + 1))
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))


def _validate(code: str) -> None:
    tree = ast.parse(code, mode="exec")
    SecurityVisitor().visit(tree)


def _worker(code: str, queue: multiprocessing.Queue):
    try:
        _apply_limits()
        _validate(code)
        compiled = compile(code, "<user_code>", "exec")
        stdout_buffer = io.StringIO()
        tracer = ExecutionTracer(stdout_buffer)
        namespace = {"__builtins__": _safe_builtins()}

        with tempfile.TemporaryDirectory() as tmpdir:
            previous_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with redirect_stdout(stdout_buffer):
                    sys.settrace(tracer.trace)
                    exec(compiled, namespace, namespace)
            finally:
                sys.settrace(None)
                os.chdir(previous_cwd)

        queue.put(
            {
                "status": "ok",
                "events": tracer.events,
                "stdout": stdout_buffer.getvalue(),
                "error": None,
            }
        )
    except SecurityError as exc:
        queue.put({"status": "security_error", "events": [], "stdout": "", "error": str(exc)})
    except BaseException as exc:  # pragma: no cover - child process safety
        queue.put(
            {
                "status": "runtime_error",
                "events": tracer.events if "tracer" in locals() else [],
                "stdout": stdout_buffer.getvalue() if "stdout_buffer" in locals() else "",
                "error": f"{type(exc).__name__}: {exc}",
            }
        )


def run_user_code(code: str) -> dict[str, Any]:
    queue: multiprocessing.Queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=_worker, args=(code, queue))
    process.start()
    process.join(TIMEOUT_SECONDS + 0.5)

    if process.is_alive():
        process.terminate()
        process.join()
        return {
            "status": "timeout",
            "events": [],
            "stdout": "",
            "error": "Execution timed out. Check for long loops.",
        }

    if queue.empty():
        return {
            "status": "runtime_error",
            "events": [],
            "stdout": "",
            "error": "Execution failed before returning a trace.",
        }

    return queue.get()
