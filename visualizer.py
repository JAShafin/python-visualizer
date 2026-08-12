import sys
import io
import traceback

def run_user_code(code, program_inputs=""):
    # 1. Handle multiple inputs properly (split by line, strip whitespace, keep empty lines if needed)
    user_inputs_list = program_inputs.split("\n") if program_inputs else []

    def safe_mock_input(prompt=""):
        if len(user_inputs_list) > 0:
            return user_inputs_list.pop(0)
        return ""  # Gracefully returns empty string if inputs run out, preventing crashes

    trace_steps = []
    output_buffer = io.StringIO()
    
    def trace_calls(frame, event, arg):
        # Only trace the user's actual script, not internal system files
        if frame.f_code.co_filename != "<string>": 
            return trace_calls

        if event in ['line', 'return']:
            # Extract clean variables (ignoring modules, builtins, and functions)
            clean_vars = {
                k: v for k, v in frame.f_locals.items() 
                if not k.startswith('__') 
                and not callable(v) 
                and not str(type(v)) == "<class 'module'>"
            }
            
            # Format explanation text cleanly line-by-line
            if clean_vars:
                var_strings = [f"- '{k}' = {repr(v)}" for k, v in clean_vars.items()]
                explanation = f"Line {frame.f_lineno} executed.\nVariables:\n" + "\n".join(var_strings)
            else:
                explanation = f"Line {frame.f_lineno} executed."

            # Build Call Stack safely for functions and loops
            call_stack = []
            f = frame
            while f and f.f_code.co_filename == "<string>":
                name = "Main Script" if f.f_code.co_name == "<module>" else f.f_code.co_name
                call_stack.insert(0, name)
                f = f.f_back
            
            stack_str = " -> ".join(call_stack) if call_stack else "Main Script"

            trace_steps.append({
                "line": frame.f_lineno,
                "explanation": explanation,
                "call_stack": stack_str,
                "output": output_buffer.getvalue(),
                "error": ""
            })
        return trace_calls

    exec_globals = {
        "__builtins__": __builtins__.copy(),
        "input": safe_mock_input
    }

    old_stdout = sys.stdout
    sys.stdout = output_buffer
    old_trace = sys.gettrace()
    sys.settrace(trace_calls)

    error_msg = ""
    try:
        compiled_code = compile(code, "<string>", "exec")
        exec(compiled_code, exec_globals)
    except Exception as e:
        error_msg = traceback.format_exc().splitlines()[-1]
    finally:
        sys.settrace(old_trace)
        sys.stdout = old_stdout

    if error_msg:
        trace_steps.append({
            "line": None,
            "explanation": "An error occurred during execution.",
            "call_stack": "",
            "output": output_buffer.getvalue(),
            "error": error_msg
        })

    if not trace_steps:
        trace_steps.append({
            "line": None,
            "explanation": "Execution finished.",
            "call_stack": "Main Script",
            "output": output_buffer.getvalue(),
            "error": error_msg
        })

    return trace_steps

__all__ = ["run_user_code"]