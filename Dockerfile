FROM continuumio/miniconda3:latest

COPY Requirements_Linux.yaml /tmp/environment.yml

RUN conda env create -f /tmp/environment.yml

# Always run inside environment
SHELL ["conda", "run", "-n", "Project_4_CS325", "/bin/bash", "-c"]

# Ensure Python can import "core", "gui", etc.
ENV PYTHONPATH="/app"

# Copy project files
WORKDIR /app
COPY . /app

# Default command: run tests
CMD ["conda", "run", "-n", "Project_4_CS325", "pytest", "-q"]
