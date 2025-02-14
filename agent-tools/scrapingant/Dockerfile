FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . ${LAMBDA_TASK_ROOT}

CMD [ "lambda_function.lambda_handler" ]
