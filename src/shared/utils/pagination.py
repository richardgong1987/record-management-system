from dataclasses import dataclass

DEFAULT_PAGE_SIZE = 15


@dataclass(frozen=True)
class Page:
    rows: list[dict]
    total_pages: int
    current_page: int


def paginate(
    rows: list[dict],
    current_page: int,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Page:
    if page_size <= 0:
        raise ValueError("page_size must be positive")
    total = len(rows)
    total_pages = max(1, (total + page_size - 1) // page_size)
    normalised = max(1, min(current_page, total_pages))
    start = (normalised - 1) * page_size
    return Page(
        rows=rows[start : start + page_size],
        total_pages=total_pages,
        current_page=normalised,
    )
