#!/bin/bash
source /code/.venv/bin/activate
python -m alembic upgrade head
python main.py