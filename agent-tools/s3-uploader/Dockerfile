FROM public.ecr.aws/lambda/python:3.11

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . ${LAMBDA_TASK_ROOT}

CMD [ "src.lambda_function.lambda_handler" ]
