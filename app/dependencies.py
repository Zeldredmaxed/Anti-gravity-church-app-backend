"""Shared dependencies: pagination, common query params."""

from fastapi import Query
from typing import Optional


class PaginationParams:
    """Common pagination parameters."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(25, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page


class DateRangeParams:
    """Common date range filter."""

    def __init__(
        self,
        start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    ):
        self.start_date = start_date
        self.end_date = end_date
