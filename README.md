# Neo-Chat AI Orchestration Layer

An OpenAI-compatible orchestration layer with enterprise-grade features including credit management, multi-LLM routing, and advanced preprocessing.

## Features

- OpenAI-compatible API
- Credit management system
- Multi-LLM routing via OpenRouter
- Rate limiting
- Preprocessing pipeline
- Security features

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```
   cp .env.example .env
   ```
4. Run the development server:
   ```
   uvicorn src.main:app --reload
   ```

## API Documentation

Once the server is running, you can access the API documentation at:
```
http://localhost:8000/docs
```

## Environment Variables

- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: Secret for JWT token generation
- `ENCRYPTION_KEY`: Key for data encryption 