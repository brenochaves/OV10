from enum import StrEnum


class SourceSystem(StrEnum):
    STATUS_INVEST_XLSX = "status_invest_xlsx"


class TransactionType(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    BONUS = "BONUS"
    CONVERSION_IN = "CONVERSION_IN"
    CONVERSION_OUT = "CONVERSION_OUT"


class DividendType(StrEnum):
    DIVIDEND = "DIVIDEND"
    JCP = "JCP"
    INCOME = "INCOME"
    TAXABLE_INCOME = "TAXABLE_INCOME"


class CorporateActionType(StrEnum):
    INCORPORATION_TOTAL = "INCORPORATION_TOTAL"
    SIMPLE_CONVERSION = "SIMPLE_CONVERSION"
    UNKNOWN = "UNKNOWN"


class AccountType(StrEnum):
    BROKER = "broker"
    SYSTEM = "system"


class CashMovementType(StrEnum):
    TRADE_SETTLEMENT = "trade_settlement"
    DIVIDEND_RECEIPT = "dividend_receipt"
    CORPORATE_ACTION_CASH = "corporate_action_cash"


class InstrumentType(StrEnum):
    STOCK_BR = "stock_br"
    FII = "fii"
    BDR = "bdr"
    ETF_BR = "etf_br"
    STOCK_US = "stock_us"
    ETF_US = "etf_us"
    FUND_BR = "fund_br"
    TREASURY_BR = "treasury_br"
    CRYPTO = "crypto"
    UNKNOWN = "unknown"
