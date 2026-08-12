"""Run and trace user Python code for the visualizer UI."""

from __future__ import annotations

import builtins
import io
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from types import FrameType
from typing import Any


TRACE_FILENAME = "<user_code>"
MAX_REPR_LENGTH = 200

__all__ = ["run_user_code"]


def _safe_repr(value: Any) -> str:
	try:
		rendered = repr(value)
	except Exception:
		rendered = f"<{type(value).__name__}>"

	if len(rendered) > MAX_REPR_LENGTH:
		return rendered[: MAX_REPR_LENGTH - 3] + "..."
	return rendered


def _snapshot_mapping(mapping: dict[str, Any]) -> dict[str, str]:
	return {
		key: _safe_repr(value)
		for key, value in mapping.items()
		if not key.startswith("__")
	}


def _stack_for_frame(frame: FrameType) -> list[dict[str, Any]]:
	stack: list[dict[str, Any]] = []
	current = frame

	while current is not None and current.f_code.co_filename == TRACE_FILENAME:
		stack.append({"function": current.f_code.co_name, "line": current.f_lineno})
		current = current.f_back

	stack.reverse()
	return stack


def _make_event(frame: FrameType, event_type: str, stdout_capture: io.StringIO, user_globals: dict[str, Any]) -> dict[str, Any]:
	event: dict[str, Any] = {
		"event": event_type,
		"function": frame.f_code.co_name,
		"line": frame.f_lineno,
		"stack": _stack_for_frame(frame),
		"locals": _snapshot_mapping(frame.f_locals),
		"globals": _snapshot_mapping(user_globals),
		"stdout": stdout_capture.getvalue(),
	}
	return event


def run_user_code(code: str, stdin_text: str = "") -> dict[str, Any]:
	stdout_capture = io.StringIO()
	stderr_capture = io.StringIO()
	stdin_capture = io.StringIO(stdin_text)

	def mocked_input(prompt: str = "") -> str:
		if prompt:
			print(prompt, end="", file=stdout_capture)
		line = stdin_capture.readline()
		if line == "":
			return ""
		return line.rstrip("\n").rstrip("\r")

	user_builtins = dict(builtins.__dict__)
	user_builtins["input"] = mocked_input

	user_globals: dict[str, Any] = {
		"__name__": "__main__",
		"__builtins__": user_builtins,
	}
	events: list[dict[str, Any]] = []
	previous_trace = sys.gettrace()

	def tracer(frame: FrameType, event: str, arg: Any):
		if frame.f_code.co_filename != TRACE_FILENAME:
			return tracer if event == "call" else None

		if event in {"call", "line", "return"}:
			events.append(_make_event(frame, event, stdout_capture, user_globals))
		elif event == "exception":
			exception_type, exception_value, _ = arg
			exception_event = _make_event(frame, event, stdout_capture, user_globals)
			exception_event["exception"] = f"{exception_type.__name__}: {exception_value}"
			events.append(exception_event)

		return tracer

	try:
		compiled = compile(code, TRACE_FILENAME, "exec")
		with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
			original_stdin = sys.stdin
			sys.stdin = stdin_capture
			try:
				sys.settrace(tracer)
				exec(compiled, user_globals, user_globals)
			finally:
				sys.settrace(previous_trace)
				sys.stdin = original_stdin
	except Exception as exc:
		error_text = "".join(traceback.format_exception_only(type(exc), exc)).strip()
		return {
			"status": "error",
			"error": error_text,
			"stdout": stdout_capture.getvalue(),
			"stderr": stderr_capture.getvalue(),
			"events": events,
		}

	return {
		"status": "ok",
		"stdout": stdout_capture.getvalue(),
		"stderr": stderr_capture.getvalue(),
		"events": events,
	}
