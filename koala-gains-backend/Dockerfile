# Use Python 3.11 slim base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy Poetry files
COPY poetry.lock pyproject.toml README.md /app/

# Copy the application files, including .env
COPY koala_gains /app/koala_gains

# Install Poetry
RUN pip install poetry

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false \
&& poetry install


# Copy commit info file
COPY koala_gains/commit_info.txt /app/koala_gains/

# Expose Flask's default port
EXPOSE 5000

# Set environment variables for Flask
ENV FLASK_ENV=development

# Command to run the Flask app
ENTRYPOINT ["poetry", "run", "python", "koala_gains/app.py"]
