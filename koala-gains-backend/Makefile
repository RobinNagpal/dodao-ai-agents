pull-image:
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 729763663166.dkr.ecr.us-east-1.amazonaws.com
	docker pull 729763663166.dkr.ecr.us-east-1.amazonaws.com/koala-gains-backend:latest

run-image:
	docker stop cf-analysis-container || true
	docker rm cf-analysis-container || true
	docker run -it -p 9500:5000 --name cf-analysis-container 729763663166.dkr.ecr.us-east-1.amazonaws.com/koala-gains-backend:latest env

activate-venv:
	source .venv/bin/activate

run-project:
	poetry run python -m koala_gains.app

setup:
	poetry env use 3.11
	poetry install

fmt:
	black koala_gains
