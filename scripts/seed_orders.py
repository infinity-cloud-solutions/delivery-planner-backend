#!/usr/bin/env python3
"""
seed_orders.py — Seed orders for each delivery zone of Guadalajara.

Driver assignment uses the real backend logic (DeliveryScheduler).
The origin (0,0 reference) is the Hidalgo & Alcalde intersection — Guadalajara's historic
downtown — at lat 20.6783825 / lon -103.348088.

Zone layout relative to origin
────────────────────────────────────────────────────────────────────
  Zone  Driver  Condition                 Neighborhoods
  ────  ──────  ────────────────────────  ──────────────────────────────────────
  NW      1     lat >=, lon <= origin     Zapopan, Andares, Providencia, Vallarta
  SW      2     lat  <, lon <= origin     Chapalita, López Mateos, Santa Anita
  NE      1     lat >=, lon >  origin     Huentitán, Mezquitán, Santuario
  SE      2     lat  <, lon >  origin     Tlaquepaque, Tonalá, Miravalle

Day-of-week shift rules (HiBerryApp orders) — mirrors DeliveryScheduler
────────────────────────────────────────────────────────────────────
  Mon / Wed / Fri  →  morning: West zones (NW, SW) | afternoon: East zones (NE, SE)
  Tue / Thu / Sat  →  morning: East zones (NE, SE) | afternoon: West zones (NW, SW)
  Sun              →  all zones valid for both shifts

Each driver covers exactly ONE zone per shift:
  Driver 1 → NW in one shift, NE in the other
  Driver 2 → SW in one shift, SE in the other
"""

import argparse
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "orders"))

from order_modules.dao.order_dao import OrderDAO
from order_modules.utils.delivery import DeliveryScheduler
from order_modules.utils.source import OrderSource
from order_modules.utils.status import OrderStatus

# ---------------------------------------------------------------------------
# City zones — real Guadalajara addresses.
# Every coordinate has been verified against the origin to confirm its sector.
# ---------------------------------------------------------------------------
ZONES = {
    "NW": {
        "label": "Noroeste — Zapopan / Andares / Providencia / Vallarta",
        "clients": [
            {
                "name": "BERRIES ANDARES",
                "phone": "3318001001",
                "address": "Blvd. Puerta de Hierro 4965, Andares, Zapopan, Jal. 45116",
                "lat": 20.7356,
                "lon": -103.4268,
            },
            {
                "name": "CAFÉ PROVIDENCIA",
                "phone": "3318001002",
                "address": "Av. Américas 1254, Providencia, Guadalajara, Jal. 44630",
                "lat": 20.6899,
                "lon": -103.3769,
            },
            {
                "name": "JUGO BAR VALLARTA",
                "phone": "3318001003",
                "address": "Av. Vallarta 2440, Arcos Vallarta, Guadalajara, Jal. 44130",
                "lat": 20.6881,
                "lon": -103.3954,
            },
            {
                "name": "NUTRICIÓN ZAPOPAN",
                "phone": "3318001004",
                "address": "Av. Patria 500, Zapopan, Jal. 45180",
                "lat": 20.7215,
                "lon": -103.4207,
            },
            {
                "name": "SMOOTHIES TEPEYAC",
                "phone": "3318001005",
                "address": "Av. Tepeyac 1024, Col. Tepeyac, Zapopan, Jal. 45050",
                "lat": 20.7073,
                "lon": -103.4059,
            },
        ],
    },
    "SW": {
        "label": "Suroeste — Chapalita / López Mateos / Santa Anita",
        "clients": [
            {
                "name": "PLAZA DEL SOL FRUITS",
                "phone": "3318002001",
                "address": "Av. López Mateos Sur 2375, Cd. del Sol, Guadalajara, Jal. 44950",
                "lat": 20.6594,
                "lon": -103.3853,
            },
            {
                "name": "ORGÁNICO CHAPALITA",
                "phone": "3318002002",
                "address": "Av. Chapalita 1050, Chapalita, Guadalajara, Jal. 44500",
                "lat": 20.6636,
                "lon": -103.4035,
            },
            {
                "name": "NUTRICIÓN MÉXICO",
                "phone": "3318002003",
                "address": "Av. México 2700, Ladrón de Guevara, Guadalajara, Jal. 44600",
                "lat": 20.6728,
                "lon": -103.3932,
            },
            {
                "name": "BERRIES SANTA ANITA",
                "phone": "3318002004",
                "address": "Carretera Guadalajara-Chapala Km 8.5, Santa Anita, Tlajomulco, Jal. 45645",
                "lat": 20.5873,
                "lon": -103.3935,
            },
            {
                "name": "FRESH MARKET SUR",
                "phone": "3318002005",
                "address": "Av. Niños Héroes 2855, Moderna, Guadalajara, Jal. 44140",
                "lat": 20.6660,
                "lon": -103.3820,
            },
        ],
    },
    "NE": {
        "label": "Noreste — Huentitán / Mezquitán / Santuario",
        "clients": [
            {
                "name": "CAFÉ INDEPENDENCIA NORTE",
                "phone": "3318003001",
                "address": "Calz. Independencia Norte 1221, Independencia Oriente, Guadalajara, Jal. 44340",
                "lat": 20.6928,
                "lon": -103.3322,
            },
            {
                "name": "HUENTITÁN BERRIES",
                "phone": "3318003002",
                "address": "Calle Gigantes 360, Huentitán El Bajo, Guadalajara, Jal. 44260",
                "lat": 20.7004,
                "lon": -103.3106,
            },
            {
                "name": "SMOOTHIES MEZQUITÁN",
                "phone": "3318003003",
                "address": "Av. Federalismo Norte 1360, Mezquitán, Guadalajara, Jal. 44270",
                "lat": 20.7012,
                "lon": -103.3398,
            },
            {
                "name": "NUTRICIÓN SANTUARIO",
                "phone": "3318003004",
                "address": "Calle Belisario Domínguez 1058, Santuario, Guadalajara, Jal. 44200",
                "lat": 20.6863,
                "lon": -103.3355,
            },
            {
                "name": "FRESH CIRCUNVALACIÓN",
                "phone": "3318003005",
                "address": "Av. Circunvalación Div. del Norte 876, Guadalajara, Jal. 44270",
                "lat": 20.7043,
                "lon": -103.3278,
            },
        ],
    },
    "SE": {
        "label": "Sureste — Tlaquepaque / Tonalá / Miravalle",
        "clients": [
            {
                "name": "BERRIES TLAQUEPAQUE",
                "phone": "3318004001",
                "address": "Av. Revolución 52, San Pedro Tlaquepaque, Jal. 45500",
                "lat": 20.6415,
                "lon": -103.3094,
            },
            {
                "name": "SMOOTHIES TONALÁ",
                "phone": "3318004002",
                "address": "Av. de Tonalá 100, Tonalá, Jal. 45400",
                "lat": 20.6234,
                "lon": -103.2350,
            },
            {
                "name": "CAFÉ TLAQUEPAQUE CENTRO",
                "phone": "3318004003",
                "address": "Calle Independencia 170, San Pedro Tlaquepaque, Jal. 45500",
                "lat": 20.6403,
                "lon": -103.3096,
            },
            {
                "name": "ORGÁNICO MIRAVALLE",
                "phone": "3318004004",
                "address": "Av. 8 de Julio 2222, El Retiro, Guadalajara, Jal. 44716",
                "lat": 20.6622,
                "lon": -103.3242,
            },
            {
                "name": "NUTRICIÓN REVOLUCIÓN",
                "phone": "3318004005",
                "address": "Av. Revolución 1780, Guadalajara, Jal. 44716",
                "lat": 20.6615,
                "lon": -103.3306,
            },
        ],
    },
}

WEST_ZONES = ["NW", "SW"]
EAST_ZONES = ["NE", "SE"]

PRODUCTS = [
    {"product": "BLUEBERRY BOLSA 2KG", "price": 200},
    {"product": "ZARZAMORA BOLSA 2KG", "price": 200},
    {"product": "FRAMBUESA BOLSA 2KG", "price": 240},
    {"product": "FRESA BOLSA 2KG", "price": 195},
    {"product": "MANGO BOLSA 2KG", "price": 160},
    {"product": "PIÑA BOLSA 2KG", "price": 180},
    {"product": "MIX BERRIES BOLSA 2KG", "price": 210},
]

SHIFTS = {
    "morning": {"time": "9 AM - 1 PM"},
    "afternoon": {"time": "1 PM - 5 PM"},
}

DISCOUNTS = ["0", "5", "10", "15"]
PAYMENT_METHODS = ["Tarjeta", "Efectivo"]


def get_zones_for_shift(day_of_week: int, shift: str) -> list:
    """Return zone keys whose clients will receive a valid (non-zero) driver
    for the given weekday and shift, following the HiBerryApp scheduling rules
    (mirroring DeliveryScheduler.assign_driver_for_delivery):

      Mon / Wed / Fri  (0, 2, 4): morning → West (NW, SW) | afternoon → East (NE, SE)
      Tue / Thu / Sat  (1, 3, 5): morning → East (NE, SE) | afternoon → West (NW, SW)
      Sun              (6):        all zones for both shifts (no hard restriction)

    Each driver covers exactly ONE zone per shift:
      Driver 1 → NW or NE   |   Driver 2 → SW or SE
    """
    if day_of_week == 6:  # Sunday — no hard restriction in scheduler
        return WEST_ZONES + EAST_ZONES
    if day_of_week in (0, 2, 4):  # Monday / Wednesday / Friday
        return WEST_ZONES if shift == "morning" else EAST_ZONES
    # Tuesday / Thursday / Saturday  (days 1, 3, 5)
    return EAST_ZONES if shift == "morning" else WEST_ZONES


def generate_order(client, delivery_date, shift, driver, created_by="seed@hiberry.mx"):
    num_products = random.randint(2, 5)
    cart_items = []
    for _ in range(num_products):
        product = random.choice(PRODUCTS)
        cart_items.append(
            {
                "product": product["product"],
                "price": product["price"],
                "quantity": random.randint(1, 5),
            }
        )

    discount = random.choice(DISCOUNTS)
    multiplier = {"0": 1.0, "5": 0.95, "10": 0.90, "15": 0.85}[discount]
    subtotal = sum(i["price"] * i["quantity"] for i in cart_items)
    total = subtotal * multiplier
    now = datetime.now(timezone(timedelta(hours=-6))).isoformat()

    return {
        "id": str(uuid4()),
        "delivery_date": delivery_date,
        "client_name": client["name"],
        "phone_number": client["phone"],
        "delivery_address": client["address"],
        "delivery_time": SHIFTS[shift]["time"],
        "cart_items": cart_items,
        "discount": discount,
        "total_amount": total,
        "payment_method": random.choice(PAYMENT_METHODS),
        "latitude": client["lat"],
        "longitude": client["lon"],
        "status": OrderStatus.CREATED.value,
        "source": OrderSource.HIBERRYAPP.value,
        "created_at": now,
        "created_by": created_by,
        "cooler": None,
        "notes": None,
        "errors": [],
        "delivery_sequence": None,
        "driver": driver,
    }


def seed_orders(num_orders=3, shift=None, delivery_date=None, as_saturday=False):
    dao = OrderDAO()
    scheduler = DeliveryScheduler()
    today = delivery_date or datetime.now(timezone(timedelta(hours=-6))).strftime(
        "%Y-%m-%d"
    )
    day_of_week = datetime.strptime(today, "%Y-%m-%d").weekday()
    day_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    # --as-saturday: use Saturday zone/shift rules regardless of the actual weekday.
    # DeliveryScheduler needs a real Saturday date string for its own weekday check,
    # so we find the most recent Saturday to pass to it, while delivery_date on each
    # record stays as today (the real delivery date).
    if as_saturday and day_of_week != 5:
        days_since_saturday = (day_of_week - 5) % 7 or 7
        last_saturday = (
            datetime.strptime(today, "%Y-%m-%d") - timedelta(days=days_since_saturday)
        ).strftime("%Y-%m-%d")
        effective_day = 5
        scheduler_date = last_saturday
        print(
            f"\nSeeding orders for {today} ({day_names[day_of_week]}) [simulating Saturday rules]"
        )
    else:
        effective_day = day_of_week
        scheduler_date = today
        print(f"\nSeeding orders for {today} ({day_names[day_of_week]})")

    print(
        f"Origin (downtown 0,0): lat=20.6783825, lon=-103.348088  (Hidalgo & Alcalde, Guadalajara)\n"
    )

    shifts = [shift] if shift else ["morning", "afternoon"]
    created = skipped = 0

    for shift_name in shifts:
        delivery_time = SHIFTS[shift_name]["time"]
        active_zones = get_zones_for_shift(effective_day, shift_name)

        print(
            f"── {shift_name.upper()} ({delivery_time})  active zones: {', '.join(active_zones)}"
        )

        for zone_key in active_zones:
            zone = ZONES[zone_key]
            clients = zone["clients"]
            picks = [clients[i % len(clients)] for i in range(num_orders)]

            for client in picks:
                driver = scheduler.assign_driver_for_delivery(
                    customer_location=(client["lat"], client["lon"]),
                    delivery_time=delivery_time,
                    order_date=scheduler_date,  # Saturday date so scheduler picks correct weekday
                    orders=[],  # fresh seed — well under capacity threshold
                    source=OrderSource.HIBERRYAPP,
                )

                if driver == 0:
                    print(
                        f"  ⚠  SKIP  [{zone_key}] {client['name']} — no driver available for this zone/shift/day"
                    )
                    skipped += 1
                    continue

                order = generate_order(client, today, shift_name, driver)
                result = dao.create_order(order)

                if result.get("status") == "success":
                    created += 1
                    print(f"  ✓  [{zone_key}] Driver {driver}  {client['name']}")
                else:
                    print(
                        f"  ✗  [{zone_key}] {client['name']} — {result.get('message')}"
                    )
                    skipped += 1

        print()

    print(f"Done. Created {created} orders  |  Skipped {skipped}")


def fix_null_drivers(delivery_date=None):
    """Find every order for *delivery_date* whose driver is null and assign the
    correct driver using the real backend DeliveryScheduler logic."""
    from decimal import Decimal

    def _decimal_to_native(obj):
        if isinstance(obj, list):
            return [_decimal_to_native(i) for i in obj]
        if isinstance(obj, dict):
            return {k: _decimal_to_native(v) for k, v in obj.items()}
        if isinstance(obj, Decimal):
            return int(obj) if obj == obj.to_integral_value() else float(obj)
        return obj

    dao = OrderDAO()
    scheduler = DeliveryScheduler()
    today = delivery_date or datetime.now(timezone(timedelta(hours=-6))).strftime(
        "%Y-%m-%d"
    )

    result = dao.fetch_orders("delivery_date", today)
    orders = result.get("payload", [])
    null_orders = [o for o in orders if not o.get("driver")]

    if not null_orders:
        print(f"No null-driver orders found for {today}")
        return

    print(f"Found {len(null_orders)} orders with driver=null for {today} — fixing...")
    fixed = failed = 0
    for o in null_orders:
        driver = scheduler.assign_driver_for_delivery(
            customer_location=(float(o["latitude"]), float(o["longitude"])),
            delivery_time=o["delivery_time"],
            order_date=today,
            orders=[],
            source=OrderSource.HIBERRYAPP,
        )
        if driver == 0:
            print(f"  ⚠  SKIP  {o['id']} — no valid driver for this zone/shift/day")
            failed += 1
            continue
        clean = _decimal_to_native(o)
        clean["driver"] = driver
        res = dao.update_order(clean)
        if res.get("status") == "success":
            fixed += 1
            print(f"  ✓  {o['id']}  →  Driver {driver}  ({o['delivery_time']})")
        else:
            print(f"  ✗  {o['id']}  update failed: {res.get('message')}")
            failed += 1

    print(f"\nDone. Fixed {fixed}  |  Skipped/failed {failed}")


def cleanup_orders():
    dao = OrderDAO()
    today = datetime.now(timezone(timedelta(hours=-6))).strftime("%Y-%m-%d")

    result = dao.fetch_orders("delivery_date", today)
    if result.get("status") == "success" and result.get("payload"):
        deleted = 0
        for order in result["payload"]:
            res = dao.delete_order(order["delivery_date"], order["id"])
            if res.get("status") == "success":
                deleted += 1
                print(f"✓ Deleted {order['id']}")
            else:
                print(f"✗ Failed to delete {order['id']}: {res.get('message')}")
        print(f"\n✓ Cleaned up {deleted} orders from {today}")
    else:
        print(f"No orders found for {today}")


def main():
    parser = argparse.ArgumentParser(
        description="Seed orders for each Guadalajara delivery zone using real backend driver logic."
    )
    parser.add_argument(
        "--orders",
        type=int,
        default=3,
        help="Orders per zone per active shift (default: 3)",
    )
    parser.add_argument(
        "--shift",
        choices=["morning", "afternoon"],
        help="Limit seeding to one shift only",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Delivery date in YYYY-MM-DD format (default: today in MX Central Time)",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete all orders for today instead of creating new ones",
    )
    parser.add_argument(
        "--fix-null-drivers",
        action="store_true",
        help="Assign the correct driver to every order that currently has driver=null",
    )
    parser.add_argument(
        "--as-saturday",
        action="store_true",
        help="Apply Saturday zone/shift rules regardless of today's actual weekday (useful for testing on Sundays)",
    )
    args = parser.parse_args()

    if args.cleanup:
        cleanup_orders()
    elif getattr(args, "fix_null_drivers", False):
        fix_null_drivers(args.date)
    else:
        seed_orders(
            args.orders, args.shift, args.date, getattr(args, "as_saturday", False)
        )


if __name__ == "__main__":
    main()
