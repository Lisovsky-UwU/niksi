"""Bank loans: payment dates, how a payment splits into interest and principal, and when
the loan will be paid off.

The model is deliberately simple, close to how a bank statement reads: interest for a
month is the remaining balance times the yearly rate / 12, the rest of a regular payment
goes to the principal, and an early repayment goes to the principal entirely. It is a
forecast, not the bank's schedule; the balance can be corrected to the bank's figure.
"""

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
# Long enough for any mortgage; a payment that barely covers interest gives no forecast.
MAX_MONTHS = 600


def payment_date_in(year: int, month: int, payment_day: int) -> date:
    """The payment day in a given month; the 31st falls on the last day of shorter months."""
    return date(year, month, min(payment_day, calendar.monthrange(year, month)[1]))


def _shift(year: int, month: int, months: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + months
    return index // 12, index % 12 + 1


def nth_payment_date(start_date: date, payment_day: int, n: int) -> date:
    """The n-th payment date (1-based), counting from the first one after start_date.

    The next payment is the one after however many regular payments were made, so paying a
    few days early or late does not confuse which payment is due.
    """
    year, month = start_date.year, start_date.month
    if payment_date_in(year, month, payment_day) <= start_date:
        year, month = _shift(year, month, 1)
    year, month = _shift(year, month, n - 1)
    return payment_date_in(year, month, payment_day)


def months_after(day: date, payment_day: int, months: int) -> date:
    year, month = _shift(day.year, day.month, months)
    return payment_date_in(year, month, payment_day)


def monthly_interest(balance: Decimal, rate_percent: Decimal) -> Decimal:
    return (balance * rate_percent / 1200).quantize(CENT, rounding=ROUND_HALF_UP)


def split_regular(balance: Decimal, rate_percent: Decimal, amount: Decimal) -> tuple[Decimal, Decimal]:
    """(interest, principal) of a regular payment. A payment smaller than the interest
    goes to interest entirely."""
    interest = min(monthly_interest(balance, rate_percent), amount)
    return interest, amount - interest


def final_payment(balance: Decimal, rate_percent: Decimal, monthly_payment: Decimal) -> Decimal:
    """The regular payment due now: the usual amount, or less when it is the last one."""
    return min(monthly_payment, balance + monthly_interest(balance, rate_percent))


@dataclass(frozen=True)
class Forecast:
    payments_left: int
    interest_left: Decimal


def forecast(balance: Decimal, rate_percent: Decimal, monthly_payment: Decimal) -> Forecast | None:
    """How many regular payments are left and how much of them is interest.

    None when the payment does not even cover the interest, so the debt never shrinks.
    """
    if balance <= 0:
        return Forecast(payments_left=0, interest_left=Decimal(0))
    if monthly_payment <= monthly_interest(balance, rate_percent):
        return None
    payments = 0
    interest_total = Decimal(0)
    while balance > 0 and payments < MAX_MONTHS:
        interest, principal = split_regular(balance, rate_percent, final_payment(balance, rate_percent, monthly_payment))
        interest_total += interest
        balance -= principal
        payments += 1
    if balance > 0:
        return None
    return Forecast(payments_left=payments, interest_left=interest_total)
