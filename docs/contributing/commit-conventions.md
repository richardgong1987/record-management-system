# Git Commit Message Conventions

The team follows the **European Commission Component Library** Git commit conventions: <https://ec.europa.eu/component-library/v1.15.0/eu/docs/conventions/git/>.

The CSCK541 brief asks every group to follow a documented commit-message standard. We adopted this one — please write every commit on this project according to the rules below. Consistent commit history makes the work easy to scan during peer assessment and grading.

## Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

- The **header** (`<type>(<scope>): <subject>`) is mandatory.
- The **body** and **footer** are optional, each separated from the previous section by a blank line.
- Wrap every line at **100 characters** maximum.

## Subject line

- Use the **imperative, present tense** — "add" not "added", "fix" not "fixed".
- **Do not capitalise** the first letter.
- **Do not end with a period.**
- Keep it short and descriptive.

A useful test: read it as *"If applied, this commit will __\<subject\>__."*

## Type

Use exactly one of:

| Type | Use for |
| --- | --- |
| `feat` | A new feature. |
| `fix` | A bug fix. |
| `docs` | Documentation only changes. |
| `style` | Non-semantic code changes (whitespace, formatting). |
| `refactor` | Code restructuring with no new feature and no bug fix. |
| `perf` | A change that improves performance. |
| `test` | Adding missing tests. |
| `chore` | Build process, tooling, or dependency changes. |

## Scope

Optional. Identifies the area of the project the change touches. For this project, prefer one of:

- `gui` — code under [src/gui/](../../src/gui/)
- `data` — code under [src/data/](../../src/data/)
- `record` — record store / serialisation in [src/record/](../../src/record/)
- `conf` — configuration in [src/conf/](../../src/conf/)
- `tests` — when the change is exclusively in [tests/](../../tests/)
- `docs` — when paired with `type: docs` to indicate which document area changed
- `build` — packaging, PyInstaller, requirements

If a commit spans several areas, omit the scope.

## Body (optional)

- Use **imperative, present tense** (same as the subject).
- Explain the **motivation** for the change and **contrast with previous behaviour** — the body answers *why*, not *what* (the diff already shows what).

## Footer (optional)

Use the footer for two things:

1. **Breaking changes** — start a line with `BREAKING CHANGE:` followed by a space, then a description of what breaks.
2. **Issue / Kanban references** — reference the Kanban card or GitHub issue this commit closes, e.g. `Closes #12`.

## Reverts

When reverting a previous commit, format the message as:

```
revert: <header of the commit being reverted>

This reverts commit <hash>.
```

Where `<hash>` is the SHA of the commit being reverted.

## Examples

### Good

```
feat(gui): add client record creation form
```

```
fix(data): preserve newlines when loading records on windows

The jsonlines reader was stripping CR characters because the file was
opened in text mode. Open with newline='' so on-disk content round-trips
intact across platforms.

Closes #14
```

```
docs(contributing): add commit message conventions
```

```
refactor(record): split jsonl reader and writer into separate modules
```

```
chore(build): pin pyinstaller to 6.6.0
```

### Avoid

| Bad | Why |
| --- | --- |
| `Fixed bug` | No type, past tense, capitalised, says nothing about what was fixed. |
| `feat(GUI): Added new form.` | Capitalised subject, past tense, trailing period. |
| `update stuff` | No type, vague subject. |
| `fix(data): fixed the thing where loading was broken on windows because the jsonl reader was opened in text mode and stripped carriage returns` | Subject too long — push the detail into the body. |
