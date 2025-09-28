# Optimized Single-Stage Build for Apache Airflow
FROM apache/airflow:3.1.0-python3.12

USER root

# Install build dependencies for compilation (will be removed later)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Copy plumbing_core and requirements.txt
COPY plumbing_core /opt/plumbing_core
COPY plumbing_airflow/requirements.txt /opt/

# Install all dependencies using uv (faster than pip)
RUN uv pip install --no-cache-dir -r /opt/requirements.txt

# Copy DAGs to working directory
COPY plumbing_airflow/dags /opt/airflow/dags

# Clean up build dependencies and caches to reduce image size
RUN apt-get autoremove -y \
    build-essential \
    gcc \
    g++ \
    cmake \
    && apt-get autoclean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/* \
    && rm -rf /root/.cache \
    && find /usr/local/lib/python3.12/site-packages -name "*.pyc" -delete \
    && find /usr/local/lib/python3.12/site-packages -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Set proper ownership for airflow user
RUN chown -R airflow:root /opt/airflow/dags

USER airflow
