# EveWatch Architecture (MVC)

| Layer | Package | Responsibility | May import |
|-------|---------|----------------|------------|
| Model | `evewatch/models` | BB84 protocol, Eve, noise, QBER, key finishing, crypto | stdlib, numpy, qiskit |
| Controller | `evewatch/controllers` | Orchestrate models, run experiments | models |
| View | `evewatch/views`, `app.py` | Streamlit UI, plots | controllers, models.types |

Dependency rule: View -> Controller -> Model. Never the reverse.
