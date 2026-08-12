from flask import Flask, request, jsonify
import subprocess
import sys

app = Flask(__name__, static_folder='static', static_url_path='/static')

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/run', methods=['POST'])
def run_code():
    data = request.get_json(silent=True) or {}
    code = data.get('code', '')
    user_input = data.get('inputs', '')

    if not code.strip():
        return jsonify({"status": "error", "error": "Please provide Python code."})

    try:
        # This opens a background terminal, runs the code, and passes your inputs to it!
        process = subprocess.run(
            [sys.executable, "-c", code],
            input=user_input,
            text=True,
            capture_output=True,
            timeout=5 # Kills the code if it gets stuck in an infinite loop
        )
        
        return jsonify({
            "status": "success",
            "output": process.stdout,
            "error": process.stderr
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({"status": "error", "error": "Execution timed out (Infinite loop?)."})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

if __name__ == '__main__':
    app.run()