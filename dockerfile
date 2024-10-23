# Use the official Python image from the Docker Hub
FROM python:3.8-slim

# Set environment variables to avoid generating .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && apt-get clean

# Copy requirements.txt and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files to the working directory
COPY . /app/

# Expose port 4001
EXPOSE 4001

# Run Django server on port 4001
CMD ["python", "manage.py", "runserver", "0.0.0.0:4001"]
