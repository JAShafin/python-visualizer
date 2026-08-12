from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory

from visualizer import run_user_code


def create_app() -> Flask:
    static_dir = Path(__file__).resolve().parent / "static"
    app = Flask(__name__, static_folder=str(static_dir), static_url_path="/static")

    @app.get("/")
    @app.get("/index.html")
    def index():
        return app.send_static_file("index.html")

    @app.post("/api/trace")
    def trace_code():
        payload = request.get_json(silent=True) or {}
        code = payload.get("code", "")
        if not isinstance(code, str) or not code.strip():
            return jsonify({"status": "error", "error": "Please provide Python code."}), 400
        result = run_user_code(code)
        return jsonify(result)

    @app.get("/<path:path>")
    def static_or_index(path: str):
        if path.startswith("api/"):
            abort(404)
        file_path = static_dir / path
        if file_path.is_file():
            return send_from_directory(static_dir, path)
        return app.send_static_file("index.html")

    return app


app = create_app()


if __name__ == "__main__":
    app.run()
