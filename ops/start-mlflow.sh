#!/bin/sh
set -e

# Use defaults from environment
POSTGRES_HOST=postgres
POSTGRES_ADMIN_DB=${POSTGRES_DATABASE:-postgres}
MLFLOW_DATABASE=${MLFLOW_DATABASE:-mlflow}
ENCODED_PG_PASSWORD=$(python3 -c "import urllib.parse, os; print(urllib.parse.quote(os.environ['POSTGRES_PASSWORD']))")

# Install Postgres client
apk add --no-cache postgresql-client || apt-get update && apt-get install -y postgresql-client

# Install psycopg2 for Python + PostgreSQL
pip install psycopg2-binary

echo "Waiting for Postgres at host '$POSTGRES_HOST'..."

# Wait until Postgres is ready
while ! PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_ADMIN_DB" -c '\q' >/dev/null 2>&1; do
  echo "Postgres not ready… sleeping 2s"
  sleep 2
done

echo "Postgres is up! Creating MLflow database if it does not exist..."

# Check if MLflow database exists; create if missing
DB_EXISTS=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_ADMIN_DB" -tAc "SELECT 1 FROM pg_database WHERE datname='$MLFLOW_DATABASE'")
if [ "$DB_EXISTS" != "1" ]; then
  echo "Database '$MLFLOW_DATABASE' does not exist. Creating..."
  PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_ADMIN_DB" -c "CREATE DATABASE \"$MLFLOW_DATABASE\";"
else
  echo "Database '$MLFLOW_DATABASE' already exists. Skipping creation."
fi

echo "Starting MLflow server..."
exec mlflow server \
  --host 0.0.0.0 \
  --port 5000 \
  --backend-store-uri postgresql://${POSTGRES_USER}:${ENCODED_PG_PASSWORD}@$POSTGRES_HOST:5432/${MLFLOW_DATABASE} \
  --default-artifact-root ${MLFLOW_TRACKING_URI}
