# --- Stage 1: Build ---
# Use an official Python runtime as a parent image
FROM python:3.10-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.8.2 # Use a specific Poetry version
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VIRTUALENVS_IN_PROJECT=true # Keep venv inside project dir for easier copying

# Install Poetry
RUN apt-get update && apt-get install --no-install-recommends -y curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get remove --purge -y curl \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Set the working directory in the container
WORKDIR /app

# Copy only dependency definition files first to leverage Docker cache
COPY poetry.lock pyproject.toml ./

# Install dependencies - without dev dependencies
# --no-root avoids installing the project itself in this stage, just dependencies
RUN poetry install --no-interaction --no-ansi --no-dev --no-root

# Copy the application code into the container
COPY ./app ./app

# --- Stage 2: Run ---
# Use a smaller base image for the final stage
FROM python:3.10-slim as final

# Set environment variables (repeat non-build specific ones)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Default port - can be overridden by ENV variable at runtime
ENV PORT=8000
# Default LLM provider - can be overridden
ENV LLM_PROVIDER="stub"
# Default Cache settings - can be overridden
ENV CACHE_ENABLED="False"
ENV CACHE_TTL_SECONDS=300
ENV CACHE_MAX_SIZE=1024
ENV MAX_TEXT_LENGTH=5000

# Set the working directory
WORKDIR /app

# Copy the virtual environment with dependencies from the builder stage
COPY --from=builder /app/.venv ./.venv

# Copy the application code from the builder stage
COPY --from=builder /app/app ./app

# Activate the virtual environment for subsequent commands
ENV PATH="/app/.venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE ${PORT}

# Command to run the application using Uvicorn
# Use 0.0.0.0 to allow connections from outside the container
# Access PORT via environment variable interpolation provided by the shell
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
