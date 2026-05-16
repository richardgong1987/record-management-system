# Releasing

How to cut a release of the desktop app — pushed to a GitHub Release with `.app`/`.exe`/Linux bundles attached. The pipeline itself is described in [`docs/design/packaging-and-release.md`](../design/packaging-and-release.md); this page is the operational how-to.

## When to release

Cut a release when:

- A noticeable user-facing change has landed on `main` (new feature, visual change, bug fix the team wants packaged).
- Before a coursework milestone or demo so graders/teammates can download a current build.

Don't tag for every PR — tags create permanent GitHub Releases and shouldn't be churned.

## Versioning

We follow semver-flavoured tags: `vMAJOR.MINOR.PATCH`.

- `v0.1.0` → first usable build.
- `v0.1.1` → small fixes on top of `v0.1.0` (the pipeline fix shipped this way).
- `v0.2.0` → meaningful feature increment (e.g. once airline + flight tabs are fully implemented).
- `v1.0.0` → reserved for the final submission build.

Pre-release variants are allowed: `v0.2.0-rc1`, `v0.2.0-beta`, etc. — these still trigger the workflow and still create a GitHub Release (mark it as a pre-release manually in the GitHub UI if you want).

## Pre-release checklist

Run these on the branch you intend to release, before tagging:

```bash
black src/             # auto-format
pylint src/            # lint
pytest                 # full test suite
```

All three must be green. Also make sure:

- The change you want to ship is actually merged into the branch you're tagging (usually `main`).
- `README.md` and any design docs touched by the change reflect the new behaviour.
- `requirements.txt` is up to date — PyInstaller in CI installs whatever is pinned there, so a missing/stale dep will fail the build.

## Cutting a release

From your local checkout, on the branch you want to release (usually `main`):

```bash
git checkout main
git pull --ff-only
git tag -a vX.Y.Z -m "vX.Y.Z — short summary"
git push origin vX.Y.Z
```

That's it. The `git push origin vX.Y.Z` is the trigger — the workflow at [`.github/workflows/release.yml`](../../.github/workflows/release.yml) listens for `v*` tag pushes and does the rest.

## What happens after the push

A single workflow run starts:

1. **Three parallel build jobs** (`ubuntu-latest`, `windows-latest`, `macos-latest`):
   - Install Python 3.11 and `requirements.txt`.
   - Run `pyinstaller RecordManagementSystem.spec`.
   - Archive `dist/RecordManagementSystem` (or `.app` on macOS) into a `.zip` / `.tar.gz`.
   - Upload the archive as a workflow artifact.

2. **One `release` job** (only when triggered by a `v*` tag):
   - Downloads the three artifacts.
   - Publishes them to `https://github.com/<owner>/<repo>/releases/tag/<tag>` with auto-generated release notes.

Typical wall time: 2–4 minutes for the builds, ~30 s for the release job.

## Verify the release

```bash
gh run list --workflow=release.yml --limit 1   # check the latest run
gh release view vX.Y.Z                          # confirm the release + assets exist
```

Or open the Release in the browser and confirm all three assets are attached:

- `RecordManagementSystem-linux-x86_64.tar.gz`
- `RecordManagementSystem-macos.zip`
- `RecordManagementSystem-windows-x86_64.zip`

Optional smoke test: download one for your OS, unzip, run, click around for ten seconds, create a record, restart, confirm the record is still there (it's stored at `~/RecordManagementSystem/record.jsonl`, separate from the dev `src/data/record.jsonl`).

## Manual test build (no release published)

When you want to make sure the bundle still builds without cutting a real release — e.g. after touching `RecordManagementSystem.spec`, `src/conf/loader.py`, or anything that affects packaging — use the workflow's `workflow_dispatch` trigger.

### From the GitHub UI

1. Open the **Actions** tab → **Build & Release** in the left sidebar.
2. Click **Run workflow** in the top right.
3. Pick the branch (usually your feature branch) and click the green **Run workflow** button.

### From the CLI

```bash
gh workflow run release.yml --ref <branch-name>
gh run list --workflow=release.yml --limit 1     # find the run ID
gh run watch <run-id> --exit-status              # wait for it to finish
```

This runs the three builds and uploads the archives as **workflow artifacts** (downloadable from the run page) but **skips** the release job — no GitHub Release is created, nothing user-visible changes. Use this freely.

## If a build fails

```bash
gh run view <run-id> --log-failed | head -100    # see what broke
```

Common failures and what they mean:

- `ERROR: Spec file "RecordManagementSystem.spec" not found!` — the spec was excluded by `.gitignore`. The whitelist line `!RecordManagementSystem.spec` must stay.
- `ModuleNotFoundError: No module named 'X'` at runtime in the frozen bundle — PyInstaller missed a dynamic import. Add the missing module to `hiddenimports` in `RecordManagementSystem.spec`.
- `FileNotFoundError: ... config.json` at runtime — the file wasn't bundled. Add an entry to `datas` in the spec.
- Workflow runs but artifacts are 0 bytes — the package step's archive command may have run from the wrong directory; check the platform-specific `Package` step in `release.yml`.

If only one OS fails, the workflow still uploads the other two artifacts (`fail-fast: false`). You can fix the broken OS in a follow-up commit, then re-tag (use the next patch version — don't move an existing tag).

## Re-running vs re-tagging

If a build flaked (network blip, transient runner issue) and you want to retry without changing anything:

```bash
gh run rerun <run-id>
```

If the failure was a real bug, **don't** force-update the tag — create a new patch tag instead:

```bash
# fix the bug, commit, push
git tag -a v0.1.2 -m "v0.1.2 — <one-line fix summary>"
git push origin v0.1.2
```

A bumped tag keeps the broken release in history as a record and avoids the "different SHA, same tag" surprise for anyone who already pulled.

## Notes for end users (worth mentioning in release notes)

- **macOS**: the `.app` is unsigned. First launch will be blocked by Gatekeeper — right-click → Open and confirm. Or `xattr -dr com.apple.quarantine RecordManagementSystem.app`.
- **Windows**: the `.exe` is unsigned. SmartScreen will show "Windows protected your PC" — click **More info** → **Run anyway**.
- **Linux**: untarred folder is portable — run `RecordManagementSystem/RecordManagementSystem`. Requires glibc ≥ 2.39 (matches the Ubuntu runner used in CI).
- All platforms persist records to `~/RecordManagementSystem/record.jsonl`. This file is independent of the development `src/data/record.jsonl`.
