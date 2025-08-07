# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dash is a user-friendly admin panel for handling IoT controllers, built with FastAPI and Python 3.12+. The system manages various IoT devices including carwash controllers, vacuum systems, water vending machines, and fiscalizers (receipt printers).

## Development Commands

### Environment Setup
- **Install dependencies**: `uv sync` (uses uv package manager)
- **Run application**: `uv run python -m dash run`
- **Run with Docker**: `docker-compose up`

### Database Operations
- **Run migrations**: `uv run alembic upgrade head`
- **Create migration**: `uv run alembic revision --autogenerate -m "description"`
- **Downgrade migration**: `uv run alembic downgrade -1`

### Testing & Quality
- **Run tests**: `uv run pytest`
- **Run specific test**: `uv run pytest tests/test_filename.py::test_function_name`
- **Lint code**: `uv run ruff check`
- **Format code**: `uv run ruff format`

### Utility Scripts
- **Create superadmin**: `uv run python scripts/create_superadmin.py`

## Architecture Overview

### Core Structure
```
src/dash/
├── main/           # Application bootstrap, configuration, DI setup
├── models/         # SQLAlchemy ORM models
├── services/       # Business logic layer
├── infrastructure/ # External integrations (DB, IoT, payments, auth)
├── presentation/   # FastAPI routes and HTTP layer
```

### Key Architectural Patterns

**Dependency Injection**: Uses Dishka for comprehensive DI container management across all layers.

**Repository Pattern**: Database access abstracted through repositories in `infrastructure/repositories/`.

**Service Layer**: Business logic encapsulated in services with clear separation of concerns.

**IoT Integration**: Multiple IoT client types (Carwash, WSM, Fiscalizer, MQTT) with unified interface patterns.

### Configuration System
- Uses Pydantic Settings with nested configuration classes
- Environment variables loaded from `.env` file using double-underscore delimiter (e.g., `POSTGRES__HOST`)
- Configuration classes: `PostgresConfig`, `RedisConfig`, `AppConfig`, `MqttConfig`, etc.

### Database Layer
- **ORM**: SQLAlchemy 2.0+ with async support
- **Migrations**: Alembic with PostgreSQL enum support
- **Connection**: AsyncPG driver for PostgreSQL
- **Models**: Located in `models/` with inheritance from `Base`

### IoT System
- **Multiple protocols**: HTTP clients for different device types, MQTT for real-time communication
- **Client abstractions**: Each IoT type has dedicated client in `infrastructure/iot/`
- **Callback handlers**: Located in `presentation/iot_callbacks/` for processing device events

### Authentication & Authorization
- **JWT tokens**: Access and refresh token system
- **Password hashing**: bcrypt for secure password storage
- **SMS verification**: Integration for user verification flows

### Payment Processing
- **Multiple providers**: Monopay, Liqpay, Checkbox integrations
- **Webhook handling**: Secure payment callback processing
- **Transaction tracking**: Complete audit trail for all payments

## Important Implementation Details

### Error Handling
- Custom error classes in `services/common/errors/`
- Global exception handlers in `presentation/exception_handlers.py`
- Structured logging with correlation IDs

### Testing Strategy
- Async test support with pytest-asyncio
- Test configuration in `tests/conftest.py`
- Mock-based testing for external services

### Performance & Monitoring
- DataDog integration available via configuration
- Structured logging with structlog
- Connection pooling for database and Redis

### Development Notes
- Code uses Python 3.12+ features including type hints and pattern matching
- Ruff for linting and formatting with specific rule configuration
- All async/await patterns throughout the codebase
- UV package manager for fast dependency resolution