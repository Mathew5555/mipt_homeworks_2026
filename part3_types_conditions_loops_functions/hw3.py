import sys
from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

ONE = 1
TWO = 2
THREE = 3
TWELVE = 12
FEBRUARY = 2
LEAP_FEBRUARY_DAYS = 29
ZERO = float(0)

AMOUNT_KEY = "amount"
DATE_KEY = "date"
CATEGORY_KEY = "category"

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}

DAYS_IN_MONTH = {
    1: 31,
    2: 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31,
}

DateTuple = tuple[int, int, int]
Transaction = dict[str, Any]
StatsTuple = tuple[float, float, float, dict[str, float]]

financial_transactions_storage: list[Transaction] = []


def is_leap_year(year: int) -> bool:
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def get_days_in_month(month: int, year: int) -> int:
    if month == FEBRUARY and is_leap_year(year):
        return LEAP_FEBRUARY_DAYS
    return DAYS_IN_MONTH[month]


def valid_date_values(date: DateTuple) -> bool:
    day, month, year = date
    if year < 0:
        return False
    if not (ONE <= month <= TWELVE):
        return False
    return ONE <= day <= get_days_in_month(month, year)


def extract_date(line: str) -> DateTuple | None:
    parts = line.split("-")
    if len(parts) != THREE:
        return None
    if not all(part.isdigit() for part in parts):
        return None

    day, month, year = tuple(map(int, parts))
    parsed_date = (day, month, year)
    if not valid_date_values(parsed_date):
        return None
    return parsed_date


def parse_amount(line: str) -> float | None:
    line_dot = line.replace(",", ".")
    line_split = line_dot.split(".")
    if len(line_split) > TWO:
        return None
    if not all(el.lstrip("-").isdigit() for el in line_split):
        return None
    return float(line_dot)


def valid_category(category: str) -> bool:
    if "::" not in category:
        return False
    general, target = category.split("::")
    if general not in EXPENSE_CATEGORIES:
        return False
    return target in EXPENSE_CATEGORIES[general]


def not_after(date1: DateTuple, date2: DateTuple) -> bool:
    left = (date1[2], date1[1], date1[0])
    right = (date2[2], date2[1], date2[0])
    return left <= right


def same_month(date1: DateTuple, date2: DateTuple) -> bool:
    same_year = date1[2] == date2[2]
    same_month_number = date1[1] == date2[1]
    return same_year and same_month_number


def skip_transaction(transaction: Transaction, date: DateTuple) -> bool:
    if AMOUNT_KEY not in transaction or DATE_KEY not in transaction:
        return True
    return not not_after(transaction[DATE_KEY], date)


def apply_income(data: list[float], transaction: Transaction, date: DateTuple) -> None:
    amount = transaction[AMOUNT_KEY]
    data[0] += amount
    if same_month(transaction[DATE_KEY], date):
        data[1] += amount


def apply_cost(
    data: list[float],
    categories: dict[str, float],
    transaction: Transaction,
    date: DateTuple,
) -> None:
    amount = transaction[AMOUNT_KEY]
    data[0] -= amount
    if not same_month(transaction[DATE_KEY], date):
        return

    data[2] += amount
    general_cat = transaction[CATEGORY_KEY].split("::")[1]
    categories[general_cat] = categories.get(general_cat, 0) + amount


def collect_stats(date: DateTuple) -> StatsTuple:
    data = [ZERO, ZERO, ZERO]
    categories: dict[str, float] = {}

    for transaction in financial_transactions_storage:
        if skip_transaction(transaction, date):
            continue
        if CATEGORY_KEY in transaction:
            apply_cost(data, categories, transaction, date)
            continue
        apply_income(data, transaction, date)

    return data[0], data[1], data[2], categories


def beautiful_lines(category_totals: dict[str, float]) -> list[str]:
    lines: list[str] = []
    for index, category in enumerate(sorted(category_totals), ONE):
        value = f"{category_totals[category]:.2f}"
        lines.append(f"{index}. {category}: {value}")
    return lines


def month_summary(income: float, expenses: float) -> tuple[str, float]:
    difference = income - expenses
    if difference < 0:
        return "loss", abs(difference)
    return "profit", difference


def income_handler(amount: float, line: str) -> str:
    if amount <= ZERO:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    date = extract_date(line)
    if date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append({AMOUNT_KEY: amount, DATE_KEY: date})
    return OP_SUCCESS_MSG


def cost_handler(category_name: str, amount: float, line: str) -> str:
    if not valid_category(category_name):
        financial_transactions_storage.append({})
        return NOT_EXISTS_CATEGORY

    if amount <= ZERO:
        financial_transactions_storage.append({})
        return NONPOSITIVE_VALUE_MSG

    date = extract_date(line)
    if date is None:
        financial_transactions_storage.append({})
        return INCORRECT_DATE_MSG

    financial_transactions_storage.append({CATEGORY_KEY: category_name, AMOUNT_KEY: amount, DATE_KEY: date})
    return OP_SUCCESS_MSG


def cost_categories_handler() -> str:
    lines: list[str] = []
    for general_cat, targets in EXPENSE_CATEGORIES.items():
        lines.extend(f"{general_cat}::{target}" for target in targets)
    return "\n".join(lines)


def stats_handler(line_date: str) -> str:
    date = extract_date(line_date)
    if date is None:
        return INCORRECT_DATE_MSG

    stats = collect_stats(date)
    result_word, result_amount = month_summary(stats[1], stats[2])
    lines = [
        f"Your statistics as of {line_date}:",
        f"Total capital: {stats[0]:.2f} rubles",
        f"This month, the {result_word} amounted to {result_amount:.2f} rubles.",
        f"Income: {stats[1]:.2f} rubles",
        f"Expenses: {stats[2]:.2f} rubles",
        "",
        "Details (category: amount):",
    ]
    lines.extend(beautiful_lines(stats[3]))
    return "\n".join(lines)


def process_income(args: list[str]) -> str:
    if len(args) != TWO:
        return UNKNOWN_COMMAND_MSG

    amount = parse_amount(args[0])
    if amount is None:
        return UNKNOWN_COMMAND_MSG

    return income_handler(amount, args[1])


def process_cost(args: list[str]) -> str:
    if len(args) == ONE and args[0] == "categories":
        return cost_categories_handler()
    if len(args) != THREE:
        return UNKNOWN_COMMAND_MSG

    if not valid_category(args[0]):
        return f"{NOT_EXISTS_CATEGORY}\n{cost_categories_handler()}"

    amount = parse_amount(args[1])
    if amount is None:
        return UNKNOWN_COMMAND_MSG

    return cost_handler(args[0], amount, args[2])


def start_command(command: str) -> str:
    parts = command.split()
    if not parts:
        return UNKNOWN_COMMAND_MSG

    action = parts[0]
    args = parts[1:]
    if action == "income":
        return process_income(args)
    if action == "cost":
        return process_cost(args)
    if action == "stats" and len(args) == ONE:
        return stats_handler(args[0])
    return UNKNOWN_COMMAND_MSG


def main() -> None:
    for line in sys.stdin:
        command = line.strip()
        if command:
            print(start_command(command))


if __name__ == "__main__":
    main()
