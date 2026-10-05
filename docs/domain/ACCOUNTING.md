# Accounting

Portfolio accounting is canonical and uses `Decimal` for cash, price, quantity, fees, cost basis, exposure, and P&L. Fills update cash and average-cost position lots atomically; sells cannot exceed available owned quantity. Equity equals cash plus executable marked position value. Every order, fill, and resulting state transition is persisted for audit.

