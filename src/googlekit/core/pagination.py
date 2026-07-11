"""Pagination helpers."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from googlekit.core.constants import DEFAULT_PAGE_SIZE

T = TypeVar("T")


@dataclass(slots=True)
class Page(Generic[T]):
    """One page of API results (items + optional ``next_page_token``).

    Use ``.items`` for this page, or ``files.iterate(...)`` / ``PageIterator`` to
    walk every page. ``has_more`` is True when another page token is present.
    """

    items: list[T]
    next_page_token: str | None = None
    raw: dict[str, object] = field(default_factory=dict)

    @property
    def has_more(self) -> bool:
        """True if ``next_page_token`` is set (another page is available)."""
        return bool(self.next_page_token)


class PageIterator(Generic[T]):
    """Lazy iterator over paginated Google API results.

    Iterating yields individual items. Call ``.pages()`` to yield full
    :class:`Page` objects instead.
    """

    def __init__(
        self,
        fetch_page: Callable[[str | None, int], Page[T]],
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
        page_token: str | None = None,
    ) -> None:
        self._fetch_page = fetch_page
        self._page_size = page_size
        self._page_token = page_token
        self._exhausted = False
        self._buffer: list[T] = []
        self._index = 0

    def __iter__(self) -> Iterator[T]:
        return self

    def __next__(self) -> T:
        while self._index >= len(self._buffer):
            if self._exhausted:
                raise StopIteration
            page = self._fetch_page(self._page_token, self._page_size)
            self._buffer = page.items
            self._index = 0
            self._page_token = page.next_page_token
            if not page.next_page_token:
                self._exhausted = True
            if not self._buffer and self._exhausted:
                raise StopIteration
        item = self._buffer[self._index]
        self._index += 1
        return item

    def pages(self) -> Iterator[Page[T]]:
        """Yield full pages instead of individual items."""
        token = self._page_token
        while True:
            page = self._fetch_page(token, self._page_size)
            yield page
            if not page.next_page_token:
                break
            token = page.next_page_token
