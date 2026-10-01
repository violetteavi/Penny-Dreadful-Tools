# Archetype classifier

This folder is the root of the archetype classifier project: its glossary, decisions and agent configuration live here. The repository's top-level AGENTS.md still applies to all code.

## Agent skills

### Issue tracker

Issues live in GitHub Issues on the fork `violetteavi/Penny-Dreadful-Tools`, not upstream. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context, rooted in this folder: `CONTEXT.md` and `docs/adr/`. See `docs/agents/domain.md`.

## Function names

A function's prefix says whether it touches a database:

- `load_`: reads a database and never writes (`load_snapshot`, `load_contents`).
- `create_`, `save_`, `log_`, `materialise_`: write to a database (`create_snapshot`, `save_run`, `log_test_look`).
- `build_`: pure. It makes new values from its inputs, with no I/O (`build_eval_set`, `build_training_decks`).

Don't use `get_` for new functions: elsewhere in this repo it means a database lookup (`get_deck_id`). Model methods keep the scikit-learn names (`fit`, `predict`). Merged pure functions such as `score` and `assign_split` keep their names.
