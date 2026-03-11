# Use an official Python slim runtime as a parent image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (required for some C-extensions like scipy/numpy if wheels aren't matched perfectly, though slim usually works well)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 5000 to the docker network
EXPOSE 5000

# Run gunicorn server mapped to 5000 internally. 4 workers handles standard concurrent analytics load.
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "server:app"]
