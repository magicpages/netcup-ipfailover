FROM python:3.9-slim

# Install necessary packages
RUN apt update && apt install -y iputils-ping && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir zeep

# Copy the application to the container
COPY failover/ /srv/failover/

# Set the working directory
WORKDIR /srv/failover

# Command to run the application
ENTRYPOINT ["python", "failover.py"]
