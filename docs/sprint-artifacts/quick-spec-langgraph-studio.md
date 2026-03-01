# Quick Spec: LangGraph Studio Integration

## Objective

Enable the existing ACM extraction `StateGraph` to run in LangGraph Studio for local visual debugging, step-through execution, and state inspection, without changing extraction behavior.

## Scope

- Add root `langgraph.json` pointing to the compiled graph export.
- Add a Studio-safe graph entrypoint module (`open_notebook/graphs/studio_entry.py`) that loads `.env` and warns when SurrealDB env config is incomplete.
- Add Studio/LangSmith env entries to `.env.example`.
- Add usage docs in `README.md` for `langgraph-cli` and `langgraph dev`.

## Non-Goals

- No changes to prompts, extraction logic, schema, or graph topology.
- No production deployment changes.

## Implementation Notes

1. Graph export validation:
   - `open_notebook/graphs/acm_extraction.py` exports `graph = agent_state.compile()` at module scope.
   - `langgraph.json` can safely reference that symbol directly.
2. Studio entrypoint:
   - `studio_entry.py` calls `load_dotenv()` and exports `graph` for Studio workflows.
   - Missing SurrealDB config logs a warning only (visualization mode remains usable).
3. Environment:
   - Add explicit LangSmith vars with a safe default (`LANGCHAIN_TRACING_V2=false`).

## Risks and Mitigations

- **Risk:** Studio import failures due to env assumptions.
  - **Mitigation:** `studio_entry.py` loads `.env` and avoids hard DB bootstrapping.
- **Risk:** Conflicts with ongoing unified pipeline work.
  - **Mitigation:** references compiled graph export, no topology edits.

## Verification Plan

- `langgraph dev` starts successfully.
- Studio shows full extraction graph topology.
- Node chain visible includes structure/inventory/tag/orchestrate/validate/correct/dedup/save path.
- Dry-run execution can be initiated from Studio with test input state.
