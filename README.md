# J.A.R.V.I.S — assistant prototype

An alpha assistant combining Ollama/optional Apple MLX, model routing, memory,
tool experiments, voice and a React/Three.js interface. This is a broad
multi-component prototype. The implemented modules and historical roadmap do not
establish a production-ready assistant or verified support for every device.

It is independent of `jarvis-core`: this repository installs the `jarvis` package
and uses `python -m jarvis.api.main`; the other project has a separate deterministic
policy/state-machine core and different contracts. Keep their environments separate.

## Components

`jarvis/core/` routes/orchestrates requests; `models/` adapts Ollama/MLX;
`memory/` uses Redis, ChromaDB and SQLite profile storage; `tools/` contains
web/code/shell and other integrations; `voice/` experiments with speech and wake
words. `jarvis/api/` exposes FastAPI routes, `ui/` is the visual React client,
and `clients/` contains separate iOS/Windows client work.

## Development setup

Use Python 3.12 for the tested environment and supported Node 22 for the UI.
Apple MLX/voice extras need compatible macOS/Apple Silicon; they are not portable
dependencies for every platform.

```bash
git clone https://github.com/M-Fatih-C/J.A.R.V.I.S.git
cd J.A.R.V.I.S
uv sync --locked --extra dev
cp .env.example .env
# Configure your own secrets and optional services before starting.
uv run python -m jarvis.api.main
```

The server now defaults to **127.0.0.1:8000** in both code and the example config.
Provide your own local Ollama and, where needed, Redis/ChromaDB services; the
Compose file describes supporting services, not a verified production deployment.
MLX can be installed with `uv sync --locked --extra dev --extra mlx` on supported
hardware. Do not download large models merely to run the offline contract suite.

UI development is separate:

```bash
cd ui
npm ci --ignore-scripts
npm run build
```

## Tests and status

```bash
uv run pytest -q
uv run ruff check .
```

The baseline dev-only test collection needed optional MLX installed; the test now
explicitly skips that module when MLX is absent. Two health contract tests previously
attempted real provider connections; they now override only those dependencies
with offline unavailable-service adapters, retaining the actual endpoint/auth tests.
With the MLX extra installed, the updated suite passed 158 tests and skipped 7
explicitly gated/platform-dependent cases with external sockets blocked. New
configuration tests check loopback and production-secret rejection.
Real-model, voice and end-to-end tests remain opt-in or platform-dependent and are
not claimed as passed. The audit built the UI successfully; it emitted a large-chunk
warning. Inspect the current PR checks and validation notes for exact results.

## Security and privacy boundaries

Set unique JWT, device and SQLite-profile encryption secrets before storing data.
`ENV=prod` now rejects disabled authentication, example keys and keys shorter than
32 characters. This validation and loopback default reduce configuration mistakes;
they are not production certification. Changing a profile-encryption key can make
existing values unreadable; plan a separate data migration/backup procedure.

Profile encryption applies to selected values, not the whole SQLite database or
every log/cache. Web, mail and configurable remote services may send data outside
the machine. Tool execution, filesystem access, shell commands and network exposure
require explicit trust and further review. Keep keys, personal conversations,
recordings, indexes and generated files out of commits. No unconditional “all data
stays local”, full-database encryption or performance claim is made.


## License and contact

See the existing [MIT license](LICENSE). Author: [Muhammet Fatih Çetintaş](https://github.com/M-Fatih-C).
