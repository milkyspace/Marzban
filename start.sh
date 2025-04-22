#!/bin/bash
source /code/.venv/bin/activate
/code/.venv/bin/python -m alembic upgrade head
/code/.venv/bin/python main.py