FROM ghcr.io/mlflow/mlflow:v3.1.1

COPY start-mlflow.sh /mlflow/start-mlflow.sh
RUN chmod +x /mlflow/start-mlflow.sh
