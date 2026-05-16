from dataclasses import FrozenInstanceError

import pytest

from shared.utils.pagination import DEFAULT_PAGE_SIZE, Page, paginate


def _rows(count: int) -> list[dict]:
    return [{"i": i} for i in range(count)]


def test_default_page_size_is_fifteen() -> None:
    assert DEFAULT_PAGE_SIZE == 15


def test_default_page_size_is_applied_when_not_passed() -> None:
    page = paginate(_rows(20), current_page=1)
    assert len(page.rows) == DEFAULT_PAGE_SIZE
    assert page.total_pages == 2  # ceil(20 / 15)


_PAGINATE_CASES = [
    # id                            total  size  req   page  total_pages  start  stop
    ("empty", (0, 15, 1, 1, 1, 0, 0)),
    ("single-row", (1, 15, 1, 1, 1, 0, 1)),
    ("rows-below-page-size", (5, 15, 1, 1, 1, 0, 5)),
    ("rows-equal-page-size", (15, 15, 1, 1, 1, 0, 15)),
    ("exact-multiple-2pp-page1", (30, 15, 1, 1, 2, 0, 15)),
    ("exact-multiple-2pp-page2", (30, 15, 2, 2, 2, 15, 30)),
    ("exact-multiple-3pp-page1", (45, 15, 1, 1, 3, 0, 15)),
    ("exact-multiple-3pp-page2", (45, 15, 2, 2, 3, 15, 30)),
    ("exact-multiple-3pp-page3", (45, 15, 3, 3, 3, 30, 45)),
    ("partial-16rows-page2", (16, 15, 2, 2, 2, 15, 16)),
    ("partial-23rows-page2", (23, 15, 2, 2, 2, 15, 23)),
    ("clamp-zero", (23, 15, 0, 1, 2, 0, 15)),
    ("clamp-negative", (23, 15, -7, 1, 2, 0, 15)),
    ("clamp-far-above", (23, 15, 99, 2, 2, 15, 23)),
    ("clamp-one-above", (23, 15, 3, 2, 2, 15, 23)),
    ("psize1-first", (3, 1, 1, 1, 3, 0, 1)),
    ("psize1-middle", (3, 1, 2, 2, 3, 1, 2)),
    ("psize1-last", (3, 1, 3, 3, 3, 2, 3)),
    ("psize1-clamp-above", (3, 1, 4, 3, 3, 2, 3)),
    ("psize-larger-page1", (10, 100, 1, 1, 1, 0, 10)),
    ("psize-larger-clamps", (10, 100, 7, 1, 1, 0, 10)),
]


@pytest.mark.parametrize(
    "total,page_size,requested,expected_page,expected_total_pages,start,stop",
    [case for _, case in _PAGINATE_CASES],
    ids=[name for name, _ in _PAGINATE_CASES],
)
def test_paginate(
    total: int,
    page_size: int,
    requested: int,
    expected_page: int,
    expected_total_pages: int,
    start: int,
    stop: int,
) -> None:
    rows = _rows(total)
    page = paginate(rows, current_page=requested, page_size=page_size)
    assert page.rows == rows[start:stop]
    assert page.current_page == expected_page
    assert page.total_pages == expected_total_pages


# ---------------------------------------------------------------------------
# Canonical empty Page object — checks dataclass equality, not just fields
# ---------------------------------------------------------------------------


def test_empty_dataset_yields_canonical_empty_page() -> None:
    assert paginate([], current_page=1) == Page(rows=[], total_pages=1, current_page=1)


# ---------------------------------------------------------------------------
# Invalid page sizes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("invalid_size", [0, -1, -5, -100])
def test_invalid_page_size_raises(invalid_size: int) -> None:
    with pytest.raises(ValueError, match="page_size must be positive"):
        paginate(_rows(3), current_page=1, page_size=invalid_size)


# ---------------------------------------------------------------------------
# Purity and immutability
# ---------------------------------------------------------------------------


def test_paginate_does_not_mutate_input_rows() -> None:
    rows = _rows(20)
    snapshot = list(rows)
    paginate(rows, current_page=2, page_size=5)
    assert rows == snapshot


def test_page_is_frozen() -> None:
    page = paginate(_rows(5), current_page=1)
    with pytest.raises(FrozenInstanceError):
        setattr(page, "current_page", 99)
