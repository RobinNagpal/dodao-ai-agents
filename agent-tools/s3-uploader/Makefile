setup:
	uv venv --python=python3.11 .venv && uv pip install -r requirements.txt

install:
	uv pip install -r requirements.txt

run-test:
	source .venv/bin/activate && pytest -v ./test
