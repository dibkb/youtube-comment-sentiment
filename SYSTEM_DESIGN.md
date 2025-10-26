# YouTube Comment Sentiment Analysis - System Design

## 📋 Overview

**BroTube** is a real-time sentiment analysis service for YouTube comments that provides sentiment classification (positive, negative, neutral) for video comments using Large Language Models (LLMs). The system is designed with performance, scalability, and cost-effectiveness in mind.

## 🎯 Core Objectives

1. **Real-time Sentiment Analysis**: Analyze YouTube comments in near-real-time
2. **Performance Optimization**: Minimize LLM API calls through intelligent caching
3. **Scalability**: Handle concurrent requests efficiently
4. **Cost Efficiency**: Reduce redundant API calls through Redis caching
5. **Observability**: Monitor system health with Prometheus metrics

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  (Web Frontend / Mobile App)                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                               │
│                    FastAPI Application                          │
│  ┌────────────────────────┐  ┌────────────────────────┐        │
│  │  Comment Sentiment     │  │   Video Search         │        │
│  │  Router                │  │   Router               │        │
│  │  - POST /comment-      │  │   - POST /videos/      │        │
│  │    sentiment/{video_id}│  │      search            │        │
│  │                        │  │   - GET /videos/       │        │
│  │                        │  │      info/{videoId}    │        │
│  │                        │  │   - GET /videos/       │        │
│  │                        │  │      trending-videos   │        │
│  └────────────────────────┘  └────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BUSINESS LOGIC LAYER                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Sentiment Analysis Module                               │  │
│  │  - Batch sentiment analysis with concurrency control  │  │
│  │  - Smart caching with pre-filtering                    │  │
│  │  - Pipeline-based Redis operations                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
┌────────────────────────┐    ┌────────────────────────┐
│   EXTERNAL SERVICES    │    │    CACHE LAYER          │
│                        │    │                         │
│  • YouTube Data API    │    │  • Redis (In-memory     │
│    v3                  │    │    cache)              │
│  • Groq API           │    │  • Cache Strategy:      │
│    (LLaMA 3.3)        │    │    - Full responses     │
│                        │    │    - Individual         │
│                        │    │      sentiments        │
│                        │    │  • TTL: 24 hours       │
└────────────────────────┘    └────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY LAYER                       │
│              Prometheus (Metrics Collection)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Technology Stack

### Core Framework

- **FastAPI**: High-performance async web framework
- **Python 3.11+**: Modern Python with type hints and async support

### AI/ML

- **LangChain**: LLM orchestration framework
- **Groq API**: High-speed LLM inference (LLaMA 3.3 70B)
- **Structured Output**: Pydantic models for reliable JSON responses

### External APIs

- **YouTube Data API v3**: Fetches video metadata and comments
- **Google API Python Client**: Official YouTube API wrapper

### Caching & Performance

- **Redis 7**: In-memory data store for multi-level caching
- **Pipeline Operations**: Bulk Redis operations for performance
- **Semaphore-based Concurrency**: Controlled parallel LLM requests

### Monitoring & Observability

- **Prometheus**: Metrics collection and aggregation
- **Prometheus FastAPI Instrumentator**: Auto-instrumented metrics

### Deployment

- **Docker & Docker Compose**: Containerization
- **Poetry**: Dependency management
- **Uvicorn**: ASGI server for production

---

## 📊 Data Models

### API Request/Response Models

```python
# Input
class CommentRequest(BaseModel):
    next_page_token: Optional[str] = None

class CleanedComment(BaseModel):
    id: str
    cleanedComment: str

# Output
class CommentSentiment(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
```

---

## 🔄 Request Flow

### 1. Comment Sentiment Analysis Flow

```
┌──────────────┐
│  Client POST  │
│  /comment-   │
│  sentiment/   │
│  {video_id}  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ Check Redis Cache for   │
│ complete response (hash) │
└──────┬───────────────────┘
       │
       ▼ (Cache Miss)
┌─────────────────────────────────┐
│ Fetch comments from YouTube API │
└──────┬──────────────────────────┘
       │
       ▼
┌───────────────────────────────────┐
│ Filter comments already analyzed  │
│ (Pre-filtering to skip cache)     │
└──────┬────────────────────────────┘
       │
       ▼
┌───────────────────────────────────┐
│ Batch Sentiment Analysis          │
│ • Concurrent LLM requests        │
│ • Semaphore-controlled (20 max)   │
│ • Store results in Redis          │
└──────┬────────────────────────────┘
       │
       ▼
┌───────────────────────────────────┐
│ Enrich comments with sentiment    │
│ (Pipeline bulk Redis reads)       │
└──────┬────────────────────────────┘
       │
       ▼
┌───────────────────────────────────┐
│ Cache complete response           │
│ (TTL: 24 hours)                   │
└──────┬────────────────────────────┘
       │
       ▼
┌──────────────┐
│ Return to    │
│ Client       │
└──────────────┘
```

### 2. Smart Caching Strategy

The system implements **multi-level caching** to minimize LLM API calls:

#### Level 1: Response Cache

- **Key**: SHA256 hash of `(video_id + page_token)`
- **Value**: Complete enriched response with sentiments
- **TTL**: 24 hours (86400 seconds)
- **Purpose**: Return cached results for repeated requests

#### Level 2: Individual Sentiment Cache

- **Key**: Comment ID
- **Storage**: Redis Hash (`comments` field)
- **Value**: Sentiment string ("positive", "negative", "neutral")
- **TTL**: Persistent until explicitly deleted
- **Purpose**: Reuse sentiment analysis across pages/videos

#### Cache Optimization Techniques:

1. **Pre-filtering**: Check which comments need analysis before LLM calls
2. **Pipeline Operations**: Bulk read/write to Redis for performance
3. **Batch Processing**: Process multiple comments concurrently
4. **Semaphore Control**: Limit concurrent LLM API calls (default: 20)

---

## 🚀 Performance Optimizations

### 1. **Concurrent Batch Processing**

```python
# Configurable batch size (default: 5)
# Max concurrent requests (default: 20)
semaphore = asyncio.Semaphore(min(len(comments_to_analyze), batch_size))
await asyncio.gather(*[analyze_sentiment(comment, semaphore) for comment in comments])
```

### 2. **Redis Pipeline Operations**

```python
# Bulk read sentiments from Redis
pipe = redis_client.pipeline()
for comment in comments:
    pipe.hget("comments", comment.id)
sentiments = pipe.execute()  # Single round-trip
```

### 3. **Pre-filtering Uncached Comments**

```python
# Only analyze comments not in cache
comments_to_analyze = [
    comment for i, comment in enumerate(comments)
    if not cache_results[i]
]
```

### 4. **Singleton Pattern**

- `YoutubeAPI`: Single connection to YouTube API
- `LanguageModel`: Single LLM client instance
- `RedisClient`: Single Redis connection

### 5. **Response Compression**

- JSON responses cached as strings
- Minimal overhead for repeated requests

---

## 🔍 API Endpoints

### Comment Sentiment Analysis

**Endpoint**: `POST /comment-sentiment/{video_id}`

- **Purpose**: Fetch and analyze sentiments for video comments
- **Parameters**: `next_page_token` (optional)
- **Returns**: Enriched comment response with sentiments
- **Caching**: Yes (24 hours)

### Video Search

**Endpoint**: `POST /videos/search`

- **Purpose**: Search for YouTube videos
- **Parameters**: `query` (search string)
- **Max Results**: 20 (configurable)
- **Caching**: Yes (24 hours)

**Endpoint**: `GET /videos/search-related`

- **Purpose**: Find related videos by title
- **Parameters**: `title`, `maxResults` (default: 5)
- **Caching**: Yes

**Endpoint**: `GET /videos/info/{videoId}`

- **Purpose**: Get detailed video information
- **Returns**: Video metadata, statistics, content details
- **Caching**: Yes

**Endpoint**: `GET /videos/trending-videos`

- **Purpose**: Get trending videos by country
- **Parameters**: `country` (default: "US"), `maxResults` (default: 8)
- **Caching**: Yes

---

## ⚙️ Configuration

### Settings (`app/settings.py`)

```python
# API Keys (from environment)
GROQ_API_KEY: str
YOUTUBE_API_KEY: str

# Application Configuration
MAX_RESULTS: int = 20              # Default comment results per page
MAX_RESULTS_SEARCH: int = 20       # Search results limit
MAX_RESULTS_RELATED: int = 5       # Related videos limit
MAX_RESULTS_TRENDING: int = 8      # Trending videos limit
MAX_CONCURRENT_REQUESTS: int = 20  # LLM concurrent request limit
REDIS_CACHE_EXPIRATION: int = 86400  # Cache TTL (24 hours)
BATCH_SIZE: int = 5                 # Sentiment analysis batch size
```

### Environment Variables

```bash
GROQ_API_KEY=<your_groq_key>
YOUTUBE_API_KEY=<your_youtube_key>
```

---

## 🐳 Deployment

### Development Environment

```yaml
# docker-compose-dev.yml
Services:
  - app: FastAPI with hot reload
  - redis: Cache layer
  - prometheus: Metrics collection
```

### Production Environment

```yaml
# docker-compose-prod.yml
Services:
  - app: Production image (dibkb/neo-tube-server:production)
  - redis: Persistent cache
  - prometheus: Production metrics
```

### Container Orchestration

- **Platform**: Multi-platform support (ARM64, AMD64)
- **Network**: Internal Docker network for service communication
- **Ports**:
  - App: `8000`
  - Redis: `6379`
  - Prometheus: `9090`

---

## 📈 Scalability Considerations

### Horizontal Scaling

- **Stateless API**: FastAPI app can be scaled horizontally
- **Redis**: Shared cache across instances (external Redis recommended for production)
- **Session Affinity**: Not required (no server-side sessions)

### Vertical Scaling

- **Concurrent Requests**: Configurable via `MAX_CONCURRENT_REQUESTS`
- **Batch Size**: Adjustable based on LLM API rate limits
- **Worker Processes**: Uvicorn supports multiple workers

### Potential Bottlenecks

1. **LLM API Rate Limits**: Mitigated by caching and semaphore control
2. **YouTube API Quota**: Reduced through Redis caching
3. **Redis Memory**: Monitor and implement eviction policies for production

---

## 🛡️ Error Handling

### API Error Responses

```python
# 500 Internal Server Error
{
    "error": "<error_message>"
}
```

### Graceful Degradation

- Cache misses fall back to API calls
- LLM errors logged but don't crash the application
- YouTube API errors return appropriate HTTP status codes

---

## 📊 Monitoring & Metrics

### Prometheus Integration

- **Auto-instrumentation**: All routes automatically instrumented
- **Metrics**: Request counts, latencies, error rates
- **Dashboard**: Accessible at `http://localhost:9090`

### Key Metrics Tracked

- Request duration by endpoint
- Request count by status code
- Active requests
- Cache hit/miss rates (via Redis monitoring)

---

## 🔐 Security Considerations

### CORS Configuration

- Whitelisted origins for frontend access
- Credentials allowed for authenticated requests

### Environment Security

- API keys stored in environment variables
- `.env` file not committed to version control
- Production uses separate credentials

---

## 🎯 Design Patterns Implemented

1. **Singleton Pattern**: Shared connections (YouTube API, LLM, Redis)
2. **Factory Pattern**: Client initialization factories
3. **Repository Pattern**: Encapsulated data access (Redis cache)
4. **Dependency Injection**: FastAPI routers and services
5. **Pipeline Pattern**: Bulk Redis operations

---

## 🚦 Future Enhancements

### Potential Improvements

1. **Message Queue Integration**: RabbitMQ/Kafka for async sentiment processing
2. **Database Layer**: PostgreSQL for persistent sentiment storage
3. **Rate Limiting**: Protect API from abuse
4. **Authentication**: API key management for client access
5. **Sentiment Analytics**: Aggregate sentiment trends over time
6. **WebSocket Support**: Real-time sentiment updates
7. **Multi-language Support**: Language detection before analysis
8. **Sentiment Confidence Scores**: LLM confidence metrics

### Infrastructure

- **Load Balancer**: NGINX for multiple app instances
- **Database**: PostgreSQL for audit logs and analytics
- **CDN**: CloudFlare for static assets
- **CI/CD**: Automated testing and deployment

---

## 📝 Code Quality

- **Linting**: Ruff for code formatting and linting
- **Type Hints**: Full Python type annotations
- **Documentation**: Docstrings and inline comments
- **Error Handling**: Try-catch blocks with graceful failures

---

## 🧪 Testing Strategy

### Recommended Tests

1. **Unit Tests**: Individual function tests
2. **Integration Tests**: API endpoint testing
3. **Performance Tests**: Load testing with concurrent requests
4. **Cache Tests**: Verify cache hit/miss logic
5. **Mock Tests**: Mock external API calls

### Testing Tools

- `pytest`: Testing framework
- `httpx`: Async HTTP client for API testing
- `fakeredis`: Redis mock for testing

---

## 📚 Dependencies

### Production Dependencies

```toml
fastapi[standard] >=0.115.12
langchain-groq >=0.3.2
google-api-python-client >=2.167.0
redis >=5.2.1
prometheus-fastapi-instrumentator >=7.1.0
pydantic-settings >=2.9.1
```

### Build System

- **Poetry**: Dependency management
- **Python**: >=3.11, <4.0

---

## 🎬 Conclusion

This system is designed for **performance**, **scalability**, and **cost efficiency**:

- **Smart caching** reduces redundant API calls
- **Concurrent processing** handles multiple requests efficiently
- **Modular architecture** allows easy extension
- **Production-ready** with monitoring and error handling

The architecture supports horizontal scaling and can handle high traffic volumes with intelligent caching and batch processing.
