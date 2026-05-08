# Git Commit Message Conventions

The team follows the **PyInstaller** project's commit message conventions: <https://pyinstaller.org/en/stable/development/commit-messages.html>.

The CSCK541 brief asks every group to follow a documented commit-message standard. We adopted PyInstaller's because we already pin PyInstaller for packaging, the convention is well-defined, and a consistent commit history makes the work easy to scan during peer assessment and grading.

> Please write **every** commit on this project according to the rules below.

## Format

```
<subsystem>: <Subject>.

<body — optional, wrapped at 72 characters>

<footer — optional>
```

- The **header** (`<subsystem>: <Subject>.`) is mandatory.
- The **body** and **footer** are optional, each separated from the previous section by a blank line.

## Subject line

- Aim for **≤ 50 characters**, hard limit **72 characters**.
- Use **present tense** — "Add" not "Added", "Fix" not "Fixed".
- **Capitalise** the first word after the colon (e.g. `gui: Add client form.`).
- **End with a period.**
- Prefix with a subsystem identifier (see next section), followed by `: ` (colon + space).

A useful test: read the description as *"This commit will __\<subject\>__."*

## Subsystem prefixes

Use one of the following — they correspond to areas of the project:

| Prefix | Use for |
| --- | --- |
| `gui` | Code under [src/gui/](../../src/gui/) |
| `data` | Code under [src/data/](../../src/data/) |
| `record` | Record store / serialisation in [src/record/](../../src/record/) |
| `conf` | Configuration in [src/conf/](../../src/conf/) |
| `tests` | When the change is exclusively in [tests/](../../tests/) |
| `docs` | Documentation under [docs/](../../docs/) or `README.md` |
| `build` | Packaging, PyInstaller, `requirements.txt`, `pyproject.toml` |
| `meta` | Repo housekeeping — `.gitignore`, GitHub workflows, issue templates |

If a single commit genuinely spans several subsystems, pick the dominant one and explain the cross-cutting nature in the body.

## Body (optional)

- Separate from the subject by a **blank line**.
- Wrap each line at **72 characters** (do not exceed 80).
- Use **present tense** (same as the subject).
- Explain the **motivation** for the change and **contrast with previous behaviour** — the body answers *why*, not *what* (the diff already shows what).
- For bug fixes, reference the Issue or Kanban card (e.g. `Closes #14`).
- Bullet points are fine — use `-` or `*` with hanging indents.
- Do **not** start a body line with `#` (Git treats it as a comment).

## Footer (optional)

Use the footer to:

- Reference closed Issues, e.g. `Closes #12`.
- Note significant side effects, dependency bumps, or behaviour changes that future readers should not miss.

## General rules

- **One commit, one logical unit.** Do not bundle unrelated changes into one commit.
- **Do not mix reformatting with functional changes** — submit pure-style and functional changes as separate commits.
- **No extraneous edits** — avoid unrelated whitespace fixes or typo corrections in files you weren't otherwise touching.
- Follow **PEP 8** for any code changes referenced in the commit.
- Use `git rebase -i` to tidy up your local commits before opening a Pull Request — small, focused commits are much easier to review.

## Examples

### Good

```
gui: Add client record creation form.
```

```
data: Preserve newlines when loading records on Windows.

The jsonlines reader was stripping CR characters because the file was
opened in text mode. Open with newline='' so on-disk content
round-trips intact across platforms.

Closes #14
```

```
docs: Add commit message conventions.
```

```
record: Split jsonl reader and writer into separate modules.
```

```
build: Pin pyinstaller to 6.6.0.
```

```
tests: Add unit tests for client record validation.
```

### Avoid

| Bad | Why |
| --- | --- |
| `Fixed bug` | No subsystem prefix, past tense, no period, says nothing about what was fixed. |
| `gui: added new form.` | Lower-case first word after the colon, past tense. |
| `gui: Add new form` | Missing trailing period. |
| `update stuff` | No prefix, no period, vague subject. |
| `gui: Implement the entire client record management form including all validation and persistence work.` | Subject far too long — push detail into the body. |
| `gui: Add form and fix unrelated typo in README.` | Mixes two unrelated changes — split into two commits. |
