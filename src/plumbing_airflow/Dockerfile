FROM apache/airflow:3.0.2-python3.12

USER root

# Install build dependencies for libsql (Rust-based package)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Copy plumbing_core, requirements.txt and dags to working directory
COPY plumbing_core /opt/plumbing_core
COPY plumbing_airflow/requirements.txt /opt/
COPY plumbing_airflow/dags /opt/airflow/dags

# Install all dependencies from requirements.txt using uv
# Now ../plumbing_core in requirements.txt resolves correctly
RUN uv pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /opt/requirements.txt

USER airflow
