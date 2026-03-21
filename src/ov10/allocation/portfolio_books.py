from __future__ import annotations

from fnmatch import fnmatchcase

from ov10.config import PortfolioBookConfig
from ov10.domain.enums import InstrumentType
from ov10.domain.models import (
    AccountPortfolioAssignment,
    AccountPositionSnapshot,
    AccountRegistryEntry,
    BookPositionSnapshot,
)


def assign_accounts_to_portfolios(
    accounts: list[AccountRegistryEntry] | tuple[AccountRegistryEntry, ...],
    config: PortfolioBookConfig,
    *,
    batch_id: str,
) -> list[AccountPortfolioAssignment]:
    assignments: list[AccountPortfolioAssignment] = []
    for account in sorted(accounts, key=lambda item: item.account_id):
        portfolio_id = _resolve_portfolio_id(account, config)
        assignments.append(
            AccountPortfolioAssignment(
                batch_id=batch_id,
                account_id=account.account_id,
                portfolio_id=portfolio_id,
            )
        )
    return assignments


def assign_account_positions_to_books(
    account_positions: list[AccountPositionSnapshot] | tuple[AccountPositionSnapshot, ...],
    account_assignments: list[AccountPortfolioAssignment] | tuple[AccountPortfolioAssignment, ...],
    config: PortfolioBookConfig,
) -> list[BookPositionSnapshot]:
    portfolio_by_account_id = {item.account_id: item.portfolio_id for item in account_assignments}
    books_by_portfolio: dict[str, list[tuple[tuple[InstrumentType, ...], str]]] = {}
    for item in sorted(
        (book for book in config.books if book.is_active),
        key=lambda book: (book.portfolio_id, book.sort_order, book.book_id),
    ):
        books_by_portfolio.setdefault(item.portfolio_id, []).append(
            (item.instrument_types, item.book_id)
        )

    book_positions: list[BookPositionSnapshot] = []
    for item in account_positions:
        portfolio_id = portfolio_by_account_id[item.account_id]
        book_id = _resolve_book_id(
            instrument_type=item.instrument_type,
            portfolio_id=portfolio_id,
            books_by_portfolio=books_by_portfolio,
        )
        book_positions.append(
            BookPositionSnapshot(
                snapshot_date=item.snapshot_date,
                portfolio_id=portfolio_id,
                book_id=book_id,
                account_id=item.account_id,
                instrument_code=item.instrument_code,
                instrument_type=item.instrument_type,
                quantity=item.quantity,
                total_cost=item.total_cost,
                avg_cost=item.avg_cost,
                currency=item.currency,
                engine_version=item.engine_version,
            )
        )
    return book_positions


def _resolve_portfolio_id(account: AccountRegistryEntry, config: PortfolioBookConfig) -> str:
    for item in config.account_assignments:
        if any(
            fnmatchcase(account.account_name, pattern) or fnmatchcase(account.account_id, pattern)
            for pattern in item.account_patterns
        ):
            return item.portfolio_id
    return config.default_portfolio_id


def _resolve_book_id(
    *,
    instrument_type: InstrumentType,
    portfolio_id: str,
    books_by_portfolio: dict[str, list[tuple[tuple[InstrumentType, ...], str]]],
) -> str:
    candidates = books_by_portfolio[portfolio_id]
    for instrument_types, book_id in candidates:
        if instrument_type in instrument_types:
            return book_id
    for instrument_types, book_id in candidates:
        if InstrumentType.UNKNOWN in instrument_types:
            return book_id
    raise ValueError(
        f"No book rule configured for portfolio={portfolio_id} instrument_type={instrument_type}"
    )
