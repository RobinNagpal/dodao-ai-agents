# Use the base Python 3.11 AWS Lambda image
FROM public.ecr.aws/lambda/python:3.11

# Set edgartools to use a writable directory for local data
ENV EDGAR_LOCAL_DATA_DIR=/tmp/edgar_data

# Copy requirements file from this folder
COPY requirements.txt /tmp/requirements.txt

# Install dependencies into the container
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the rest of the code into the container
COPY . ${LAMBDA_TASK_ROOT}

# Set the Lambda entry point to lambda_function.lambda_handler
CMD [ "src.app.lambda_handler" ]
