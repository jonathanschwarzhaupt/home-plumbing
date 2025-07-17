# Plumbing Airflow

Apache Airflow 3.0 orchestration layer for the Home Plumbing data engineering project. This package provides workflow automation and scheduling for financial data extraction, transformation, and loading pipelines using the `plumbing_core` library.

## Features

- **Apache Airflow 3.0**: Latest Airflow with modern task SDK and execution patterns
- **Custom Docker Image**: Extended Airflow image with `plumbing_core` integration
- **Comdirect DAGs**: Automated authentication and data extraction workflows
- **Local Development**: Complete docker-compose setup with Redis, PostgreSQL, and volume mounting
- **Task Flow API**: Modern Airflow patterns with @task decorators and typed interfaces

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.12+
- `uv` package manager (for local development)

### 1. Environment Setup

Create a `.env` file in the `src/plumbing_airflow/` directory:

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
```

### 2. Local Development

```bash
# Navigate to Airflow directory
cd src/plumbing_airflow

# Build and start services
docker-compose up -d --build

# Access Airflow UI
open http://localhost:8080
# Login: airflow / airflow
```

### 3. Package Development

```bash
# Install local package for development
uv add ../plumbing_core

# Generate requirements.txt from pyproject.toml
uv pip compile pyproject.toml -o requirements.txt

# Rebuild Docker image after changes
docker-compose build
```

## Project Structure

```
src/plumbing_airflow/
├── README.md
├── pyproject.toml              # Python package configuration
├── requirements.txt            # Generated dependencies for Docker
├── uv.lock                     # Locked dependencies
├── Dockerfile                  # Custom Airflow image with plumbing_core
├── docker-compose.yaml         # Complete Airflow cluster setup
├── dags/
│   └── comdirect_auth.py      # Comdirect authentication DAG
├── plugins/                   # Custom Airflow plugins
└── logs/                      # Airflow execution logs
```

## DAG Examples

### Comdirect Authentication DAG

The `comdirect_auth` DAG demonstrates the complete OAuth 2.0 flow with PhotoTan challenge:

```python
from airflow.sdk import dag, task, Variable
from plumbing_core.sources.comdirect import (
    APIConfig, get_session_id, authenticate_user_credentials
)

@dag(start_date=datetime(2025, 4, 1), schedule=None, tags=["comdirect"])
def comdirect_auth():
    @task
    def get_auth_token():
        cfg = APIConfig()
        session_id = get_session_id()
        access_token = authenticate_user_credentials(cfg=cfg, session_id=session_id)
        return access_token.to_dict()

    @task
    def save_auth_token(access_token) -> None:
        Variable.set(
            key="comdirect_access_token", 
            value=access_token, 
            serialize_json=True
        )

    access_token = get_auth_token()
    save_auth_token(access_token)
```

**Features:**

- Task Flow API with @task decorators
- Automatic XCom passing between tasks
- Variable storage for token persistence
- Error handling and retry logic

## Development Workflow

### Building Custom Docker Image

The project uses a custom Dockerfile that extends the official Airflow 3.0.3 image:

```dockerfile
FROM apache/airflow:3.0.3-python3.12

USER root
COPY plumbing_core /opt/plumbing_core
COPY plumbing_airflow/requirements.txt /opt/
RUN uv pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /opt/requirements.txt

USER airflow
```

**Key points:**

- Copies `plumbing_core` package to container working directory
- Uses `uv` for fast dependency installation
- Maintains proper user permissions for Airflow execution

### Docker Compose Architecture

The setup includes a complete Airflow cluster:

- **airflow-apiserver**: Main web interface and API (port 8080)
- **airflow-scheduler**: DAG scheduling and task orchestration
- **airflow-dag-processor**: DAG parsing and validation
- **airflow-worker**: Celery worker for task execution
- **airflow-triggerer**: Deferred task handling
- **postgres**: Metadata database
- **redis**: Celery message broker

### Volume Mounting

Development volumes are automatically mounted:

```yaml
volumes:
  - ./dags:/opt/airflow/dags      # DAG files
  - ./logs:/opt/airflow/logs      # Execution logs
  - ./config:/opt/airflow/config  # Configuration files
  - ./plugins:/opt/airflow/plugins # Custom plugins
```

## Configuration

### Environment Variables

Required for Comdirect integration:

- `COMDIRECT_CLIENT_ID`: OAuth client identifier
- `COMDIRECT_CLIENT_SECRET`: OAuth client secret
- `COMDIRECT_USERNAME`: Banking username
- `COMDIRECT_PASSWORD`: Banking password

Optional Airflow customization:

- `AIRFLOW_UID`: User ID for file permissions (default: 50000)
- `_AIRFLOW_WWW_USER_USERNAME`: Web UI admin username
- `_AIRFLOW_WWW_USER_PASSWORD`: Web UI admin password

## Troubleshooting

### Common Issues and Solutions

**1. Flask Version Conflicts**

```bash
# Problem: Adding apache-airflow to pyproject.toml upgrades Flask, breaking API server
# Solution: Add airflow to dev group only, keep it out of requirements.txt
[dependency-groups]
dev = ["apache-airflow>=3.0.3", "ruff>=0.12.3"]
```

**2. Package Import Errors**

```bash
# Problem: "distribution not found" errors for plumbing_core
# Solution: Ensure COPY command places package in container working directory
COPY plumbing_core /opt/plumbing_core  # Correct location
```

**3. DAG Import Failures**

```bash
# Check DAG processor logs
docker-compose logs airflow-dag-processor

# Verify package installation in container
docker-compose exec airflow-worker python -c "import plumbing_core; print('OK')"
```

### Useful Commands

```bash
# View service logs
docker-compose logs airflow-scheduler
docker-compose logs airflow-worker

# Restart specific services
docker-compose restart airflow-scheduler

# Access Airflow CLI
docker-compose exec airflow-worker airflow --help

# Run DAG manually
docker-compose exec airflow-worker airflow dags trigger comdirect_auth
```

## Dependencies

Built on modern Python and Airflow stack:

- **Apache Airflow**: 3.0.3+ with task SDK and execution API
- **Python**: 3.12+ for modern language features
- **PostgreSQL**: 13 for metadata storage
- **Redis**: 7.2-bookworm for Celery message broker
- **uv**: Fast Python package manager
- **plumbing_core**: Local package for data integration

## Architecture Notes

### Task Flow Patterns

The project uses Airflow's modern Task Flow API patterns:

- **@task decorators**: Clean task definition without operators
- **Automatic XCom**: Type-safe data passing between tasks
- **Return values**: Tasks return Python objects directly
- **Error handling**: Built-in retry and failure handling

### Integration with plumbing_core

DAGs leverage the modular `plumbing_core` library:

- **Authentication**: OAuth flows handled by core auth module
- **Data extraction**: Account and transaction methods from core
- **Type safety**: Pydantic models ensure data integrity
- **Logging**: Consistent logging across core and orchestration layers

This separation allows the same data logic to be used in different orchestration contexts (Airflow, Prefect, standalone scripts, etc.).
