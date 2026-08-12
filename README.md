# python-visualizer

A web MVP to paste Python code, run it in a restricted sandbox, and visualize execution step-by-step to support learning and debugging.

## MVP scope

- Paste your own Python code into a browser editor.
- Run code with a secure backend execution service.
- Visualize step events: current line, locals/globals, call stack, stdout, and runtime errors.
- Step through execution with previous/next controls and a timeline slider.

## User flow and screens

1. Open the editor page (`/`).
2. Pick an example snippet or paste your own code.
3. Click **Run Trace**.
4. Use timeline/step buttons to inspect execution.
5. Inspect synchronized panels for code line highlight, variables, stack, output, and errors.
6. Optionally save/load snippets locally or share the current code via URL.

## Architecture

- **Frontend:** static HTML/CSS/JS in `/static`.
- **Backend:** Flask app (`app.py`) exposing `POST /api/trace`.
- **Tracing layer:** `visualizer.py` performs code validation, sandboxed execution, and event serialization.

## Security model

- Runs user code in an isolated subprocess per request.
- Applies CPU and memory limits (where supported by platform).
- Executes in a temporary working directory.
- Blocks dangerous builtins (`open`, `eval`, `exec`, etc.).
- Restricts imports to a safe allowlist.
- Validates AST before execution to reject disallowed calls/imports.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Deploy on Render

This repository includes `/render.yaml` for one-click Blueprint deploys.

1. Push this repository to GitHub.
2. In Render, click **New +** → **Blueprint**.
3. Select this repository and approve the detected `render.yaml`.
4. Render will run:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app`
5. Open the generated Render URL to use the app on the internet.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Roadmap milestones

- Expand import allowlist and richer policy controls.
- Improve visualization for complex objects and diffs between steps.
- Add persistent snippet storage with user accounts.
- Add async job queue for long-running trace requests.
- Add CI for tests and browser-based UI checks.
