#!/bin/bash
/code/.venv/bin/python -m alembic upgrade head
/code/.venv/bin/python main.py