from flask import Flask, jsonify, request, send_from_directory

from visualizer import run_user_code


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static")

    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.post("/api/trace")
    def trace_code():
        payload = request.get_json(silent=True) or {}
        code = payload.get("code", "")
        if not isinstance(code, str) or not code.strip():
            return jsonify({"status": "error", "error": "Please provide Python code."}), 400
        result = run_user_code(code)
        return jsonify(result)

    return app


app = create_app()


if __name__ == "__main__":
    app.run()
