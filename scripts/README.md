# Database Seeding Scripts

## seed_orders.py

Seeds the Orders DynamoDB table with realistic data for each delivery zone of Guadalajara.
Driver assignment uses the **real backend logic** (`DeliveryScheduler`) — driver is always
populated and varies by zone, shift, and day of the week.

### City zones

The origin (0,0) is the **Hidalgo & Alcalde intersection** in Guadalajara's historic downtown
(`lat 20.6783825 / lon -103.348088`). Four zones radiate from that point:

| Zone | Driver | Direction        | Neighborhoods                              |
|------|--------|------------------|--------------------------------------------|
| NW   | 1      | lat ≥, lon ≤ 0   | Zapopan, Andares, Providencia, Vallarta    |
| SW   | 2      | lat <, lon ≤ 0   | Chapalita, López Mateos, Santa Anita       |
| NE   | 1      | lat ≥, lon > 0   | Huentitán, Mezquitán, Santuario            |
| SE   | 2      | lat <, lon > 0   | Tlaquepaque, Tonalá, Miravalle             |

Day-of-week rules activate the correct zones per shift automatically, mirroring
`DeliveryScheduler.assign_driver_for_delivery`. Each driver covers **one zone per shift**:

| Day              | Morning (9 AM – 1 PM) | Afternoon (1 PM – 5 PM) |
|------------------|-----------------------|-------------------------|
| Mon / Wed / Fri  | West (NW, SW)         | East (NE, SE)           |
| Tue / Thu / Sat  | East (NE, SE)         | West (NW, SW)           |
| Sun              | All zones             | All zones               |

Driver breakdown per shift:
- **Driver 1**: NW (one shift) ↔ NE (other shift)
- **Driver 2**: SW (one shift) ↔ SE (other shift)

### Usage

**Default — 3 orders per zone per active shift, both shifts, today:**
```bash
.venv/bin/python scripts/seed_orders.py
```

**Custom number of orders per zone:**
```bash
.venv/bin/python scripts/seed_orders.py --orders 5
```

**Morning shift only:**
```bash
.venv/bin/python scripts/seed_orders.py --shift morning
```

**Afternoon shift only:**
```bash
.venv/bin/python scripts/seed_orders.py --shift afternoon
```

**Specific delivery date:**
```bash
.venv/bin/python scripts/seed_orders.py --date 2026-04-28
```

**Cleanup all orders for today:**
```bash
.venv/bin/python scripts/seed_orders.py --cleanup
```

**Fix orders that already exist but have driver=null:**
```bash
.venv/bin/python scripts/seed_orders.py --fix-null-drivers
```

### Options

| Flag                | Type   | Default | Description                                                    |
|---------------------|--------|---------|----------------------------------------------------------------|
| `--orders`          | int    | 3       | Orders per zone per active shift                               |
| `--shift`           | choice | both    | Limit to `morning` or `afternoon`                              |
| `--date`            | str    | today   | Delivery date in `YYYY-MM-DD` format                           |
| `--cleanup`          | flag   | —       | Delete all orders for today instead of creating them           |
| `--fix-null-drivers` | flag   | —       | Compute and assign correct driver for every null-driver order  |
| `--as-saturday`      | flag   | —       | Apply Saturday zone/shift rules (useful for testing on Sundays)|

### Data generated

- **Driver**: always set — computed by `DeliveryScheduler` based on zone + shift + weekday
- **Zone clients**: 5 real Guadalajara addresses per zone (20 unique clients total)
- **Products**: random 2–5 items from the HIBerry catalog per order
- **Discounts**: 0 %, 5 %, 10 %, or 15 %
- **Payment methods**: Tarjeta or Efectivo
- **Status**: `Creada` for all seeded orders

### Requirements

- Virtual environment activated (`.venv`) with `boto3`, `aws-lambda-powertools`, `python-dotenv`
- AWS credentials configured (local DynamoDB or real AWS)
- `APP_ENVIRONMENT` env var set (defaults to `local`)
