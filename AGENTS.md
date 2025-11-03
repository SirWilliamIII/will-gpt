# Repository Guidelines

## Project Structure & Module Organization
- `parsers/` holds platform adapters (e.g., `chatgpt_parser.py`, `claude_parser.py`) and shared abstractions in `base_parser.py`.
- `retrieval/` contains Qdrant-facing search logic, while `embeddings/` manages vector generation workflows.
- `api/` and `frontend/` provide the FastAPI backend and React UI scaffolding; container orchestration lives in `podman-compose.yml` and the `Dockerfile`.
- Place raw exports in `data/raw/`; derived artifacts should land in `data/processed/` to keep large datasets out of source control.

## Build, Test, and Development Commands
- `make build` compiles container images defined in `podman-compose.yml`.
- `make up` (or `make up-jupyter`) starts the full stack; Qdrant dashboard appears at `http://localhost:6333/dashboard`.
- `make test-parser` / `make test-claude` exercise the parser pipeline against exports in `data/raw/`.
- `make search` opens the interactive CLI search client; use `make query QUERY="…" ` for single-shot lookups.

## Coding Style & Naming Conventions
- Target Python 3.13; run `uv pip install -r requirements.txt` or `uv sync` when dependencies change.
- Format code with `black` before submitting; keep imports sorted and prefer explicit type hints in new modules.
- Module and package names stay lowercase with underscores; classes use `PascalCase`, functions and variables use `snake_case`.
- Keep parser outputs self-describing—favor structured dataclasses over ad-hoc dicts for new payloads.

## Testing Guidelines
- Use the provided `make test-*` targets; they mount the running app container and validate against real exports.
- Seed required fixtures (e.g., `data/raw/chatgpt.json`) before running tests; add lightweight synthetic samples under `tests/fixtures/` when possible.
- Extend test scripts with scenario-focused helper functions rather than adding new binaries; keep logs informative but concise.

## Commit & Pull Request Guidelines
- Follow commit prefixes observed in history (`feat:`, `fix:`, `refactor:`) and keep subject lines under ~72 characters.
- Reference related issues in the body using `Closes #123` when applicable and describe any data migrations or schema changes explicitly.
- Pull requests should summarize the user impact, list validation steps (`make test-parser`, `make search`), and include screenshots or CLI transcripts for UI or retrieval behavior changes.
