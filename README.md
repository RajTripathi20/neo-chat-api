# Neo-Chat AI Orchestration Layer

An OpenAI-compatible API with enterprise features for AI model orchestration.

## Overview

This project provides an API that is compatible with the OpenAI API, allowing clients to use it as a drop-in replacement while adding enterprise features such as:

- Authentication and authorization
- Rate limiting
- Credit management
- Request logging
- Model routing and orchestration
- Reasoning capabilities

## Project Structure

The project follows a modular architecture with clear separation of concerns:

```
src/
├── api/                  # API endpoints and middleware
│   ├── middleware.py     # Authentication, rate limiting, and credit checking middleware
│   └── openai_compat.py  # OpenAI-compatible API endpoints
├── models/               # Data models and database operations
│   ├── api_models.py     # Pydantic models for API requests and responses
│   ├── database.py       # Database connection and operations
│   ├── init_db.py        # Database initialization
│   ├── migrations.py     # Database migrations
│   └── schemas.py        # Database schemas
├── processing/           # Request processing pipeline
│   ├── pipeline.py       # Processing pipeline implementation
│   └── steps/            # Individual processing steps
├── providers/            # External AI providers
│   └── openrouter.py     # OpenRouter API client
├── services/             # Business logic services
│   ├── accounting.py     # Credit management
│   ├── authentication.py # Authentication and authorization
│   └── rate_limiter.py   # Rate limiting
├── utils/                # Utility functions and constants
│   ├── constants/        # Application constants
│   │   ├── __init__.py   # Constants module initialization
│   │   ├── api.py        # API-related constants
│   │   ├── auth.py       # Authentication-related constants
│   │   ├── errors.py     # Error message constants
│   │   ├── http.py       # HTTP status codes and headers
│   │   ├── messages.py   # Message-related constants
│   │   ├── models.py     # Model-related constants
│   │   └── server.py     # Server configuration constants
│   └── logging.py        # Logging utilities
└── main.py               # Application entry point
```

## Key Components

### API Layer

The API layer provides OpenAI-compatible endpoints for chat completions and model listing. It handles request validation, authentication, and response formatting.

### Processing Pipeline

The processing pipeline implements the Chain of Responsibility pattern to process requests through multiple steps, such as:

1. Sanitization - Filter out harmful content
2. Intent Classification - Determine the user's intent
3. Model Selection - Choose the appropriate model for the request
4. Request Transformation - Transform the request for the selected model

### Providers

The providers module contains clients for external AI providers, such as OpenRouter, which is used to route requests to various AI models.

### Services

The services module contains business logic for:

- Authentication and authorization
- Rate limiting
- Credit management

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL

### Installation

1. Clone the repository:

```bash
git clone https://github.com/your-org/neo-chat-ai-orchestration.git
cd neo-chat-ai-orchestration
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file with the following variables:

```
DATABASE_URL=postgresql://user:password@localhost:5432/neochat
OPENROUTER_API_KEY=your-openrouter-api-key
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

5. Initialize the database:

```bash
python -m src.models.init_db
```

6. Run the application:

```bash
python -m src.main
```

## API Usage

### Authentication

All API requests require an API key in the `Authorization` header:

```
Authorization: Bearer sk-neochat-your-api-key
```

### Chat Completions

```http
POST /v1/chat/completions
Content-Type: application/json
Authorization: Bearer sk-neochat-your-api-key

{
  "model": "neo-reasoning",
  "messages": [
    {
      "role": "user",
      "content": "Explain quantum computing in simple terms"
    }
  ],
  "max_tokens": 500,
  "temperature": 0.7,
  "include_reasoning": true,
  "reasoning_effort": "high"
}
```

### List Models

```http
GET /v1/models
Authorization: Bearer sk-neochat-your-api-key
```

## Development

### Adding a New Processing Step

1. Create a new class that inherits from `ProcessingStep` in `src/processing/steps/`:

```python
from src.processing.pipeline import ProcessingStep
from src.models.api_models import ChatRequest

class MyNewStep(ProcessingStep):
    async def execute(self, request: ChatRequest) -> ChatRequest:
        # Process the request
        return request
```

2. Add the step to the pipeline in `src/processing/pipeline.py`:

```python
from src.processing.steps.my_new_step import MyNewStep

class ContentProcessor:
    def __init__(self):
        self.steps = [
            SanitizationFilter(),
            IntentClassifier(),
            MyNewStep(),  # Add your new step here
        ]
```

### Adding a New Model

1. Add the model information to `src/utils/constants/models.py`:

```python
AVAILABLE_MODELS = [
    # Existing models...
    {
        "id": "neo-new-model",
        "name": "Neo New Model",
        "description": "A new model with special capabilities.",
        "input_price_per_million_tokens": 1.5,
        "output_price_per_million_tokens": 4.0,
        "context_length": 128000
    }
]
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [OpenAI](https://openai.com/) for the API design
- [OpenRouter](https://openrouter.ai/) for model routing
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework 