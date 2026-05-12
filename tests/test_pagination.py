import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gui.record_list.pagination import (  # noqa: E402
    DEFAULT_PAGE_SIZE,
    Page,
    paginate,
)


def _rows(count: int) -> list[dict]:
    return [{"i": i} for i in range(count)]


def test_default_page_size_is_ten() -> None:
    assert DEFAULT_PAGE_SIZE == 10


def test_empty_dataset_yields_one_empty_page() -> None:
    page = paginate([], current_page=1)
    assert page == Page(rows=[], total_pages=1, current_page=1)


def test_exact_multiple_first_page() -> None:
    page = paginate(_rows(20), current_page=1)
    assert page.rows == _rows(20)[:10]
    assert page.total_pages == 2
    assert page.current_page == 1


def test_exact_multiple_last_page() -> None:
    page = paginate(_rows(20), current_page=2)
    assert page.rows == _rows(20)[10:]
    assert page.total_pages == 2
    assert page.current_page == 2


def test_partial_last_page() -> None:
    page = paginate(_rows(23), current_page=3)
    assert page.rows == _rows(23)[20:]
    assert len(page.rows) == 3
    assert page.total_pages == 3
    assert page.current_page == 3


def test_single_page_dataset() -> None:
    page = paginate(_rows(5), current_page=1)
    assert page.rows == _rows(5)
    assert page.total_pages == 1
    assert page.current_page == 1


def test_clamp_below_one() -> None:
    page = paginate(_rows(23), current_page=0)
    assert page.current_page == 1
    assert page.rows == _rows(23)[:10]


def test_clamp_above_total() -> None:
    page = paginate(_rows(23), current_page=99)
    assert page.current_page == 3
    assert page.rows == _rows(23)[20:]


def test_negative_current_page_clamps_to_one() -> None:
    page = paginate(_rows(5), current_page=-7)
    assert page.current_page == 1


def test_custom_page_size_one() -> None:
    page = paginate(_rows(3), current_page=2, page_size=1)
    assert page.rows == [{"i": 1}]
    assert page.total_pages == 3
    assert page.current_page == 2


def test_zero_page_size_raises() -> None:
    with pytest.raises(ValueError):
        paginate(_rows(3), current_page=1, page_size=0)


def test_negative_page_size_raises() -> None:
    with pytest.raises(ValueError):
        paginate(_rows(3), current_page=1, page_size=-5)
