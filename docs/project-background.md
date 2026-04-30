# Project Background

A desktop record management application for a specialist travel agent. Manages **Client**, **Airline**, and **Flight** records through a graphical user interface, with persistent storage on the local file system.

This project is the group coursework for **CSCK541 (March 2026 B), Week 8**, University of Liverpool.

## Features

- Create, delete, update, search, and display records.
- Three record types with fixed schemas (see [Record schemas](#record-schemas)).
- Persistent storage as JSON Lines (`.jsonl`) — loaded on startup, saved on close.
- Unit tests per module.
- Packaged as a standalone executable with PyInstaller.

## Project layout

```
src/
├── main.py        # Application entry point
├── conf/          # Configuration loading
├── data/          # Data-access layer over the on-disk record store
├── gui/           # Desktop GUI
└── record/        # On-disk record store (record.jsonl)
tests/             # Unit tests (one module per src/ package)
docs/              # Project documentation
```

The directory structure follows the project skeleton provided by the module — preserve it.

## Record schemas

Field names are kept verbatim from the assignment brief.

### Client

| Field | Type |
| --- | --- |
| ID | int |
| Type | str |
| Name | str |
| Address Line 1 | str |
| Address Line 2 | str |
| Address Line 3 | str |
| City | str |
| State | str |
| Zip Code | str |
| Country | str |
| Phone Number | str |

### Airline

| Field | Type |
| --- | --- |
| ID | int |
| Type | str |
| Company Name | str |

### Flight

| Field | Type |
| --- | --- |
| Client_ID | int |
| Airline_ID | int |
| Date | datetime |
| Start City | str |
| End City | str |

`Type` is a record-type discriminator stored on the record itself.

## Storage

In memory, records are held as a list of dictionaries (`recordslist = [{}, {}, {}]`). On disk they are persisted as JSON Lines via the [`jsonlines`](https://jsonlines.readthedocs.io/) library — one record per line. The application checks for an existing store on startup and writes back to it on close.

## Getting started

Requires Python 3.x.

```bash
# 1. Clone
git clone https://github.com/richardgong1987/record-management-system.git
cd record-management-system

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python src/main.py
```

## Testing

Unit tests live under [tests/](../tests/), with one test module per `src/` package. Run all tests with:

```bash
python -m pytest
```

## Packaging

The deliverable is built with **PyInstaller 6.6.0** (pinned — do not upgrade without team agreement):

```bash
pip install pyinstaller==6.6.0
pyinstaller --onefile src/main.py
```

The resulting executable is in `dist/`.

## Team & roles

Each teammate holds one or more of the following roles:

- GUI / UX designer
- Programmer
- Project manager
- Tester

| Teammate | Role(s) |
| --- | --- |
| _TBD_ | _TBD_ |

## Submission

- Final artifact: `.zip` of the repository, uploaded to the VLE.
- Every teammate uploads an **identical** copy.
- Includes the 1000-word report and all meeting minutes.
- Deadline: **Monday, 25 May 2026, 23:59**.
