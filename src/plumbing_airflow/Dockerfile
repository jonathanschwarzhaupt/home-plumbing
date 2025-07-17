FROM apache/airflow:3.0.3-python3.12

USER root

# Copy plumbing_core and requirements.txt to working directory
COPY plumbing_core /opt/plumbing_core
COPY plumbing_airflow/requirements.txt /opt/

# Install all dependencies from requirements.txt using uv
# Now ../plumbing_core in requirements.txt resolves correctly
RUN uv pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /opt/requirements.txt

USER airflow
