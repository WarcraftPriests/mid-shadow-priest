# Copilot Instructions for mid-shadow-priest

## Project Purpose
- This repository contains Python scripts and SimulationCraft input files for Shadow Priest simulation workflows.
- Typical work involves generating profiles, running sims, and aggregating result artifacts for analysis.

## Stack and Entry Points
- Language: Python
- Primary scripts:
  - `suite.py`: orchestration for end-to-end sim runs
  - `profiles.py`: profile generation
  - `sim.py`: simulation execution and aggregation
  - `top.py`: selects top talent builds from generated result files
- Primary config:
  - `config.yml`

## Repository Conventions
- Keep changes minimal and focused to the requested task.
- Prefer targeted edits over broad refactors.
- Preserve existing naming conventions for files and actors.
- Preserve generated result filename patterns, including sim type names like `Composite`, `Single`, and `Dungeons-Route`.
- Result files can be produced in stages; readers should tolerate missing intermediate files when that is valid for partial runs.

## Generated Artifacts
- Many folders contain generated output (for example `output/` and `results/` directories under sim folders).
- Do not modify or delete generated artifacts unless explicitly asked.
- Avoid introducing changes to large generated CSV/Markdown result files when solving code issues.

## Secrets and Local Environment
- Never hardcode API keys or local paths.
- Respect `api_secrets.py` and `local_secrets.py` as local/private configuration.
- Keep solutions compatible with local and CI usage where possible.

## Development Workflow
- Read `config.yml` before changing simulation behavior.
- For simulation pipeline issues, trace flow in this order:
  1. `profiles.py`
  2. `sim.py`
  3. aggregation/analyze helpers in `internal/`
  4. `top.py`/`suite.py`
- For route or dungeon behavior, verify naming consistency between producers and consumers of result files.

## Validation Commands
- Use the project virtual environment when present.
- Lint:
  - `ruff check .`
- Tests:
  - `pytest`
  - `pytest --cov=. --cov-report=term-missing -q`
- Prefer targeted tests for changed modules first, then broader test runs as needed.

## Editing Guidelines
- Keep comments concise and only where logic is non-obvious.
- Do not rename public scripts or major config keys unless explicitly requested.
- Maintain backward-compatible CLI behavior unless the request requires a breaking change.
- If fixing a bug, add or update a focused regression test when feasible.

## Communication Expectations
- Explain assumptions and constraints briefly.
- Call out when validation could not be fully completed and why.
- Surface risks around partial-run state and generated artifacts when relevant.
