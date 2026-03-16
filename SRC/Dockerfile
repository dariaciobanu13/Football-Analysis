# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements or explicitly install them
# For this demo, we can just run pip install directly
RUN pip install --no-cache-dir pandas matplotlib seaborn openpyxl statsbombpy

# Copy the current directory contents into the container at /app
COPY . /app/

# Define default command to run the pipeline
ENTRYPOINT ["python", "main.py"]

# Default arguments (can be overridden when running)
CMD ["--match-id", "303596", "--team", "Barcelona"]
