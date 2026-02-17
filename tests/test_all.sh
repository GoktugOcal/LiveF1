pip install -r requirements-dev.txt
pytest tests/ -v
# or with coverage:
# pytest tests/ -v --cov=livef1 --cov-report=term-missing