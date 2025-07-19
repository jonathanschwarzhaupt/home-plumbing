# Home Plumbing

## 1. Overview / Background

Managing my personal finances through the Comdirect banking app has proven frustrating due to the lack of a detailed, customizable spending overview.I aim to solve that gap by independently extracting, integrating, and analyzing financial data to build a richer, tailored spending dashboard.

Beyond solving a personal need, the project also serves as a playground to integrate multiple data sources, explore modern technologies like Apache Airflow 3.0 with SQLite and DuckDB analytics integration, and apply modern data engineering best practices such as the Write-Audit-Publish (WAP) pattern.

Scope: This is a personal Proof of Concept (PoC) designed to validate the technical setup and workflows. The project may later evolve into a more polished, "production-grade" solution as features and robustness improve.

Goal: The goal is to have a Airflow installation running in my Kubernetes [homelab](https://github.com/jonathanschwarzhaupt/homelab).

## 2. Project Structure

The codebase follows a modular structure with core plumbing logic separated from orchestration:

- **Core package**: `src/plumbing_core/` - Reusable Python package with source connectors, auth helpers, and typed data models
- **Comdirect integration**: `src/plumbing_core/src/plumbing_core/sources/comdirect/` - Banking API connector with OAuth flow
- **SQLite destination**: `src/plumbing_core/src/plumbing_core/destinations/sqlite/` - SQLite storage with DuckDB analytics integration
- **Airflow orchestration**: `src/plumbing_airflow/` - Apache Airflow 3.0 DAGs and Docker setup for workflow automation
- **Examples**: `src/plumbing_core/examples/` - Demonstration scripts

```
.
├── src/
│   ├── plumbing_core/
│   │   ├── sources/
│   │   │   └── comdirect/
│   │   │       ├── auth.py         # OAuth 2.0 flow with PhotoTan
│   │   │       ├── data.py         # Data extraction methods
│   │   │       ├── helpers.py      # HTTP utilities
│   │   │       └── types.py        # Pydantic models
│   │   └── destinations/
│   │       └── sqlite/
│   │           ├── config.py       # SQLite configuration
│   │           ├── connection.py   # DuckDB connection manager
│   │           └── writers.py      # Data writers with upsert logic
│   └── plumbing_airflow/
│       ├── dags/                   # Airflow DAGs package
│       │   └── plumbing_airflow/
│       │       ├── comdirect/      # Comdirect workflow DAGs
│       │       └── shared/         # Shared DAG configurations
│       ├── docker-compose.yaml     # Complete Airflow cluster setup
│       └── Dockerfile              # Custom Airflow image
```

## 3. Tasks / TODOs

- [x] Write comdirect source module
- [x] Write SQLite destination module
- [x] Create Airflow 3.0 orchestration layer
- [x] Docker compose setup for Airflow local development
- [ ] Write basic unit tests
- [ ] Production deployment to Kubernetes homelab
- [ ] Categorization of transactions
- [ ] Visual frontend to track my spending

## 4. Setup Instructions

### Prerequisites

- Python 3.12+
- `uv` package manager
- `mise` for environment management
- Docker and Docker Compose (for Airflow)

### Installation

1. **Initial setup** (runs automatically via mise hook):

   ```bash
   ./scripts/setup_project
   mise install
   ```

2. **Install core package**:

   ```bash
   cd src/plumbing_core
   uv pip install .
   ```

3. **Environment variables**:

   ```bash
   # Required for Comdirect API
   export COMDIRECT_CLIENT_ID="your_client_id"
   export COMDIRECT_CLIENT_SECRET="your_client_secret"
   export COMDIRECT_USERNAME="your_username"
   export COMDIRECT_PASSWORD="your_password"
   
   # Optional for SQLite
   export SQLITE_DB_PATH="path/to/database.db"
   ```

### Airflow Development

1. **Navigate to Airflow directory**:

   ```bash
   cd src/plumbing_airflow
   ```

2. **Create environment file** (`.env`):

   ```bash
   # Airflow configuration - optional
   AIRFLOW_UID=50000
   _AIRFLOW_WWW_USER_USERNAME=airflow
   _AIRFLOW_WWW_USER_PASSWORD=airflow

   # Comdirect API credentials
   COMDIRECT_CLIENT_ID=your_client_id
   COMDIRECT_CLIENT_SECRET=your_client_secret
   COMDIRECT_USERNAME=your_username
   COMDIRECT_PASSWORD=your_password
   COMDIRECT__SQLITE_PATH="/opt/airflow/database"
   ```

3. **Start Airflow services**:

   ```bash
   docker-compose up -d --build
   ```

4. **Access Airflow UI**:

   Open <http://localhost:8080> (login: airflow/airflow)

### Usage Examples

```python
from plumbing_core.sources.comdirect import (
    APIConfig, 
    authenticate_user_credentials,
    get_accounts_balances
)
from plumbing_core.destinations.sqlite import (
    SQLiteConfig,
    write_account_balances
)

# Extract account balances
balances = get_accounts_balances(cfg=config, bearer_access_token=token)

# Load to SQLite
db_config = SQLiteConfig(db_path=Path("comdirect.db"))
write_account_balances(balances=balances, config=db_config)
```

See `src/plumbing_core/examples/` for complete demonstration scripts.

## 5. Architecture Notes

### SQLite + DuckDB Integration

The SQLite destination uses an interesting architectural pattern: **SQLite for storage, DuckDB for analytics**.

- **SQLite**: Single-file databases with no infrastructure overhead. Each source gets its own `.db` file with a single writer, eliminating concurrency issues
- **DuckDB**: Acts as a bridge during analytics, allowing complex queries across multiple SQLite files and seamless integration with pandas/arrow ecosystems

This pattern scales well for modestly-sized data platforms where you want the simplicity of file-based storage but the analytical power of modern columnar query engines.

### OAuth Flow

The Comdirect authentication follows a multi-step OAuth 2.0 flow:

1. Generate initial OAuth token with user credentials
2. Create session object
3. Trigger PhotoTan challenge
4. Wait for user confirmation (configurable timeout)
5. Mark session as validated
6. Obtain final access token

### Data Models

- Uses Pydantic for type validation and data parsing
- Implements field flattening for nested API responses
- Automatic token expiry calculation and refresh logic

### Airflow Orchestration

The Airflow layer provides workflow automation using modern patterns:

- **Task Flow API**: Modern @task decorators with type-safe data passing
- **Shared Configuration**: Reusable DAG configurations and utilities in `shared.dag_config`
- **Custom Docker Image**: Extended Airflow 3.0.3 with integrated `plumbing_core` package
- **Complete Cluster**: PostgreSQL metadata, Redis message broker, and multiple Airflow services

## 6. Future Improvements and Ideas

- Parsing of digital grocery shopping receipts
- Enhanced error handling and retry logic
- Comprehensive test coverage
- Advanced analytics with e.g. DuckDB (reporting, insights)
- Production Kubernetes deployment to homelab
