# 03 — Modelo de Dados e Módulos

## 1. Objetivo
Definir o modelo de dados canônico do OV10, inspirado em portfolio accounting profissional.

## 2. Entidades centrais

## 2.1 Investor
Representa a pessoa titular.

Campos mínimos:
- investor_id
- investor_name
- tax_residency
- base_currency
- status

## 2.2 Portfolio
Agrupamento patrimonial do investidor.

Campos mínimos:
- portfolio_id
- investor_id
- portfolio_name
- objective
- base_currency
- active_flag

Exemplos:
- carteira pessoal BR
- carteira internacional
- carteira Noah

## 2.3 Book
Subdivisão operacional dentro da carteira.

Campos mínimos:
- book_id
- portfolio_id
- book_name
- strategy_type
- active_flag

Exemplos:
- buy and hold BR
- FIIs
- EUA growth
- cripto spot

## 2.4 Account
Conta/corretora ou origem custodial.

Campos mínimos:
- account_id
- book_id
- broker_name
- account_label
- country
- currency

## 2.5 Instrument
Cadastro canônico do ativo.

Campos mínimos:
- instrument_id
- ticker
- normalized_ticker
- instrument_type
- issuer_name
- country
- currency
- exchange
- isin_optional
- status

Tipos possíveis:
- stock_br
- fii
- etf_br
- stock_us
- etf_us
- reit
- crypto
- fixed_income
- treasury
- cash_equivalent

## 2.6 Transaction
Evento operacional primário.

Campos mínimos:
- transaction_id
- source_system
- source_file
- source_row_ref
- investor_id
- portfolio_id
- book_id
- account_id
- instrument_id
- trade_date
- settlement_date_optional
- transaction_type
- quantity
- unit_price
- gross_amount
- fees
- taxes
- net_amount
- currency
- notes

Tipos esperados:
- BUY
- SELL
- TRANSFER_IN
- TRANSFER_OUT
- CASH_IN
- CASH_OUT
- SUBSCRIPTION_BUY
- STAKING_IN
- STAKING_OUT
- AIRDROP_IN

## 2.7 CorporateAction
Evento societário/corporativo.

Campos mínimos:
- corporate_action_id
- instrument_id
- action_type
- effective_date
- announcement_date_optional
- ratio_from_optional
- ratio_to_optional
- cash_component_optional
- source_name
- source_reference
- confidence_level
- manual_override_flag
- comments

Tipos mínimos:
- SPLIT
- REVERSE_SPLIT
- BONUS
- SUBSCRIPTION_RIGHT
- SPIN_OFF
- MERGER
- TICKER_CHANGE
- AMORTIZATION

## 2.8 DividendEvent
Provento declarado.

Campos mínimos:
- dividend_event_id
- instrument_id
- dividend_type
- ex_date
- record_date_optional
- pay_date
- amount_per_unit
- currency
- source_name
- source_reference
- comments

Tipos:
- DIVIDEND
- JCP
- AMORTIZATION
- INCOME
- COUPON

## 2.9 DividendReceipt
Provento recebido/apropriado à carteira.

Campos mínimos:
- dividend_receipt_id
- dividend_event_id_optional
- investor_id
- portfolio_id
- book_id
- account_id
- instrument_id
- reference_position_date
- payable_quantity
- gross_amount
- withholding_tax_optional
- net_amount
- received_date
- source_name
- confidence_level

## 2.10 PositionSnapshot
Snapshot de posição calculada.

Campos mínimos:
- snapshot_date
- investor_id
- portfolio_id
- book_id
- account_id
- instrument_id
- quantity
- avg_cost_local
- avg_cost_base
- market_price
- market_value
- unrealized_pnl
- source_mode

## 2.11 TaxLot (opcional, mas recomendado)
Lote fiscal para cálculo preciso de custo e alienação.

Campos mínimos:
- tax_lot_id
- instrument_id
- acquisition_transaction_id
- acquisition_date
- quantity_open
- quantity_original
- unit_cost
- currency
- methodology

## 2.12 TaxResultMonthly
Resultado fiscal mensal.

Campos mínimos:
- tax_month
- investor_id
- portfolio_id_optional
- jurisdiction
- tax_bucket
- gross_proceeds
- cost_basis
- realized_gain
- exempt_gain
- taxable_gain
- carry_loss_used
- carry_loss_generated
- tax_due
- notes

## 3. Regras de modelagem

### 3.1 Tudo precisa ter origem rastreável
Toda linha deve guardar:
- sistema de origem;
- arquivo de origem;
- referência de linha quando possível.

### 3.2 Nada deve depender de texto livre para regra crítica
Usar enums, dicionários e tabelas de mapeamento.

### 3.3 Correção manual deve ser governada
Toda intervenção manual precisa ser identificável.

### 3.4 Fonte consolidada e fonte bruta devem coexistir
Exemplo:
- transações do Status Invest como entrada consolidada;
- notas de corretagem como entrada bruta.

## 4. Módulos de código recomendados

```text
ov10/
  config/
  ingestion/
    status_invest/
    broker_notes/
    cash/
    manual/
  normalization/
  reference/
    instruments/
    brokers/
    mappings/
  ledger/
  corporate_actions/
  dividends/
  positions/
  valuation/
  tax/
  reconciliation/
  reporting/
  tests/
```

## 5. Contratos de entrada e saída
Cada módulo deve ter contratos explícitos.

### exemplo
- `ingestion.status_invest.transactions` → DataFrame schema X
- `normalization.transactions.normalize_status_invest_transactions()` → canonical transaction schema
- `positions.compute_positions()` → canonical position snapshots

## 6. Recomendação crítica
Definir schemas formais com validação. Exemplos possíveis:
- pydantic
- pandera
- dataclasses + validators

A decisão é do Codex, mas a exigência é: **schema explícito**.
