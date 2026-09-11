import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

# Fixed UTC-6 offset for Mexico Central Standard Time, consistent with the rest of the codebase
MX_OFFSET = timedelta(hours=-6)

# Leading characters that Excel/Sheets interpret as the start of a formula
_CSV_FORMULA_PREFIXES = ("=", "+", "-", "@")


def _sanitize_csv_field(value: Any) -> Any:
    """Neutralize values that would be interpreted as formulas by spreadsheet software."""
    if isinstance(value, str) and value.startswith(_CSV_FORMULA_PREFIXES):
        return "'" + value
    return value


def get_report_period(
    today: datetime = None,
) -> Tuple[str, str, str, str]:
    """Return (created_month, start_date, end_date, period_label) for the current run.

    Runs on the 16th → report for the 1st till 15th of the current month.
    Runs on the 1st  → report for the 16th till EOM of the previous month.
    """
    if today is None:
        today = datetime.now(timezone(MX_OFFSET))

    day = today.day
    if day == 16:
        start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = today.replace(day=15, hour=0, minute=0, second=0, microsecond=0)
    elif day == 1:
        last_day_prev = today.replace(day=1) - timedelta(days=1)
        start = last_day_prev.replace(day=16, hour=0, minute=0, second=0, microsecond=0)
        end = last_day_prev.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError(f"Report is scheduled for day 1 or 16 only; got day {day}")

    created_month = start.strftime("%Y-%m")
    start_date = start.strftime("%Y-%m-%d")
    end_date = end.strftime("%Y-%m-%d")
    period_label = f"{start_date}_to_{end_date}"

    return created_month, start_date, end_date, period_label


def build_detail_csv(orders: List[Dict[str, Any]]) -> str:
    """One row per order: creation date, creator, client, phone, article count, items."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(
        [
            "Fecha de creación",
            "Creado por",
            "Cliente",
            "Teléfono",
            "Núm. artículos",
            "Artículos",
            "Repartidor",
        ]
    )

    for order in orders:
        cart_items = order.get("cart_items", [])
        num_articles = sum(int(item.get("quantity", 0)) for item in cart_items)
        items_desc = ", ".join(
            f"{int(item.get('quantity', 0))}x {item.get('product', '')}"
            for item in cart_items
        )
        writer.writerow(
            [
                order.get("created_date_mx", ""),
                _sanitize_csv_field(order.get("created_by", "")),
                _sanitize_csv_field(order.get("client_name", "")),
                _sanitize_csv_field(order.get("phone_number", "")),
                num_articles,
                _sanitize_csv_field(items_desc),
                order.get("driver", ""),
            ]
        )

    return output.getvalue()


def build_summary_csv(orders: List[Dict[str, Any]]) -> str:
    """Two-table summary: orders per creator, then total quantity per product."""
    user_counts: Dict[str, int] = {}
    product_totals: Dict[str, int] = {}

    for order in orders:
        user = order.get("created_by", "Desconocido")
        user_counts[user] = user_counts.get(user, 0) + 1

        for item in order.get("cart_items", []):
            product = item.get("product", "")
            qty = int(item.get("quantity", 0))
            if product:
                product_totals[product] = product_totals.get(product, 0) + qty

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Creado por", "Total de órdenes"])
    for user, count in sorted(user_counts.items(), key=lambda x: -x[1]):
        writer.writerow([_sanitize_csv_field(user), count])

    writer.writerow([])

    writer.writerow(["Producto", "Total vendido"])
    for product, total in sorted(product_totals.items(), key=lambda x: -x[1]):
        writer.writerow([_sanitize_csv_field(product), total])

    return output.getvalue()
