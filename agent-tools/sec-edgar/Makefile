setup:
	uv venv --python=python3.11 .venv && uv pip install -r requirements.txt

install:
	uv pip install -r requirements.txt

run-test:
	source .venv/bin/activate && pytest -v ./test/test_lambda.py

run-single-test:
	source .venv/bin/activate && pytest -s ./test/test_lambda.py::test_all_financial_reports

run-test-windows: 
	source .venv/Scripts/activate && pytest -v ./test

run-test-local:
	source .venv/bin/activate && python -m src.test_local
