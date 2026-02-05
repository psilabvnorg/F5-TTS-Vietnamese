# Implementation Plan: API Requirements

**Date**: December 13, 2025  
**Project**: F5-TTS Vietnamese API  
**Version**: 2.0.0

---

## Executive Summary

This document outlines the implementation strategy for three core requirements:
1. **Security & Rate Limiting**: Token-based authentication with session-based rate limiting
2. **Frontend Integration**: CORS configuration and API design for seamless frontend connectivity
3. **Text Preprocessing**: Automated text normalization for Vietnamese TTS generation

---

## 1. Security & Rate Limiting

### 1.1 Architecture Overview

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Middleware Layer   │
├─────────────────────┤
│ 1. CORS Handler     │
│ 2. Rate Limiter     │
│ 3. Auth Validator   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  API Endpoints      │
└─────────────────────┘
```

### 1.2 Components to Implement

#### A. Session-Based Rate Limiting (Anonymous Users)
**Requirements:**
- 5 requests per session
- 1,000 character limit per request
- No authentication required

**Implementation Strategy (Redis-backed):**
```python
# File: fast_api/middleware/rate_limiter_redis.py

from fastapi import Request, HTTPException
import time, os, redis
from datetime import datetime

DEFAULT_LIMIT = int(os.getenv("RATE_LIMIT_ANONYMOUS", "5"))
CHAR_MAX = int(os.getenv("RATE_LIMIT_CHAR_MAX", "1000"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class RedisRateLimiter:
    """Redis-backed limiter using 24h window per session (IP+UA)."""
    def __init__(self):
        self.r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        self.window_seconds = 24 * 60 * 60

    def get_session_id(self, request: Request) -> str:
        return f"{request.client.host}:{request.headers.get('user-agent','')}"

    def _keys(self, sid: str):
        base = f"rl:{sid}"
        return {"count": f"{base}:count", "reset": f"{base}:reset"}

    def check(self, session_id: str, text_len: int):
        if text_len > CHAR_MAX:
            raise HTTPException(status_code=400, detail=f"Text exceeds {CHAR_MAX} characters")
        keys = self._keys(session_id)
        now_ts = int(time.time())
        if not self.r.exists(keys["count"]):
            self.r.set(keys["count"], 0, ex=self.window_seconds)
            self.r.set(keys["reset"], now_ts + self.window_seconds, ex=self.window_seconds)
        count, reset_ts = self.r.pipeline().incr(keys["count"]).get(keys["reset"]).execute()
        if int(count) > DEFAULT_LIMIT:
            reset_iso = datetime.utcfromtimestamp(int(reset_ts)).isoformat()+"Z"
            raise HTTPException(status_code=429, detail="Rate limit exceeded (5/session)", headers={
                "X-RateLimit-Limit": str(DEFAULT_LIMIT),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": reset_iso
            })
        remaining = max(0, DEFAULT_LIMIT - int(count))
        return {"remaining": remaining, "reset_iso": datetime.utcfromtimestamp(int(reset_ts)).isoformat()+"Z"}
```

**Usage in FastAPI (SSE route):**
```python
from middleware.rate_limiter_redis import RedisRateLimiter
rate_limiter = RedisRateLimiter()

@app.get("/tts/generate-audio")
async def tts_generate_audio(..., session_id: str = Depends(get_session_id)):
    rate_info = rate_limiter.check(session_id, len(text))
    # Include headers on SSE response and rate info in first event
```

#### B. Token-Based Authentication (Registered Users)
**Requirements:**
- JWT-based authentication
- Unlimited requests for authenticated users
- User management (registration, login, logout)

**Implementation Strategy:**
```python
# File: fast_api/auth/jwt_handler.py

from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = "your-secret-key-here"  # TODO: Move to environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

def hash_password(password: str):
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)
```

**Database Schema:**
```python
# File: fast_api/models/user.py

from pydantic import BaseModel, EmailStr
from datetime import datetime

class User(BaseModel):
    id: int
    email: EmailStr
    username: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime
    api_calls_count: int = 0

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

**Authentication Endpoints:**
```python
# File: fast_api/main.py

@app.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    """
    Register a new user
    - Check if email exists
    - Hash password
    - Create user in database
    - Return JWT token
    """
    # TODO: Implement database operations
    pass

@app.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Login user
    - Verify email and password
    - Generate JWT token
    - Return token
    """
    # TODO: Implement authentication
    pass

@app.get("/auth/me")
async def get_current_user(token_payload: dict = Depends(verify_token)):
    """Get current authenticated user details"""
    # TODO: Fetch user from database
    pass
```

#### C. Enhanced Rate Limiting Middleware
```python
# File: fast_api/middleware/auth_middleware.py

from fastapi import Request, HTTPException
from auth.jwt_handler import verify_token

async def check_auth_and_rate_limit(request: Request):
    """
    Combined middleware for authentication and rate limiting
    - If Authorization header present: verify token, allow unlimited
    - If no auth: apply session-based rate limiting
    """
    auth_header = request.headers.get("Authorization")
    
    if auth_header:
        try:
            # Authenticated user - no rate limit
            token_payload = verify_token_from_header(auth_header)
            return {
                "authenticated": True,
                "user_id": token_payload.get("sub"),
                "rate_limited": False
            }
        except HTTPException:
            # Invalid token, fall back to rate limiting
            pass
    
    # Anonymous user - apply rate limiting
    session_id = rate_limiter.get_session_id(request)
    return {
        "authenticated": False,
        "session_id": session_id,
        "rate_limited": True
    }
```

### 1.3 Database Setup

**Option 1: SQLite (Simple, for development)**
```python
# File: fast_api/database/sqlite_db.py

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "users.db"

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            api_calls_count INTEGER DEFAULT 0
        )
    """)
    
    conn.commit()
    conn.close()
```

**Option 2: PostgreSQL (Production-ready)**
```python
# File: fast_api/database/postgres_db.py

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "postgresql://user:password@localhost/f5tts_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    api_calls_count = Column(Integer, default=0)

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 1.4 Required Dependencies

```txt
# Add to fast_api/requirements.txt

# Existing
fastapi
uvicorn[standard]
pydantic

# New dependencies for authentication
python-jose[cryptography]  # JWT handling
passlib[bcrypt]            # Password hashing
python-multipart           # Form data parsing
sqlalchemy                 # ORM (optional, for PostgreSQL)
psycopg2-binary            # PostgreSQL driver (optional)

# For rate limiting
redis                      # Required for Redis-backed limiter
slowapi                    # Optional alternative
```

---

## 2. Frontend Integration

### 2.1 Current CORS Configuration
✅ Already implemented in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2.2 Production CORS Configuration
```python
# File: fast_api/config.py

import os
from typing import List

class Settings:
    PROJECT_NAME: str = "F5-TTS Vietnamese API"
    VERSION: str = "2.0.0"
    
    # CORS settings
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173"  # React, Vite defaults
    ).split(",")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    
    # Rate limiting
    RATE_LIMIT_ANONYMOUS: int = 5
    RATE_LIMIT_CHAR_MAX: int = 1000

settings = Settings()
```

```python
# Update main.py
from config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2.3 Frontend API Client Example

**TypeScript/React Example:**
```typescript
// File: frontend/src/api/f5tts.ts

interface TTSRequest {
  text: string;
  voice_id: string;
  speed?: number;
}

class F5TTSAPI {
  private baseURL: string;
  private token: string | null;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('f5tts_token');
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    return headers;
  }

  async generateTTS(request: TTSRequest): Promise<Blob> {
    const response = await fetch(`${this.baseURL}/tts/generate`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'TTS generation failed');
    }

    // Check rate limit headers
    const remaining = response.headers.get('X-RateLimit-Remaining');
    if (remaining !== null && parseInt(remaining) === 0) {
      console.warn('Rate limit reached. Please login for unlimited access.');
    }

    return response.blob();
  }

  async login(email: string, password: string): Promise<void> {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();
    this.token = data.access_token;
    localStorage.setItem('f5tts_token', data.access_token);
  }

  async register(email: string, username: string, password: string): Promise<void> {
    const response = await fetch(`${this.baseURL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, username, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    const data = await response.json();
    this.token = data.access_token;
    localStorage.setItem('f5tts_token', data.access_token);
  }

  logout(): void {
    this.token = null;
    localStorage.removeItem('f5tts_token');
  }

  isAuthenticated(): boolean {
    return this.token !== null;
  }
}

export default F5TTSAPI;
```

### 2.4 Response Headers for Frontend
```python
# Add to all TTS endpoints
from fastapi.responses import JSONResponse

@app.post("/tts/generate")
async def generate_tts(...):
    # ... generation logic ...
    
    return JSONResponse(
        content={...},
        headers={
            "X-RateLimit-Limit": "5",
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": reset_time.isoformat(),
            "X-Authenticated": "true" if authenticated else "false"
        }
    )
```

---

## 3. Text Preprocessing

### 3.1 Requirements
1. ✅ Remove special characters
2. ⚠️ Convert numbers to words (needs testing)
3. ✅ Replace periods (.) with commas (,)
4. ✅ Convert uppercase to lowercase

### 3.2 Implementation

```python
# File: fast_api/utils/text_preprocessor.py

import re
from typing import Dict
import unicodedata

class VietnameseTextPreprocessor:
    """
    Text preprocessing for Vietnamese TTS generation
    
    Features:
    - Remove special characters
    - Convert numbers to Vietnamese words
    - Replace periods with commas
    - Convert to lowercase
    """
    
    def __init__(self):
        # Vietnamese number words
        self.ones = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
        self.tens = ["", "mười", "hai mươi", "ba mươi", "bốn mươi", "năm mươi", 
                     "sáu mươi", "bảy mươi", "tám mươi", "chín mươi"]
        
        # Scale names
        self.scales = {
            1000000000: "tỷ",
            1000000: "triệu",
            1000: "nghìn",
            100: "trăm"
        }
    
    def remove_special_characters(self, text: str) -> str:
        """
        Remove special characters while preserving Vietnamese diacritics
        Keep: letters, numbers, spaces, commas, Vietnamese characters
        """
        # Keep Vietnamese characters, alphanumeric, spaces, and commas
        pattern = r'[^\w\s,àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]'
        text = re.sub(pattern, '', text)
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def number_to_words(self, num: int) -> str:
        """
        Convert integer to Vietnamese words
        Examples:
          1 -> "một"
          15 -> "mười lăm"
          100 -> "một trăm"
          1234 -> "một nghìn hai trăm ba mươi bốn"
        """
        if num == 0:
            return "không"
        
        if num < 0:
            return "âm " + self.number_to_words(abs(num))
        
        if num < 10:
            return self.ones[num]
        
        if num < 20:
            if num == 10:
                return "mười"
            elif num == 15:
                return "mười lăm"
            else:
                return "mười " + self.ones[num % 10]
        
        if num < 100:
            tens = num // 10
            ones = num % 10
            result = self.tens[tens]
            if ones > 0:
                if ones == 5:
                    result += " lăm"
                elif ones == 1 and tens > 1:
                    result += " mốt"
                else:
                    result += " " + self.ones[ones]
            return result
        
        # Handle larger numbers
        for scale_value, scale_name in sorted(self.scales.items(), reverse=True):
            if num >= scale_value:
                quotient = num // scale_value
                remainder = num % scale_value
                
                result = self.number_to_words(quotient) + " " + scale_name
                
                if remainder > 0:
                    if remainder < 10:
                        result += " lẻ"
                    result += " " + self.number_to_words(remainder)
                
                return result
        
        return str(num)  # Fallback
    
    def convert_numbers_in_text(self, text: str) -> str:
        """
        Find and convert all numbers in text to words
        Examples:
          "Tôi có 5 quả táo" -> "Tôi có năm quả táo"
          "Năm 2024" -> "Năm hai nghìn không trăm hai mươi bốn"
        """
        def replace_number(match):
            num_str = match.group(0)
            try:
                num = int(num_str)
                return self.number_to_words(num)
            except ValueError:
                return num_str
        
        # Find all numbers (including those with commas like 1,234)
        text = re.sub(r'\d[\d,]*', lambda m: replace_number(
            re.match(r'\d+', m.group(0).replace(',', ''))
        ), text)
        
        return text
    
    def replace_periods(self, text: str) -> str:
        """Replace periods with commas"""
        return text.replace('.', ',')
    
    def to_lowercase(self, text: str) -> str:
        """Convert text to lowercase"""
        return text.lower()
    
    def preprocess(self, text: str, convert_numbers: bool = False) -> str:
        """
        Full preprocessing pipeline
        
        Args:
            text: Input text
            convert_numbers: Whether to convert numbers to words (default: False)
                            Set to False initially for testing
        
        Returns:
            Preprocessed text ready for TTS
        """
        # Step 1: Convert to lowercase first
        text = self.to_lowercase(text)
        
        # Step 2: Replace periods with commas
        text = self.replace_periods(text)
        
        # Step 3: Convert numbers to words (optional, needs testing)
        if convert_numbers:
            text = self.convert_numbers_in_text(text)
        
        # Step 4: Remove special characters
        text = self.remove_special_characters(text)
        
        # Step 5: Final cleanup
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

# Create singleton instance
text_preprocessor = VietnameseTextPreprocessor()
```

### 3.3 Integration into API

```python
# Update fast_api/main.py

from utils.text_preprocessor import text_preprocessor

@app.post("/tts/generate")
async def generate_tts(request: TTSRequest):
    """
    Generate TTS with automatic text preprocessing
    """
    # Preprocess text
    preprocessed_text = text_preprocessor.preprocess(
        request.text,
        convert_numbers=False  # Start with False, enable after testing
    )
    
    # Log original vs preprocessed for monitoring
    print(f"Original: {request.text}")
    print(f"Preprocessed: {preprocessed_text}")
    
    # Use preprocessed text for generation
    # ... rest of TTS generation code ...
```

### 3.4 Testing Endpoint

```python
@app.post("/utils/preprocess-text")
async def preprocess_text_endpoint(
    text: str,
    convert_numbers: bool = False
):
    """
    Test endpoint for text preprocessing
    
    Example:
    {
        "text": "XIN CHÀO! Tôi có 5 quả táo. Giá 1,000 VNĐ.",
        "convert_numbers": true
    }
    
    Returns:
    {
        "original": "XIN CHÀO! Tôi có 5 quả táo. Giá 1,000 VNĐ.",
        "preprocessed": "xin chào, tôi có năm quả táo, giá một nghìn vnd",
        "steps": {
            "lowercase": "xin chào! tôi có 5 quả táo. giá 1,000 vnĐ.",
            "replace_periods": "xin chào! tôi có 5 quả táo, giá 1,000 vnĐ,",
            "convert_numbers": "xin chào! tôi có năm quả táo, giá một nghìn vnĐ,",
            "remove_special": "xin chào tôi có năm quả táo giá một nghìn vnđ"
        }
    }
    """
    preprocessed = text_preprocessor.preprocess(text, convert_numbers)
    
    return {
        "original": text,
        "preprocessed": preprocessed,
        "convert_numbers_enabled": convert_numbers,
        "character_count": {
            "original": len(text),
            "preprocessed": len(preprocessed)
        }
    }
```

### 3.5 Testing Plan for Number Conversion

```python
# File: fast_api/tests/test_text_preprocessor.py

import pytest
from utils.text_preprocessor import VietnameseTextPreprocessor

def test_number_conversion():
    preprocessor = VietnameseTextPreprocessor()
    
    test_cases = [
        ("1", "một"),
        ("5", "năm"),
        ("10", "mười"),
        ("15", "mười lăm"),
        ("21", "hai mươi mốt"),
        ("100", "một trăm"),
        ("1000", "một nghìn"),
        ("1234", "một nghìn hai trăm ba mươi bốn"),
        ("2024", "hai nghìn không trăm hai mươi bốn"),
    ]
    
    for number_str, expected in test_cases:
        result = preprocessor.number_to_words(int(number_str))
        print(f"{number_str} -> {result}")
        assert result == expected, f"Failed for {number_str}"

def test_preprocessing():
    preprocessor = VietnameseTextPreprocessor()
    
    test_cases = [
        {
            "input": "XIN CHÀO! Tôi có 5 quả táo.",
            "convert_numbers": False,
            "expected": "xin chào, tôi có 5 quả táo,"
        },
        {
            "input": "XIN CHÀO! Tôi có 5 quả táo.",
            "convert_numbers": True,
            "expected": "xin chào, tôi có năm quả táo,"
        },
        {
            "input": "Giá: 1,000 VNĐ!!!",
            "convert_numbers": True,
            "expected": "giá: một nghìn vnđ"
        }
    ]
    
    for case in test_cases:
        result = preprocessor.preprocess(
            case["input"], 
            convert_numbers=case["convert_numbers"]
        )
        print(f"Input: {case['input']}")
        print(f"Output: {result}")
        print(f"Expected: {case['expected']}")
        print()

if __name__ == "__main__":
    test_number_conversion()
    test_preprocessing()
```

**Testing Strategy:**
1. **Phase 1**: Test with `convert_numbers=False` (default)
   - Verify basic preprocessing works
   - Check TTS quality
   
2. **Phase 2**: Test with `convert_numbers=True`
   - Generate samples with numbers
   - Compare audio quality
   - Check if Vietnamese number pronunciation is natural
   
3. **Phase 3**: A/B comparison
   - Generate same text with/without number conversion
   - Have native speakers evaluate naturalness

---

## 4. Implementation Sequence

### Phase 1: Security Foundation (Week 1)
1. ✅ Implement session-based rate limiter
2. ✅ Add character limit validation
3. ✅ Add rate limit headers to responses
4. ✅ Test rate limiting with multiple requests

### Phase 2: Authentication System (Week 2)
1. ✅ Set up database (SQLite for dev, PostgreSQL for prod)
2. ✅ Implement user registration endpoint
3. ✅ Implement user login endpoint
4. ✅ Implement JWT token generation/validation
5. ✅ Create protected endpoints
6. ✅ Test authentication flow

### Phase 3: Text Preprocessing (Week 1)
1. ✅ Implement text preprocessor class
2. ✅ Integrate into TTS endpoint
3. ✅ Create testing endpoint
4. ⚠️ Test number conversion (evaluate quality)
5. ✅ Deploy with `convert_numbers=False` initially

### Phase 4: Frontend Integration (Week 1)
1. ✅ Update CORS configuration
2. ✅ Document API client implementation
3. ✅ Create example frontend integration
4. ✅ Test end-to-end flow

### Phase 5: Testing & Deployment (Week 2)
1. ✅ Integration testing
2. ✅ Load testing (rate limiting under stress)
3. ✅ Security audit
4. ✅ Documentation update
5. ✅ Production deployment

---

## 5. API Endpoint Updates

### New Endpoints to Add

```python
# Authentication
POST   /auth/register          # Register new user
POST   /auth/login             # Login user
GET    /auth/me                # Get current user
POST   /auth/logout            # Logout (invalidate token)
POST   /auth/refresh           # Refresh access token

# Utilities
POST   /utils/preprocess-text  # Test text preprocessing

# Enhanced TTS
POST   /tts/generate           # Generate TTS (with auth support)
GET    /user/usage             # Get user API usage stats
```

### Updated Response Schema

```python
# All TTS responses now include:
{
  "status": "success",
  "data": {
    "audio_url": "...",
    "duration": 15.5
  },
  "rate_limit": {
    "authenticated": false,
    "remaining": 3,
    "reset_at": "2025-12-13T12:00:00Z"
  },
  "preprocessing": {
    "original_length": 150,
    "preprocessed_length": 145,
    "numbers_converted": false
  }
}
```

---

## 6. Environment Variables

```bash
# File: fast_api/.env

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://yourdomain.com

# Rate Limiting
RATE_LIMIT_ANONYMOUS=5
RATE_LIMIT_CHAR_MAX=1000

# Database
DATABASE_URL=sqlite:///./data/users.db
# DATABASE_URL=postgresql://user:password@localhost/f5tts_db

# Text Preprocessing
CONVERT_NUMBERS_TO_WORDS=false  # Enable after testing

# Redis (optional, for distributed rate limiting)
# REDIS_URL=redis://localhost:6379
```

---

## 7. Documentation Updates Needed

1. **API_DESIGN.md**: Add authentication section
2. **README.md**: Add setup instructions for new dependencies
3. **DEPLOYMENT.md**: Add environment variable configuration
4. **CLIENT_EXAMPLES.md**: Add TypeScript/JavaScript client examples

---

## 8. Security Considerations

### 8.1 Password Security
- ✅ Use bcrypt for password hashing
- ✅ Minimum password length: 8 characters
- ✅ Require at least one number and special character
- ✅ Rate limit login attempts (max 5 per 15 minutes per IP)

### 8.2 JWT Security
- ✅ Use strong SECRET_KEY (256-bit minimum)
- ✅ Set reasonable token expiration (7 days default)
- ✅ Implement token refresh mechanism
- ✅ Store tokens securely in frontend (httpOnly cookies preferred)

### 8.3 CORS Security
- ⚠️ Change `allow_origins=["*"]` to specific domains in production
- ✅ Keep `allow_credentials=True` only if using cookies

### 8.4 Rate Limiting Security
- ✅ Use IP + User-Agent for session identification
- ✅ Consider adding CAPTCHA for repeated violations
- ✅ Log rate limit violations for monitoring

---

## 9. Monitoring & Logging

```python
# File: fast_api/utils/logger.py

import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("f5tts_api")

def log_request(user_id: str, endpoint: str, status: str, details: dict):
    """Log API request"""
    logger.info(f"User: {user_id} | Endpoint: {endpoint} | Status: {status} | Details: {details}")

def log_rate_limit_violation(session_id: str, ip: str):
    """Log rate limit violations"""
    logger.warning(f"Rate limit exceeded | Session: {session_id} | IP: {ip}")

def log_auth_failure(email: str, ip: str):
    """Log authentication failures"""
    logger.warning(f"Auth failed | Email: {email} | IP: {ip}")
```

---

## 10. Testing Checklist

### Security Testing
- [ ] Test rate limiting with 5+ requests
- [ ] Test character limit (1000 chars)
- [ ] Test invalid JWT tokens
- [ ] Test expired JWT tokens
- [ ] Test SQL injection attempts
- [ ] Test XSS attempts in text input

### Functional Testing
- [ ] Test text preprocessing with various inputs
- [ ] Test number conversion accuracy
- [ ] Test with/without authentication
- [ ] Test CORS from different origins
- [ ] Test all API endpoints

### Performance Testing
- [ ] Load test with 100 concurrent users
- [ ] Test rate limiter performance
- [ ] Test database query performance
- [ ] Monitor memory usage

---

## Next Steps

1. **Review this plan** with team
2. **Prioritize phases** based on business needs
3. **Set up development environment** with new dependencies
4. **Begin Phase 1 implementation** (Security Foundation)
5. **Create test suite** for each component
6. **Document as you build** - update API_DESIGN.md

---

## Questions to Resolve

1. **Database choice**: SQLite (simple) or PostgreSQL (scalable)?
2. **Number conversion**: Should we enable by default or make it optional?
3. **Token expiration**: 7 days or custom per user?
4. **Frontend framework**: React, Vue, or other?
5. **Deployment platform**: Local server, Docker, or cloud (AWS/GCP)?

---

**End of Implementation Plan**
