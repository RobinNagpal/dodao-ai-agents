# Use the base Python 3.11 AWS Lambda image
FROM public.ecr.aws/lambda/python:3.11

# (Optional) If a lib needs a temp dir, you can set it here;
# Lambda gives you /tmp; configure more in console if needed.
ENV SOME_LIB_TMP=/tmp/some_lib

# Copy requirements & install
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy source
COPY . ${LAMBDA_TASK_ROOT}

# Tell Lambda the module:function to invoke
# i.e., src/final_lambda.py -> lambda_handler()
CMD [ "src.final_lambda.lambda_handler" ]
