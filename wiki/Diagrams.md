# Diagrams

Mermaid diagrams for Scales live in the main repo under
[`docs/diagrams`](https://github.com/Tempest150/Scales/tree/main/docs/diagrams).
All are flowcharts (rather than mixing in `sequenceDiagram` syntax), using a
consistent convention: solid arrows are exercised by real, wired-up code
paths; dashed arrows/nodes mark things that exist in code or design but
aren't actually connected yet.

| Diagram | Covers |
|---|---|
| [architecture_current.md](https://github.com/Tempest150/Scales/blob/main/docs/diagrams/architecture_current.md) | The server-hosted flow that runs against real Gmail traffic today |
| [architecture_target.md](https://github.com/Tempest150/Scales/blob/main/docs/diagrams/architecture_target.md) | The Tauri desktop end state from `to-do.md` |
| [ingest_seq.md](https://github.com/Tempest150/Scales/blob/main/docs/diagrams/ingest_seq.md) | **Historical** — the old Gmail → n8n → email-cleaner → Quart → Ollama path (see [[Ingest-Pipeline]] for the current flow) |
| [classification_class.md](https://github.com/Tempest150/Scales/blob/main/docs/diagrams/classification_class.md) | `EmailClassifier.Duro` — prompt, Ollama call, parse + verdict gate |
| [db_class.md](https://github.com/Tempest150/Scales/blob/main/docs/diagrams/db_class.md) | `db.py`'s `Rimiru` — asyncpg pool + CRUD helper |
| [data_model.md](https://github.com/Tempest150/Scales/blob/main/docs/diagrams/data_model.md) | ER diagram: `users`/`application`/`messages`, plus FKs into Libra's `company`/`job_list` |

## Higher-level diagrams (kept in the wiki, not per-module)

[[Architecture]] embeds the current and target flowcharts directly, alongside
the module-map prose. `docs/diagrams/` holds the same diagrams as
standalone, linkable files plus the finer-grained class diagrams.

## Keeping these in sync

The backend has grown past its original four files (now `routes/` blueprints,
`logger.py`, `useCheck.py`). When a new module lands (an abstracted LLM
client, a queue consumer, etc.), add a diagram pair for it rather than
folding it into an existing one, matching Libra's per-module convention. If a
diagram and the code it describes drift, regenerate the diagram rather than
hand-patching it — hand-edits drift silently.
