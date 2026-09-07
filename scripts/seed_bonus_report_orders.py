"""
Seeds the dev Orders table with test combinations for the bonus report feature.

Targets the period the *next real* EventBridge run will report on:
Sept 16 fires the "16th" schedule, which reports created_month=2026-09,
date range 2026-09-01..2026-09-15 (see bonus_report/bonus_report_modules/report_generator.py).

Usage:
    python scripts/seed_bonus_report_orders.py --profile default
    python scripts/seed_bonus_report_orders.py --profile default --clear-first
"""

import argparse
import json
import uuid
from datetime import timedelta, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr

MX_OFFSET = timezone(timedelta(hours=-6))
SHOPIFY_SOURCE = 0
MANUAL_SOURCE = 1

CREATED_MONTH = "2026-09"
PERIOD_START = "2026-09-01"
PERIOD_END = "2026-09-15"


def to_decimal(item: dict) -> dict:
    return json.loads(json.dumps(item), parse_float=Decimal)


def make_order(
    *,
    day: str,
    created_by: str,
    cart_items: list,
    source: int = MANUAL_SOURCE,
    client_name: str = "Cliente de Prueba",
    label: str = "",
) -> dict:
    created_at = f"{day}T10:00:00.000000{('-06:00')}"
    total = sum(i["price"] * i["quantity"] for i in cart_items)
    order = {
        "delivery_date": day,
        "id": str(uuid.uuid4()),
        "cart_items": cart_items,
        "client_name": client_name,
        "cooler": None,
        "delivery_address": "Aurelio Ortega 2699-A, Zapopan, Jalisco",
        "delivery_sequence": None,
        "delivery_time": "9 AM - 1 PM",
        "discount": "0",
        "driver": 1,
        "errors": [],
        "latitude": 20.721829333659,
        "longitude": -103.372328264595,
        "notes": f"seed:{label}" if label else None,
        "payment_method": "Tarjeta",
        "phone_number": "3312721827",
        "source": source,
        "status": "Creada",
        "total_amount": total,
        "updated_at": created_at,
        "updated_by": created_by,
        "created_by": created_by,
        "created_at": created_at,
        "created_month": day[:7],
        "created_date_mx": day,
    }
    return to_decimal(order)


def build_test_orders() -> list:
    orders = []

    # --- In-range, should appear in the report (5 orders, 2 creators, 3 products) ---
    orders.append(
        make_order(
            day="2026-09-01",
            created_by="marko.burgos@gmail.com",
            cart_items=[{"product": "Manzana 2 prueba", "price": 200, "quantity": 2}],
            label="in-range-1",
        )
    )
    orders.append(
        make_order(
            day="2026-09-03",
            created_by="marko.burgos@gmail.com",
            cart_items=[
                {"product": "Pera Fuji", "price": 150, "quantity": 1},
                {"product": "Naranja Valencia", "price": 80, "quantity": 3},
            ],
            label="in-range-2",
        )
    )
    orders.append(
        make_order(
            day="2026-09-05",
            created_by="evelyn@hiberry.mx",
            cart_items=[{"product": "Manzana 2 prueba", "price": 200, "quantity": 1}],
            label="in-range-3",
        )
    )
    orders.append(
        make_order(
            day="2026-09-09",
            created_by="marko.burgos@gmail.com",
            cart_items=[{"product": "Pera Fuji", "price": 150, "quantity": 2}],
            label="in-range-4",
        )
    )
    orders.append(
        make_order(
            day="2026-09-15",
            created_by="evelyn@hiberry.mx",
            cart_items=[{"product": "Naranja Valencia", "price": 80, "quantity": 5}],
            label="in-range-5-boundary-end",
        )
    )

    # --- Negative controls: must NOT appear in the report ---

    # Shopify-sourced order, in-range date -> excluded by the source filter
    orders.append(
        make_order(
            day="2026-09-07",
            created_by="shopify-integration",
            cart_items=[{"product": "Manzana 2 prueba", "price": 200, "quantity": 10}],
            source=SHOPIFY_SOURCE,
            label="exclude-shopify-source",
        )
    )

    # Different created_month entirely (Aug 31) -> excluded at the GSI partition level
    orders.append(
        make_order(
            day="2026-08-31",
            created_by="marko.burgos@gmail.com",
            cart_items=[{"product": "Manzana 2 prueba", "price": 200, "quantity": 1}],
            label="exclude-previous-month",
        )
    )

    # Same month, but second half of September (day 16) -> excluded by the date filter
    orders.append(
        make_order(
            day="2026-09-16",
            created_by="marko.burgos@gmail.com",
            cart_items=[{"product": "Manzana 2 prueba", "price": 200, "quantity": 1}],
            label="exclude-second-half",
        )
    )

    return orders


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="default")
    parser.add_argument("--table", default="Orders")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument(
        "--clear-first",
        action="store_true",
        help="Delete previously seeded rows (notes starting with 'seed:') before inserting new ones",
    )
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    table = session.resource("dynamodb").Table(args.table)

    if args.clear_first:
        scan = table.scan(FilterExpression=Attr("notes").begins_with("seed:"))
        with table.batch_writer() as batch:
            for item in scan.get("Items", []):
                batch.delete_item(
                    Key={"delivery_date": item["delivery_date"], "id": item["id"]}
                )
                print(
                    f"Deleted previously seeded order {item['id']} ({item.get('notes')})"
                )

    orders = build_test_orders()
    with table.batch_writer() as batch:
        for order in orders:
            batch.put_item(Item=order)
            print(
                f"Inserted {order['notes']}: {order['created_by']} on {order['created_date_mx']}"
            )

    print(
        f"\nSeeded {len(orders)} orders into '{args.table}' (profile={args.profile})."
    )
    print(
        f"Report period under test: created_month={CREATED_MONTH}, {PERIOD_START} -> {PERIOD_END}"
    )
    print("\nExpected report results:")
    print("  order_count = 5")
    print("  Creado por:  marko.burgos@gmail.com = 3, evelyn@hiberry.mx = 2")
    print("  Producto:    Manzana 2 prueba = 3, Pera Fuji = 3, Naranja Valencia = 8")


if __name__ == "__main__":
    main()
