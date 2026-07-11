"""Pagination laziness tests."""

from __future__ import annotations

from googlekit.core.pagination import Page, PageIterator


def test_page_has_more() -> None:
    assert Page(items=[1], next_page_token="t").has_more is True
    assert Page(items=[1], next_page_token=None).has_more is False


def test_page_iterator_is_lazy() -> None:
    fetches: list[str | None] = []

    def fetch(token: str | None, page_size: int) -> Page[int]:
        fetches.append(token)
        if token is None:
            return Page(items=[1, 2], next_page_token="p2")
        if token == "p2":
            return Page(items=[3], next_page_token=None)
        raise AssertionError(f"unexpected token {token!r}")

    it = PageIterator(fetch, page_size=2)
    assert fetches == []  # no eager fetch

    assert next(it) == 1
    assert fetches == [None]
    assert next(it) == 2
    assert fetches == [None]  # still on first page
    assert next(it) == 3
    assert fetches == [None, "p2"]

    remaining = list(it)
    assert remaining == []
    assert fetches == [None, "p2"]


def test_page_iterator_pages() -> None:
    def fetch(token: str | None, page_size: int) -> Page[str]:
        if token is None:
            return Page(items=["a"], next_page_token="n")
        return Page(items=["b"], next_page_token=None)

    pages = list(PageIterator(fetch).pages())
    assert len(pages) == 2
    assert pages[0].items == ["a"]
    assert pages[1].items == ["b"]


def test_empty_first_page() -> None:
    def fetch(token: str | None, page_size: int) -> Page[int]:
        return Page(items=[], next_page_token=None)

    assert list(PageIterator(fetch)) == []
