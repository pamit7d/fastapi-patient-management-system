#!/bin/sh

# Run migrations (if any using alembic in future, for now just app startup handles creation)
# alembic upgrade head

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
