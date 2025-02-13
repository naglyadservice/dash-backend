#!/usr/bin/env bash

set -e

uv run alembic upgrade head
exec uv run python -O -m dash.main.app