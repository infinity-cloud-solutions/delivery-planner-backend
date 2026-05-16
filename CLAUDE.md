# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Tests

Tests live in `tests/` and run against the whole repo from there:

```bash
cd tests
make install   # create .venv and install requirements.txt
make test      # pytest -v
```

Run a single test file:
```bash
cd tests && source .venv/bin/activate && pytest tests/create_order/test_lambda_handler.py -v
```

### Build & Deploy (AWS SAM)

Each service has its own `template.yaml` and `samconfig.toml`. Deploy from the service directory:

```bash
# Orders service (example)
cd src/orders
sam build
sam deploy   # uses samconfig.toml defaults

# With overrides
sam deploy --parameter-overrides "StageName=development LogLevel=DEBUG"
```

### Linting

Flake8 is configured per-service (`.flake8` ignores E501 and W503):

```bash
flake8 src/orders/
```

## Architecture

This is a **Python 3.11 serverless backend** deployed on AWS via SAM (CloudFormation). It is split into four independent SAM stacks, each with its own `template.yaml`, `requirements.txt`, and `samconfig.toml`:

| Stack | Path | Lambda handlers |
|---|---|---|
| Orders | `src/orders/` | `app.py` — create/retrieve/update/delete orders |
| Orders - Delivery | `src/orders/delivery/` | schedule and resequence delivery routes |
| Orders - Shopify Integration | `src/orders/integration/` | EventBridge → Lambda bridge for Shopify webhooks |
| Clients | `src/clients/` | CRUD for client records |
| Products | `src/products/` | CRUD for product catalog |

CI/CD is GitHub Actions. Each push to `src/<service>/**` triggers its own pipeline (`.github/workflows/<service>_pipeline.yaml`), which runs tests then deploys to `development → uat → prod` sequentially.

### Internal module layout (consistent across services)

Each `src/<service>/<service>_modules/` package follows the same layered structure:

- **`models/`** — Pydantic v2 data models (validate inputs at Lambda boundary)
- **`dao/`** — Data Access Objects: high-level DynamoDB operations (create, fetch, update, delete, bulk_update)
- **`data_access/`** — Low-level AWS clients: `dynamo_handler.py` (DynamoDB) and `geolocation_handler.py` (AWS Location Service)
- **`data_mapper/`** — Business logic that assembles DB records from validated models (e.g., `OrderHelper.build_order`)
- **`utils/`** — Cross-cutting helpers:
  - `doorman.py` — auth + request parsing (see below)
  - `delivery.py` — driver assignment algorithm
  - `aws.py` — boto3 client factory
  - `encoders.py` — JSON `DecimalEncoder` for DynamoDB Decimal types
  - `status.py` / `source.py` — enums for order states and order origins
- **`errors/`** — Custom exception hierarchy (`BaseError → AuthError, BusinessError, DAOError, …`)

### Key patterns

**DoormanUtil** (`utils/doorman.py`) is the entry-point helper used in every Lambda handler. It wraps: auth via Cognito group → Lambda function name ACL, request body parsing, query param extraction, and response building. When `APP_ENVIRONMENT=local`, auth is bypassed and all operations are permitted.

**Environments** are controlled by the `APP_ENVIRONMENT` env var (`local | development | uat | prod`). `settings.py` at each service root reads this and exports table names and other config. In local mode, geolocation returns a hardcoded Guadalajara coordinate and DynamoDB still requires a real or local endpoint.

**Driver assignment** (`order_modules/utils/delivery.py → DeliveryScheduler`) uses a geographic sector model centred on Guadalajara's Hidalgo/Alcalde intersection. Orders are split into 4 quadrants (NW/SW/NE/SE); Driver 1 covers north, Driver 2 covers south. Capacity is 32 orders per driver per time slot (morning 9AM-1PM / afternoon 1PM-5PM). Shopify orders skip capacity checks and are assigned by sector only.

**Shopify integration** (`src/orders/integration/`) listens for `orders/create` events on an EventBridge custom bus. It maps the Shopify payload via `ShopifyDataMapper`, then synchronously invokes `CreateOrderFunction` directly via boto3 `lambda.invoke`.

**DynamoDB schema** for Orders uses a composite key: `delivery_date` (HASH) + `id` (RANGE). Clients use `phone_number` as the primary key. Products use their own key defined in their template.

### Test conventions

Tests import service code via the package path (e.g., `from src.orders.app import create_order`). AWS SDK calls are mocked with `unittest.mock.patch`. The `APP_ENVIRONMENT=local` env override is applied with `@patch.dict(os.environ, {"APP_ENVIRONMENT": "local"}, clear=True)` to bypass auth and geolocation.
