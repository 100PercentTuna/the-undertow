#!/bin/bash
# Create a new Alembic migration

if [ -z "$1" ]; then
    echo "Usage: ./scripts/create_migration.sh 'migration description'"
    exit 1
fi

poetry run alembic revision --autogenerate -m "$1"

