FROM python:3.10-slim

RUN apt-get update && apt-get install -y git build-essential

WORKDIR /app

RUN pip install --upgrade pip && pip install langflow

EXPOSE 7860

CMD ["langflow", "run", "--host", "127.0.0.1", "--port", "7860"]
