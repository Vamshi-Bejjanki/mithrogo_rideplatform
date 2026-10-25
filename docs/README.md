# docs

- [`PROJECT_DESIGN.md`](PROJECT_DESIGN.md): product and technical design. The original spec and still the reference for scope and rules. Its "Implementation status" note at the top lists where the code differs.
- [`architecture.md`](architecture.md): target system architecture and how it scales. The MVP runs a smaller subset (see its status note).
- [`api.md`](api.md): REST API reference for what is implemented.

Per-module notes are in `backend/apps/*/README.md`. Setup and where each business rule lives are in [`backend/README.md`](../backend/README.md).

Update these whenever behaviour changes. `database.md`, `ride-lifecycle.md` and `deployment.md` are not written; the schema is in the models and `PROJECT_DESIGN.md` section 9, and the ride state machine is `backend/apps/rides/state.py`.
