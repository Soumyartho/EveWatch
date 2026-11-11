# EveWatch - BB84 QKD Simulator

Simulates Alice-Bob BB84 key exchange and detects Eve through quantum measurement disturbance.

## Structure (MVC)
- `evewatch/models/` - protocol and quantum logic
- `evewatch/controllers/` - orchestration and experiments
- `evewatch/views/` + `app.py` - Streamlit dashboard
- `experiments/` - paper figures
- `tests/` - pytest suite
- `docs/` - architecture and protocol notes

See [docs/architecture.md](docs/architecture.md).
