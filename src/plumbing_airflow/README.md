# Plumbing Airflow

## Commands I learned

* `uv add ../plumbing_core` to add the package from a local path
* `uv pip compile pyproject.toml -o requirements.txt` to generate the requirements.txt file from pyproject.toml
* `uv add ../plumbing_core` to install my local package

## Debuggings I had to build my custom Airflow image

* Started with provided docker compose file, all worked (volumes already mounted to mount dags for example)
* Added custom image from provided Dockerfile, all worked
* Added apache-airflow:3.0.3 to pyprject.toml - this resulted in a silently upgraded Flask version which broke the airflow apiserver - Added airflow to dev group to avoid IDE error messages but keep it out of requirements.txt. Airflow docker image relies on older Flask version than the airflow package
* Adding local image did not work immediately - needed to debug distribution not found errors as I did not copy my local package to the correct location that was the working directory of the image and thus could not be resolved with the relative import
