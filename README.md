# HiBerry Delivery Planner — Backend

Serverless backend for the HiBerry delivery management app. Handles order creation, driver assignment, delivery scheduling, client management, and Shopify integration. Built with Python 3.11, AWS SAM, API Gateway, DynamoDB, and Cognito.

## Architecture

The backend is split into **four independent SAM stacks**, each deployed separately:

| Stack | Path | Description |
|---|---|---|
| Orders | `src/orders/` | Core CRUD for orders + delivery scheduling + Shopify integration |
| Clients | `src/clients/` | Client records management |
| Products | `src/products/` | Product catalog |
| Users | `src/users/` | User management |

All stacks follow the same internal layered structure:
- **`models/`** — Pydantic v2 input validation
- **`dao/`** — High-level DynamoDB operations
- **`data_access/`** — Low-level AWS SDK clients (DynamoDB, Location Service)
- **`data_mapper/`** — Business logic that assembles DB records
- **`utils/`** — Auth, delivery scheduling, AWS helpers, encoders
- **`errors/`** — Custom exception hierarchy

## Orders API

The Orders stack exposes the following endpoints, all protected by a Cognito authorizer:

| Method | Path | Lambda handler | Description |
|---|---|---|---|
| `POST` | `/orders` | `app.create_order` | Create an order with automatic driver assignment |
| `GET` | `/orders` | `app.retrieve_orders` | Fetch orders by `delivery_date` |
| `PUT` | `/orders` | `app.update_order` | Update an existing order |
| `DELETE` | `/orders` | `app.delete_order` | Delete an order |
| `POST` | `/schedule-orders` | `app.set_delivery_schedule_order` | Sequence and assign routes for a delivery date |
| `POST` | `/update-sequencing-orders` | `app.update_delivery_schedule_order` | Persist a resequenced delivery route |

### Driver assignment

Drivers are assigned using a geographic sector model centred on the **Hidalgo & Alcalde intersection** in Guadalajara (`20.6783825, -103.348088`):

| Zone | Driver | Coordinates |
|---|---|---|
| NW — Zapopan, Providencia, Andares | 1 | lat ≥ origin, lon ≤ origin |
| NE — Huentitán, Santuario | 1 | lat ≥ origin, lon > origin |
| SW — Chapalita, López Mateos | 2 | lat < origin, lon ≤ origin |
| SE — Tlaquepaque, Tonalá | 2 | lat < origin, lon > origin |

Each driver handles one zone per shift, alternating east/west by day of week:

| Day | Morning (9 AM – 1 PM) | Afternoon (1 PM – 5 PM) |
|---|---|---|
| Mon / Wed / Fri | West (NW, SW) | East (NE, SE) |
| Tue / Thu  | East (NE, SE) | West (NW, SW) |
| Sat | All zones | All zones |

Capacity is **32 orders per driver per shift**. Shopify orders bypass capacity limits and are assigned by sector only.

### Shopify integration

`src/orders/integration/` listens for `orders/create` events on an EventBridge custom bus. It maps the Shopify payload and synchronously invokes `CreateOrderFunction` via `lambda.invoke`.

### DynamoDB schema

The Orders table uses a composite key: `delivery_date` (HASH) + `id` (RANGE).

## Local development

**Requirements:** Python 3.11, AWS SAM CLI, AWS credentials configured.

> Note: pydantic-core does not build on Python 3.14+. Use Python 3.11 explicitly.

### Run tests

```bash
cd tests
make install    # creates .venv and installs dependencies
make test       # pytest -v (all tests)
```

Run a single test file:

```bash
cd tests
source .venv/bin/activate
pytest orders/test_order_mapper.py -v
```

Run with coverage:

```bash
cd tests
../.venv311/bin/pytest --cov=../src/orders --cov-report=term-missing
```

### Environment

The `APP_ENVIRONMENT` env var controls behavior (`local | development | uat | prod`). In `local` mode:
- Cognito auth is bypassed — all operations are permitted
- Geolocation returns a hardcoded Guadalajara coordinate instead of calling AWS Location Service
- DynamoDB still requires a real or local endpoint

Set it for local Lambda invocations:

```bash
APP_ENVIRONMENT=local sam local invoke CreateOrderFunction --event events/create_order.json
```

### Database seeding

The `scripts/seed_orders.py` script seeds the Orders table with realistic Guadalajara delivery data using the real driver assignment logic.

```bash
# Seed 3 orders per zone per shift for today
.venv/bin/python scripts/seed_orders.py

# Custom options
.venv/bin/python scripts/seed_orders.py --orders 5 --shift morning --date 2026-04-28

# Clean up orders for today
.venv/bin/python scripts/seed_orders.py --cleanup
```

See [`scripts/README.md`](scripts/README.md) for full options.

## Deployment

Each stack deploys independently using SAM. `samconfig.toml` in each service directory holds environment-specific defaults.

```bash
cd src/orders
sam build
sam deploy  # uses samconfig.toml

# With overrides
sam deploy --parameter-overrides "StageName=development LogLevel=DEBUG ShopifyEventBusName=my-bus"
```

## CI/CD

GitHub Actions pipelines are defined in `.github/workflows/<service>_pipeline.yaml`. Each pipeline triggers on pushes to `src/<service>/**` and deploys sequentially through three environments:

```
run_unit_tests → development → uat (main only) → prod (main only)
```

All environments target `us-east-1`. Feature branches deploy to `development` only.

## Linting

```bash
flake8 src/orders/
```

Each service has a `.flake8` config that ignores E501 (line length) and W503 (line break before binary operator).
