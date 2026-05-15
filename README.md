# Record Management System

A desktop record management application for a specialist travel agent — group coursework for **CSCK541 (March 2026 B), Week 8**, University of Liverpool.

## Project links

- Repository: <https://github.com/richardgong1987/record-management-system>
- Kanban board: <https://github.com/users/richardgong1987/projects/1>

## Quick start

```bash
pip install -r requirements.txt
python src/main.py
```

For full setup, testing, and packaging instructions, see the [Project background → Getting started](docs/project-background.md#getting-started).

## Code style — run before pushing

Every commit you push runs through CI ([`.github/workflows/lint.yml`](.github/workflows/lint.yml)), which fails the build if either tool reports a problem. To save round-trips, run them locally first:

```bash
black src/         # format the code in place
pylint src/        # check it against our coding standards
```

Both read their config from [`pyproject.toml`](pyproject.toml). The pylint limits there mirror the hard rules we agreed on: ≤ 300 lines per file, ≤ 30 statements per function, ≤ 3 parameters, ≤ 3 levels of nesting. Please don't push code that pylint flags — fix it, or open a discussion on the relevant issue if you think a rule should be relaxed.

## Tests — run before pushing

A second workflow ([`.github/workflows/test.yml`](.github/workflows/test.yml)) runs `pytest` on every push and every pull request. A failing test blocks the merge, so run the suite locally before pushing:

```bash
pytest
```

Test configuration (discovery paths and `src/` on the import path) lives in [`pyproject.toml`](pyproject.toml) under `[tool.pytest.ini_options]`. The suite is split by category: unit tests live under [`tests/unit/`](tests/unit/) (mirroring `src/`), with `tests/integration/` and `tests/e2e/` reserved for the future integration and end-to-end suites. New modules need their own unit tests under `tests/unit/<area>/` — the assignment brief requires unit tests for each module. For how the team writes those tests (parametrize-first, naming, fixtures), see the [Unit testing standards](docs/contributing/testing-standards.md).

## Documentation

This README is an index. The documents below live under [docs/](docs/).

### About the project

- [Project background](docs/project-background.md) — purpose, features, record schemas, project layout, deliverables, and deadline.

### Contributing (developer onboarding)

- [Joining the project](docs/contributing/joining-the-project.md) — how a new classmate is added to the GitHub repository and Kanban board.
- [Git commit conventions](docs/contributing/commit-conventions.md) — commit message format the team follows for every commit.
- [GUI walkthrough](docs/contributing/gui-walkthrough.md) — a tour through `src/gui/` for anyone picking up the code: what each folder does, how a click flows through the app, and where to look when you want to change something.
- [Unit testing standards](docs/contributing/testing-standards.md) — how to write tests for this project: default to `@pytest.mark.parametrize`, house style, repeating patterns, and a pre-PR checklist.
- _Planned:_ Coding standards

### Design

- [GUI layout](docs/design/gui-layout.md) — formal design for the application shell: tabs, forms, record list, status bar, signal flow.
- [Create record](docs/design/create-record.md) — design and tour for the create-record flow: form click → validation → atomic JSONL write.
- [Update record](docs/design/update-record.md) — design and tour for the update-record flow: row click → form populate → validate → in-place replace → atomic write.
- [Delete record](docs/design/delete-record.md) — design and tour for the delete-record flow: row click → Delete button → confirm dialog → atomic write of the survivor list.
- [Clear all records](docs/design/clear-all-records.md) — design and tour for the Clear button: per-tab bulk delete of every record of the active type, with confirmation.
- _Planned:_ Search & display records
- _Planned:_ Architecture overview
- _Planned:_ Directory structure explainer

### Report

- _Planned:_ 1000-word report and supporting materials.
