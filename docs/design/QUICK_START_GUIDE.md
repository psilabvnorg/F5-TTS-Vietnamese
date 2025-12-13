# Quick Start Guide: Implementing API Requirements

**Target**: Implement security, authentication, and text preprocessing  
**Estimated Time**: 2-3 weeks  
**Difficulty**: Intermediate

---

## Prerequisites

- ✅ Existing F5-TTS Vietnamese API running
- ✅ Python 3.8+
- ✅ FastAPI knowledge
- ✅ Basic understanding of JWT and authentication
- ✅ Redis installed/running for rate limiting

---

## Step-by-Step Implementation

### Week 1: Security & Rate Limiting

#### Day 1-2: Setup Dependencies

**1. Update requirements.txt**

```bash
cd /home/psilab/F5-TTS-Vietnamese/fast_api
```

Add to `requirements.txt`:
```txt
# Existing
fastapi
uvicorn[standard]
pydantic

# New - Authentication
python-jose[cryptography]
passlib[bcrypt]
python-multipart

# New - Database
sqlalchemy

# New - Rate Limiting
redis
# starlette-limiter (optional)
```

**2. Install dependencies**

```bash
pip install -r requirements.txt

**3. Start Redis (development)**

```bash
# Linux
redis-server --daemonize yes

# Or via Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine
```
```

#### Day 3-4: Implement Rate Limiting

**1. Create middleware directory**

```bash
mkdir -p middleware
touch middleware/__init__.py
```

**2. Use Redis-backed limiter**

The codebase includes `middleware/rate_limiter_redis.py` using keys:
- `rl:{session_id}:count`
- `rl:{session_id}:reset` (24h window)

It is wired into `/tts/generate-audio` to enforce 5 requests/session and 1000-char limit.

**3. Test rate limiting (SSE endpoint)**

```bash
# Start server
./start.sh

# Test with curl
for i in {1..6}; do
  curl -i "http://localhost:8000/tts/generate-audio?text=hello&voice_id=tran_ha_linh&speed=1.0&cfg_strength=2.0&nfe_step=32"
done

# 6th request should return 429 Too Many Requests on the SSE handshake
```

#### Day 5: Add Rate Limit Headers

Update `/tts/generate-audio` to include response headers:
```python
response.headers["X-RateLimit-Limit"] = "5"
response.headers["X-RateLimit-Remaining"] = str(remaining)
response.headers["X-RateLimit-Reset"] = reset_time.isoformat()
```
Note: For SSE, these headers are sent on the initial HTTP response; the first event also includes `rate_limit` payload for UI display.

---

### Week 2: Authentication System

#### Day 1-2: Database Setup

**1. Create database directory**

```bash
mkdir -p database data
touch database/__init__.py
```

**2. Create sqlite_db.py**

```python
# See IMPLEMENTATION_PLAN.md for full code
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "users.db"

def init_database():
    # Create users table
    pass
```

**3. Initialize database**

```bash
python -c "from database.sqlite_db import init_database; init_database()"
```

#### Day 3-4: JWT Implementation

**1. Create auth directory**

```bash
mkdir -p auth
touch auth/__init__.py
```

**2. Create jwt_handler.py**

```python
from jose import jwt
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key"  # TODO: Move to .env
ALGORITHM = "HS256"

def create_access_token(data: dict):
    # See IMPLEMENTATION_PLAN.md
    pass

def verify_token(token: str):
    # See IMPLEMENTATION_PLAN.md
    pass
```

**3. Create models/user.py**

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
```

#### Day 5: Authentication Endpoints

**1. Add to main.py**

```python
@app.post("/auth/register")
async def register(user: UserCreate):
    # Hash password
    # Save to database
    # Generate JWT
    # Return token
    pass

@app.post("/auth/login")
async def login(credentials: UserLogin):
    # Verify password
    # Generate JWT
    # Return token
    pass

@app.get("/auth/me")
async def get_current_user(token: dict = Depends(verify_token)):
    # Return user info
    pass
```

**2. Test authentication**

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "username": "test", "password": "password123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Use token
TOKEN="<token from login>"
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

### Week 3: Text Preprocessing

#### Day 1-2: Implement Preprocessor

**1. Create utils directory**

```bash
mkdir -p utils
touch utils/__init__.py
```

**2. Create text_preprocessor.py**

Copy the full implementation from IMPLEMENTATION_PLAN.md:
- Vietnamese number conversion
- Special character removal
- Case conversion
- Period to comma replacement

#### Day 3: Integration

**1. Update TTS endpoint**

```python
from utils.text_preprocessor import text_preprocessor

@app.post("/tts/generate")
async def generate_tts(request: TTSRequest):
    # Preprocess text
    preprocessed = text_preprocessor.preprocess(
        request.text,
        convert_numbers=False  # Test first!
    )
    
    # Use preprocessed text for generation
    # ...
```

#### Day 4: Testing Endpoint

**1. Add test endpoint**

```python
@app.post("/utils/preprocess-text")
async def test_preprocess(text: str, convert_numbers: bool = False):
    result = text_preprocessor.preprocess(text, convert_numbers)
    return {
        "original": text,
        "preprocessed": result,
        "length": {
            "original": len(text),
            "preprocessed": len(result)
        }
    }
```

**2. Test preprocessing**

```bash
# Without number conversion
curl -X POST "http://localhost:8000/utils/preprocess-text?convert_numbers=false" \
  -H "Content-Type: application/json" \
  -d '"XIN CHÀO! Tôi có 5 táo."'

# With number conversion
curl -X POST "http://localhost:8000/utils/preprocess-text?convert_numbers=true" \
  -H "Content-Type: application/json" \
  -d '"XIN CHÀO! Tôi có 5 táo."'
```

#### Day 5: Quality Testing

**1. Generate samples with/without number conversion**

```bash
# Generate with numbers as-is
curl -X POST http://localhost:8000/tts/generate \
  -F "text=Tôi có 5 quả táo" \
  -F "voice=tran_ha_linh" \
  -o output_with_numbers.wav

# Generate with numbers converted
# (after enabling convert_numbers=true in code)
curl -X POST http://localhost:8000/tts/generate \
  -F "text=Tôi có 5 quả táo" \
  -F "voice=tran_ha_linh" \
  -o output_with_words.wav
```

**2. Compare audio quality**
- Listen to both files
- Have native speaker evaluate
- Decide whether to enable number conversion

---

## Configuration

### Create .env file

```bash
cd /home/psilab/F5-TTS-Vietnamese/fast_api
cat > .env << 'EOF'
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS (update with your frontend URL)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Rate Limiting
RATE_LIMIT_ANONYMOUS=5
RATE_LIMIT_CHAR_MAX=1000
REDIS_URL=redis://localhost:6379/0

# Database
DATABASE_URL=sqlite:///./data/users.db

# Text Preprocessing
CONVERT_NUMBERS_TO_WORDS=false
EOF
```

### Load environment variables

```python
# Add to config.py
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
CORS_ORIGINS = os.getenv("CORS_ORIGINS").split(",")
```

---

## Testing Checklist

### Manual Testing

- [ ] **Rate Limiting**
  - [ ] 5 anonymous requests work
  - [ ] 6th request returns 429
  - [ ] Authenticated requests unlimited
  - [ ] Character limit enforced (1001 chars = error)

- [ ] **Authentication**
  - [ ] Register new user
  - [ ] Login with correct password
  - [ ] Login with wrong password (should fail)
  - [ ] Access protected endpoint with token
  - [ ] Access protected endpoint without token (should fail)

- [ ] **Text Preprocessing**
  - [ ] Lowercase conversion works
  - [ ] Special characters removed
  - [ ] Periods → commas
  - [ ] Number conversion (test quality)

### Automated Testing

Create `tests/test_api.py`:

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_rate_limiting():
    for i in range(5):
        response = client.post("/tts/generate", json={
            "text": "test",
            "voice": "tran_ha_linh"
        })
        assert response.status_code == 200
    
    # 6th request should fail
    response = client.post("/tts/generate", json={
        "text": "test",
        "voice": "tran_ha_linh"
    })
    assert response.status_code == 429

def test_authentication():
    # Register
    response = client.post("/auth/register", json={
        "email": "test@test.com",
        "username": "test",
        "password": "password123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Use token
    response = client.get("/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
```

Run tests:
```bash
pytest tests/test_api.py -v
```

---

## Common Issues & Solutions

### Issue 1: "Module not found: jose"
**Solution**: Install dependencies
```bash
pip install python-jose[cryptography]
```

### Issue 2: "Database locked"
**Solution**: Use connection pooling or switch to PostgreSQL

### Issue 3: "CORS error in frontend"
**Solution**: Update CORS_ORIGINS in .env
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Issue 4: "Rate limit not resetting"
**Solution**: Check system time, add cleanup for expired sessions

### Issue 5: "JWT token expired"
**Solution**: Implement token refresh endpoint

---

## Frontend Integration Example

### React Component

```typescript
import React, { useState } from 'react';
import F5TTSAPI from './api/f5tts';

const api = new F5TTSAPI('http://localhost:8000');

function TTSGenerator() {
  const [text, setText] = useState('');
  const [audioUrl, setAudioUrl] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(api.isAuthenticated());

  const handleGenerate = async () => {
    try {
      const blob = await api.generateTTS({
        text,
        voice_id: 'tran_ha_linh',
        speed: 1.0
      });
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
    } catch (error) {
      if (error.message.includes('Rate limit')) {
        alert('You have reached your limit. Please login for unlimited access.');
      } else {
        alert('Error: ' + error.message);
      }
    }
  };

  const handleLogin = async () => {
    try {
      await api.login('user@example.com', 'password');
      setIsAuthenticated(true);
    } catch (error) {
      alert('Login failed');
    }
  };

  return (
    <div>
      {!isAuthenticated && (
        <button onClick={handleLogin}>Login for unlimited access</button>
      )}
      
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter text to synthesize..."
        maxLength={isAuthenticated ? 5000 : 1000}
      />
      
      <button onClick={handleGenerate}>Generate Speech</button>
      
      {audioUrl && (
        <audio controls src={audioUrl} />
      )}
    </div>
  );
}

export default TTSGenerator;
```

---

## Next Steps After Implementation

1. **Production Deployment**
   - Use PostgreSQL instead of SQLite
   - Set up Redis for rate limiting
   - Configure NGINX reverse proxy
   - Enable HTTPS with SSL certificate

2. **Monitoring & Analytics**
   - Log all API calls
   - Track usage per user
   - Monitor rate limit violations
   - Alert on errors

3. **Feature Enhancements**
   - Email verification for registration
   - Password reset functionality
   - Admin dashboard
   - Usage statistics for users

4. **Performance Optimization**
   - Cache preprocessed texts
   - Async TTS generation
   - CDN for static assets
   - Database query optimization

---

## Support & Documentation

- **Full Implementation Plan**: [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)
- **Architecture Diagram**: [ARCHITECTURE_DIAGRAM.md](./ARCHITECTURE_DIAGRAM.md)
- **API Documentation**: [API_DESIGN.md](./API_DESIGN.md)

---

**Ready to start? Begin with Week 1, Day 1!** 🚀
