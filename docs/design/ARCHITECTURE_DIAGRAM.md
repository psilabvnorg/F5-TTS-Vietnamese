# System Architecture: F5-TTS Vietnamese API v2.0

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │  React UI  │  │   Vue UI   │  │  Mobile    │                │
│  │            │  │            │  │  App       │                │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                │
│        │               │               │                        │
│        └───────────────┴───────────────┘                        │
│                        │                                        │
│                        │ HTTPS/REST API                         │
└────────────────────────┼────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MIDDLEWARE LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  1. CORS Handler                                         │   │
│  │     - Origin validation                                  │   │
│  │     - Credentials handling                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  2. Authentication Middleware                            │   │
│  │     - JWT token validation                               │   │
│  │     - User session management                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  3. Rate Limiter                                         │   │
│  │     ┌──────────────┐        ┌────────────────────────┐  │   │
│  │     │ Authenticated│        │  Anonymous (Redis)     │  │   │
│  │     │  Users       │        │  IP+UA session         │  │   │
│  │     │  (Unlimited) │        │  5 req / 24h window    │  │   │
│  │     └──────────────┘        └────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  4. Request Validator                                    │   │
│  │     - Text length check (max 1000 chars for anonymous)   │   │
│  │     - Input sanitization                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API ENDPOINTS                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Authentication│  │  TTS Gen     │  │  Voice Mgmt  │          │
│  │               │  │              │  │              │          │
│  │ /auth/login  │  │ /tts/generate│  │ /voices      │          │
│  │ /auth/register│  │ /tts/async   │  │ /voices/{id} │          │
│  │ /auth/me     │  │              │  │              │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Text Preprocessing Pipeline                             │   │
│  │  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   │   │
│  │  │Lower │→→→│Remove│→→→│Convert│→→│Replace│→→│Clean │   │   │
│  │  │case  │   │Special│  │Numbers│  │Periods│  │Spaces│   │   │
│  │  └──────┘   └──────┘   └──────┘   └──────┘   └──────┘   │   │
│  │       "XIN CHÀO! 5 táo."  →  "xin chào, năm táo"         │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  User Management                                         │   │
│  │  - Password hashing (bcrypt)                             │   │
│  │  - Token generation (JWT)                                │   │
│  │  - Usage tracking                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  TTS Engine Interface                                    │   │
│  │  - Voice selection                                       │   │
│  │  - F5-TTS CLI invocation                                 │   │
│  │  - Output handling                                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Database   │  │  File System │  │   Cache      │          │
│  │              │  │              │  │              │          │
│  │ - Users      │  │ - Ref Audio  │  │ - Redis      │          │
│  │ - Sessions   │  │ - Output WAV │  │   - Rate Limit store    │
│  │ - API Logs   │  │ - Vocab      │  │ - Temp Data  │          │
│  │              │  │ - Model      │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Request Flow

### Anonymous User Request Flow

```
┌──────────┐
│ Frontend │
│  Client  │
└────┬─────┘
     │
     │ POST /tts/generate
     │ { text: "xin chào", voice: "tran_ha_linh" }
     ▼
┌────────────────────────────────────────┐
│  Middleware: CORS                      │
│  ✓ Check origin                        │
└────┬───────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│  Middleware: Rate Limiter              │
│  - Generate session ID (IP+UA)         │
│  - Redis-backed counter + 24h reset    │
│  - Check: 5 requests remaining?        │
│  - Check: text < 1000 chars?           │
│  ✓ Pass or Reject (429)                │
└────┬───────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│  Text Preprocessor                     │
│  1. lowercase                          │
│  2. replace periods → commas           │
│  3. remove special chars               │
│  4. convert numbers (optional)         │
└────┬───────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│  TTS Engine (F5-TTS)                   │
│  - Load model                          │
│  - Load voice reference                │
│  - Generate audio                      │
│  - Save to output/                     │
└────┬───────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│  Response                              │
│  - Audio file (WAV)                    │
│  - Headers:                            │
│    X-RateLimit-Remaining: 4            │
│    X-RateLimit-Reset: 2025-...         │
└────┬───────────────────────────────────┘
     │
     ▼
┌──────────┐
│ Frontend │
│  Plays   │
│  Audio   │
└──────────┘
```

### Authenticated User Request Flow

```
┌──────────┐
│ Frontend │
│  Client  │
└────┬─────┘
     │
     │ POST /tts/generate
     │ Headers: Authorization: Bearer <JWT>
     │ { text: "xin chào", voice: "tran_ha_linh" }
     ▼
┌────────────────────────────────────────┐
│  Middleware: CORS                      │
│  ✓ Check origin                        │
└────┬───────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│  Middleware: Authentication            │
│  - Extract JWT from header             │
│  - Verify signature                    │
│  - Check expiration                    │
│  - Get user_id from token              │
│  ✓ Valid → Continue                    │
│  ✗ Invalid → 401 Unauthorized          │
└────┬───────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│  Rate Limiter                          │
│  - Authenticated user detected         │
│  ✓ SKIP rate limiting (unlimited)      │
│  - Log usage for analytics             │
└────┬───────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│  Text Preprocessor                     │
│  (same as anonymous)                   │
└────┬───────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│  TTS Engine (F5-TTS)                   │
│  (same as anonymous)                   │
└────┬───────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────┐
│  Response                              │
│  - Audio file (WAV)                    │
│  - Headers:                            │
│    X-Authenticated: true               │
│    X-User-ID: user_123                 │
└────┬───────────────────────────────────┘
     │
     ▼
┌──────────┐
│ Frontend │
│  Plays   │
│  Audio   │
└──────────┘
```

---

## Authentication Flow

### Registration Flow

```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Fill registration form
     │    (email, username, password)
     ▼
┌──────────────────┐
│  Frontend Form   │
│  Validation      │
│  - Email format  │
│  - Password ≥ 8  │
└────┬─────────────┘
     │ 2. POST /auth/register
     ▼
┌──────────────────────────────┐
│  Backend Validation          │
│  - Check email uniqueness    │
│  - Hash password (bcrypt)    │
└────┬─────────────────────────┘
     │ 3. Insert to database
     ▼
┌──────────────────────────────┐
│  Database                    │
│  INSERT INTO users           │
│  (email, username, hash)     │
└────┬─────────────────────────┘
     │ 4. Success
     ▼
┌──────────────────────────────┐
│  Generate JWT Token          │
│  - Payload: {sub: user_id}   │
│  - Expiry: 7 days            │
│  - Sign with SECRET_KEY      │
└────┬─────────────────────────┘
     │ 5. Return token
     ▼
┌──────────────────────────────┐
│  Frontend                    │
│  - Store token (localStorage)│
│  - Redirect to dashboard     │
└──────────────────────────────┘
```

### Login Flow

```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Enter email + password
     ▼
┌──────────────────┐
│  Frontend        │
└────┬─────────────┘
     │ 2. POST /auth/login
     ▼
┌──────────────────────────────┐
│  Backend                     │
│  1. Find user by email       │
│  2. Verify password hash     │
│  3. Generate JWT token       │
└────┬─────────────────────────┘
     │ 3. Return token
     ▼
┌──────────────────────────────┐
│  Frontend                    │
│  - Store token               │
│  - Set Authorization header  │
│  - Update UI (show username) │
└──────────────────────────────┘
```

---

## Data Models

### User Model

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    api_calls_count INTEGER DEFAULT 0
);
```

### Session Model (In-Memory)

```python
{
    "session_abc123": {
        "count": 3,              # Requests made
        "reset_time": "2025-...", # When limit resets
        "requests": [
            {
                "timestamp": "2025-...",
                "text_length": 150
            },
            ...
        ]
    }
}
```

---

## Security Layers

```
┌─────────────────────────────────────────────┐
│  Layer 1: CORS Protection                   │
│  - Only allow specific origins              │
│  - Prevent CSRF attacks                     │
└────┬────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────┐
│  Layer 2: Rate Limiting                     │
│  - Prevent abuse                            │
│  - DDoS mitigation                          │
└────┬────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────┐
│  Layer 3: Authentication                    │
│  - JWT token validation                     │
│  - User identification                      │
└────┬────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────┐
│  Layer 4: Input Validation                  │
│  - SQL injection prevention                 │
│  - XSS prevention                           │
│  - Text length limits                       │
└────┬────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────┐
│  Layer 5: Output Sanitization               │
│  - Safe file handling                       │
│  - Proper MIME types                        │
└─────────────────────────────────────────────┘
```

---

## File Structure (After Implementation)

```
fast_api/
├── main.py                          # Main FastAPI app
├── config.py                        # Configuration management
├── requirements.txt                 # Dependencies
│
├── middleware/
│   ├── __init__.py
│   ├── rate_limiter.py             # Rate limiting logic
│   └── auth_middleware.py          # Combined auth check
│
├── auth/
│   ├── __init__.py
│   ├── jwt_handler.py              # JWT operations
│   └── password_utils.py           # Password hashing
│
├── models/
│   ├── __init__.py
│   ├── user.py                     # User models
│   └── request_models.py           # API request models
│
├── database/
│   ├── __init__.py
│   ├── sqlite_db.py                # SQLite operations
│   └── postgres_db.py              # PostgreSQL operations
│
├── utils/
│   ├── __init__.py
│   ├── text_preprocessor.py        # Text preprocessing
│   └── logger.py                   # Logging utilities
│
├── routers/
│   ├── __init__.py
│   ├── auth_routes.py              # Authentication endpoints
│   ├── tts_routes.py               # TTS generation endpoints
│   └── voice_routes.py             # Voice management endpoints
│
├── tests/
│   ├── test_auth.py
│   ├── test_rate_limiter.py
│   ├── test_text_preprocessor.py
│   └── test_tts.py
│
├── data/
│   └── users.db                    # SQLite database
│
├── logs/
│   └── api.log                     # Application logs
│
└── static/
    ├── thumbnails/
    └── samples/
```

---

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt (passlib)
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **ORM**: SQLAlchemy (optional)

### Security
- **CORS**: FastAPI CORSMiddleware
- **Rate Limiting**: Custom implementation (or slowapi)
- **Token Storage**: Redis (optional, for distributed systems)

### TTS Engine
- **Model**: F5-TTS Base
- **Vocoder**: Vocos
- **Sample Rate**: 24kHz
- **Output Format**: WAV

---

## Deployment Architecture

```
┌─────────────────────────────────────────────┐
│  NGINX (Reverse Proxy)                      │
│  - SSL/TLS termination                      │
│  - Static file serving                      │
│  - Load balancing                           │
└────┬────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────┐
│  Gunicorn/Uvicorn Workers (x4)              │
│  - FastAPI application                      │
│  - Worker process pool                      │
└────┬────────────────────────────────────────┘
     │
     ├─────► PostgreSQL (User data)
     │
     ├─────► Redis (Rate limiting cache)
     │
     └─────► File System (Model, Audio)
```

---

**End of Architecture Diagram**
