# RewriteForge Service

A microservice to rewrite text into different styles (e.g., pirate, haiku, formal) using a configurable LLM backend.

## Features

*   Rewrites text via `POST /v1/rewrite`.
*   Supports styles: `pirate`, `haiku`, `formal` (default).
*   Configurable LLM adapter (stub, OpenAI, Anthropic).
*   Input text length limit (default: 5000 chars).
*   Health check endpoint (`GET /health`).
*   Optional in-memory caching.
*   Containerized with Docker.
*   Linting/formatting with Ruff.
*   Testing with Pytest.

## Project Structure

~~~
rewriteforge/
├── app/ # Main application code
│ ├── api/ # HTTP API layer (FastAPI)
│ ├── core/ # Configuration, core settings
│ ├── llm/ # LLM adapter interface and implementations
│ ├── services/ # Business logic (rewriting service)
│ └── main.py # FastAPI app entry point
├── tests/ # Unit and integration tests
│ ├── unit/
│ └── integration/
├── .env.example # Example environment variables
├── .gitignore # Git ignore rules
├── Dockerfile # Container definition
├── pyproject.toml # Project metadata and dependencies (Poetry)
└── README.md # This file
~~~

## Setup and Running

### Prerequisites

*   Python 3.10+
*   Poetry (recommended for dependency management)
*   Docker (for containerized deployment)

### Local Development (using Poetry)

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd rewriteforge
    ```

2.  **Install dependencies:**
    ```bash
    poetry install --with dev
    ```

3.  **Configure environment:**
    Copy `.env.example` to `.env` and modify as needed.
    ```bash
    cp .env.example .env
    # Edit .env to set LLM_PROVIDER, LLM_API_KEY (if applicable), etc.
    # For local dev outside Docker, you might set RELOAD=True
    ```

4.  **Run the service:**
    ```bash
    poetry run uvicorn app.main:app --reload
    ```
    *(The `--reload` flag uses the `RELOAD` variable from `.env` if using `poetry run python -m app.main`, but is explicit here for clarity)*

    The service will be available at `http://localhost:8000` (or the port specified in `.env`). Access interactive docs at `http://localhost:8000/docs`.

### Running with Docker

1.  **Build the Docker image:**
    ```bash
    docker build -t rewriteforge:latest .
    ```

2.  **Run the container:**
    ```bash
    # Using the stub adapter (default)
    docker run -d -p 8000:8000 --name rewriteforge-app rewriteforge:latest

    # Using OpenAI adapter (example, requires API key)
    # docker run -d -p 8000:8000 \
    #   --env LLM_PROVIDER=openai \
    #   --env LLM_API_KEY="your_actual_openai_key" \
    #   --name rewriteforge-app rewriteforge:latest

    # Enabling cache
    # docker run -d -p 8000:8000 \
    #   --env CACHE_ENABLED=True \
    #   --env CACHE_TTL_SECONDS=600 \
    #   --name rewriteforge-app rewriteforge:latest
    ```
    The service will be available at `http://localhost:8000`.

## Running Tests

Ensure development dependencies are installed (`poetry install --with dev`).

```bash
poetry run pytest
```

## Linting and Formatting

Ensure development dependencies are installed.

# Check formatting and linting
```bash
poetry run ruff check .
poetry run ruff format --check .
```

# Apply formatting and fixes (if possible)
```bash
poetry run ruff format .
poetry run ruff check --fix .
```

## API Endpoints

POST /v1/rewrite: Rewrites text.

Request Body:

{
  "text": "string",
  "style": "pirate | haiku | formal" // Defaults to "formal"
}

Response Body (Success: 200 OK):

{
  "original_text": "string",
  "rewritten_text": "string",
  "style": "string"
}

Error Responses: 400 Bad Request (e.g., text too long), 422 Unprocessable Entity (invalid style/body), 500 Internal Server Error, 503 Service Unavailable (LLM connection issue).

GET /health: Health check.

Response Body (Success: 200 OK):

{
  "status": "ok",
  "llm_adapter_status": "ok | degraded | error"
}

Error Responses: 500 Internal Server Error, 503 Service Unavailable (depending on implementation if core components fail).


## Next Steps

# Refactor code after Google AI Studio generation. There are still suggestive comments inside. A lot of if

# Implement actual LLM calls

# Refactor adapter to exclude middle of file imports and reduce the number of if/else statements and remove the fallback to StubLLMAdapter

# Move caching to real caching solution

# Have an integration test "with integration" :)

# Add tests for Anthropic
