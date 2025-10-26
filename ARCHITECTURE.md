# Architecture Overview - BroTube

## 📐 System Components

### 1. Application Structure

```
youtube-comment-sentiment/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── models.py               # Pydantic data models
│   ├── analyze.py              # Sentiment analysis logic
│   ├── llm.py                  # Groq LLM client (Singleton)
│   ├── youtube_api.py         # YouTube API client (Singleton)
│   ├── redis.py               # Redis client (Singleton)
│   ├── settings.py             # Configuration & environment
│   └── routers/
│       ├── comment_sentiment.py  # Comment sentiment endpoints
│       └── videos.py           # Video search endpoints
├── docker-compose-dev.yml     # Development environment
├── docker-compose-prod.yml    # Production environment
├── Dockerfile.prod             # Production Docker image
└── pyproject.toml             # Poetry dependencies
```

---

## 🔄 Data Flow Diagrams

### End-to-End Request Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLIENT REQUEST                             │
│                      POST /comment-sentiment/{video_id}             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  FastAPI Router │
                    │  (comment_      │
                    │   sentiment.py) │
                    └────────┬────────┘
                             │
                             ▼
                 ┌──────────────────────────┐
                 │  Generate Cache Key       │
                 │  SHA256(video_id + token) │
                 └───────────┬───────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Redis Lookup   │
                    │  Cache Check    │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
             Cache Hit         Cache Miss
                    │                 │
                    ▼                 ▼
            ┌─────────────┐   ┌────────────────┐
            │  Return     │   │  YouTube API   │
            │  Cached     │   │  Call          │
            │  Response   │   └───────┬────────┘
            └─────────────┘           │
                                     ▼
                          ┌──────────────────┐
                          │  Extract Comment │
                          │  IDs & Text      │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌───────────────────┐
                          │  Pre-filter Cache│
                          │  Check per comment│
                          └────────┬──────────┘
                                   │
                                   ▼
                          ┌───────────────────┐
                          │  Filter Uncached  │
                          │  Comments         │
                          └────────┬──────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │  Batch Sentiment │
                          │  Analysis        │
                          │  (Concurrent)    │
                          └────────┬─────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
          ┌──────────────────┐      ┌──────────────────────┐
          │  Groq API        │      │  Semaphore Control   │
          │  (LLaMA 3.3)     │      │  (Max 20 concurrent)│
          └────────┬─────────┘      └──────────────────────┘
                   │
                   ▼
          ┌──────────────────┐
          │  Process Results │
          │  Store in Redis  │
          └─────────┬────────┘
                    │
                    ▼
          ┌──────────────────┐
          │  Redis Pipeline   │
          │  Bulk Read        │
          │  Sentiments       │
          └─────────┬─────────┘
                    │
                    ▼
          ┌──────────────────┐
          │  Enrich Comments │
          │  with Sentiments │
          └─────────┬────────┘
                    │
                    ▼
          ┌──────────────────┐
          │  Cache Full      │
          │  Response        │
          │  (TTL: 24h)      │
          └─────────┬────────┘
                    │
                    ▼
          ┌──────────────────┐
          │  Return to Client │
          └───────────────────┘
```

---

## 🏗️ Component Architecture

### Core Services (Singleton Pattern)

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  FastAPI App (main.py)                                 │ │
│  │  • CORS Middleware                                     │ │
│  │  • Prometheus Instrumentation                          │ │
│  │  • Router Integration                                  │ │
│  └──────────────────┬────────────────────────────────────┘ │
│                     │                                       │
│  ┌──────────────────┴──────────────────────────┐          │
│  │          ROUTER LAYER                        │          │
│  │  ┌──────────────────┐  ┌──────────────────┐ │          │
│  │  │ comment_sentiment│  │      videos      │ │          │
│  │  │ /comment-        │  │ • /search        │ │          │
│  │  │  sentiment/{id}  │  │ • /info/{id}     │ │          │
│  │  │                  │  │ • /search-       │ │          │
│  │  │                  │  │   related        │ │          │
│  │  │                  │  │ • /trending-     │ │          │
│  │  │                  │  │   videos         │ │          │
│  │  └──────────────────┘  └──────────────────┘ │          │
│  └──────────────┬─────────────────┬────────────┘          │
└─────────────────┼─────────────────┼───────────────────────┘
                  │                 │
                  ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                  BUSINESS LOGIC LAYER                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  analyze.py (Sentiment Analysis)                       │ │
│  │  • analyze_sentiment() - Single comment analysis       │ │
│  │  • batch_analyze_sentiments() - Batch processing       │ │
│  │  • Pre-filtering logic                                 │ │
│  │  • Pipeline operations                                  │ │
│  └──────────────┬────────────────────────────────────────┘ │
└─────────────────┼──────────────────────────────────────────┘
                  │
        ┌─────────┼─────────┬─────────────────┐
        │         │         │                 │
        ▼         ▼         ▼                 ▼
┌─────────────┐ ┌──────┐ ┌──────────┐ ┌─────────────┐
│  YouTube    │ │ LLM  │ │  Redis   │ │ Prometheus  │
│  API Client │ │ (Groq│ │  Client  │ │ Monitoring  │
│  (Singleton)│ │ API) │ │          │ │             │
│             │ │      │ │          │ │             │
│  • Build    │ │ • LLa│ │ • Cache  │ │ • Metrics   │
│    YouTube  │ │   MA │ │   Layer  │ │   Export    │
│    client   │ │   3.3│ │ • Hash   │ │ • Auto      │
│  • Reuse    │ │      │ │   Storage│ │   Instrument│
│    instance │ │ • 70B│ │ • 24h TTL│ │             │
│             │ │      │ │ • Pipeline│└─────────────┘
└─────────────┘ └──────┘ └──────────┘
```

---

## 🎯 Design Patterns

### 1. Singleton Pattern

**Implementation**: Thread-safe singleton for shared resources

```python
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            # Initialize once
            self.initialized = True
```

**Used in**:

- `YoutubeAPI`: Single YouTube API connection
- `LanguageModel`: Single Groq LLM client
- `RedisClient`: Single Redis connection

**Benefits**:

- Connection reuse
- Reduced initialization overhead
- Memory efficiency

---

### 2. Batch Processing Pattern

**Implementation**: Concurrent batch processing with semaphore control

```python
async def batch_analyze_sentiments(comments, batch_size):
    # Pre-filter cached comments
    comments_to_analyze = filter_uncached(comments)

    # Process with concurrency limit
    semaphore = asyncio.Semaphore(batch_size)
    await asyncio.gather(
        *[analyze_sentiment(c, semaphore) for c in comments_to_analyze]
    )
```

**Benefits**:

- Controlled concurrency
- Efficient resource usage
- Configurable batch sizes

---

### 3. Cache-Aside Pattern

**Implementation**: Multi-level caching with pre-filtering

```python
# Level 1: Check full response cache
cached = redis.get(full_response_key)
if cached:
    return cached

# Level 2: Check individual sentiment cache
uncached = filter_cached_comments(comments)

# Level 3: Process only uncached
results = await batch_analyze(uncached)

# Store in both caches
store_individual(results)
store_full_response(results)
```

**Benefits**:

- Maximize cache hits
- Minimize LLM API calls
- Configurable TTL per cache level

---

### 4. Pipeline Pattern (Redis)

**Implementation**: Bulk Redis operations

```python
# Bulk read sentiments
pipe = redis.pipeline()
for comment in comments:
    pipe.hget("comments", comment.id)
sentiments = pipe.execute()  # Single round-trip
```

**Benefits**:

- Reduced network latency
- Batch operations
- Atomic execution

---

## 🔍 Cache Strategy

### Multi-Level Caching

```
┌──────────────────────────────────────────────────────────┐
│                    CACHE LAYERS                            │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Layer 1: Full Response Cache                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Key: SHA256(video_id + page_token)               │   │
│  │ Value: Complete JSON response with sentiments    │   │
│  │ TTL: 24 hours (86400 seconds)                    │   │
│  │ Hit Rate: High for repeated page requests        │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  Layer 2: Individual Sentiment Cache                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Key: comment.id                                   │   │
│  │ Storage: Redis Hash (field: "comments")           │   │
│  │ Value: "positive" | "negative" | "neutral"       │   │
│  │ TTL: Persistent (until explicit deletion)         │   │
│  │ Hit Rate: High when same comments appear across   │   │
│  │          different videos/pages                   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
│  Layer 3: Pre-filtering (Memory)                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Check: hexists("comments", comment_id)           │   │
│  │ Result: Boolean (cached or not cached)            │   │
│  │ Impact: Skip LLM calls for cached comments        │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### Cache Invalidation

- **Full Response Cache**: 24-hour TTL (automatic expiration)
- **Individual Sentiments**: Persistent (manual flush available)
- **Flush Command**: `redis_client.flushall()` (commented in code)

---

## 📊 Concurrency Model

### Request Flow with Concurrency Control

```
Request 1 ──┐
Request 2 ──┼──┐
Request 3 ──┼──┼──┐
Request 4 ──┼──┼──┼──┐
            │  │  │  │
            ▼  ▼  ▼  ▼
    ┌──────────────────┐
    │  Semaphore Pool  │
    │  (Max: 20 slots) │
    └─────────┬────────┘
              │
        ┌─────┴─────┐
        │           │
        ▼           ▼
    ┌────────┐  ┌────────┐
    │  Slots │  │  Queue │
    │  (20)  │  │        │
    └───┬────┘  └───┬────┘
        │           │
        └─────┬─────┘
              │
              ▼
    ┌──────────────────┐
    │  Groq LLM API    │
    │  (Concurrent)    │
    └──────────────────┘
```

**Configuration**:

- `MAX_CONCURRENT_REQUESTS`: 20 (configurable)
- `BATCH_SIZE`: 5 (sentiment analysis batch)
- Semaphore control prevents API rate limit exhaustion

---

## 🚀 Deployment Architecture

### Production Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Network                          │
│                  (Internal Communication)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐       │
│  │    App     │◄───┤   Redis    │    │ Prometheus │       │
│  │  (Port     │    │  (Port     │    │  (Port     │       │
│  │   8000)    │    │   6379)    │    │   9090)    │       │
│  │            │    │            │    │            │       │
│  │ dibkb/neo- │    │ redis:7-   │    │ prom/      │       │
│  │ tube-      │    │ alpine     │    │ prometheus │       │
│  │ server:    │    │            │    │            │       │
│  │ production  │    │            │    │            │       │
│  └────────────┘    └────────────┘    └────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### External Services

```
┌─────────────────────────────────────────────────────────────┐
│                    External APIs                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐         ┌──────────────────┐        │
│  │  YouTube Data     │         │  Groq API        │        │
│  │  API v3           │         │  (LLaMA 3.3)     │        │
│  │                   │         │                  │        │
│  │  • Search         │         │  • Sentiment     │        │
│  │  • Comments       │         │    Classification│        │
│  │  • Video Info     │         │                  │        │
│  │  • Trending       │         │  • Fast Inference│        │
│  └───────────────────┘         └──────────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 Scalability Path

### Current Architecture (Single Instance)

```
Client → FastAPI (1 instance) → Redis → External APIs
```

### Horizontal Scaling (Recommended)

```
                           ┌─────────────┐
                           │  Load       │
                           │  Balancer   │
                           │  (NGINX)    │
                           └──────┬──────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │   FastAPI    │    │   FastAPI    │    │   FastAPI    │
    │   Instance 1 │    │   Instance 2 │    │   Instance 3 │
    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
           │                   │                   │
           └───────────────────┼───────────────────┘
                               │
                               ▼
                      ┌──────────────┐
                      │   Redis      │
                      │  (Shared)    │
                      └──────┬───────┘
                             │
                    ┌────────┼────────┐
                    │        │        │
                    ▼        ▼        ▼
              YouTube    Groq    Prometheus
```

### Vertical Scaling

- Increase `MAX_CONCURRENT_REQUESTS` for more parallel processing
- Add more Uvicorn workers: `uvicorn --workers 4 app.main:app`
- Upgrade Redis to a larger instance

---

## 🔒 Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Security Layers                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. CORS Protection                                     │
│     ├─ Whitelisted origins                             │
│     ├─ Credentials allowed                             │
│     └─ Production + Development origins                │
│                                                         │
│  2. Environment Variables                               │
│     ├─ API keys stored in .env                         │
│     ├─ Not committed to version control               │
│     └─ Separate credentials for prod/dev              │
│                                                         │
│  3. Docker Network Isolation                           │
│     ├─ Internal network for inter-service comm.       │
│     ├─ Exposed ports limited to required only          │
│     └─ Production images from trusted registry         │
│                                                         │
│  4. Rate Limiting (Future)                             │
│     ├─ API key-based authentication                    │
│     ├─ Per-client rate limits                          │
│     └─ DDoS protection                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

This architecture provides a **scalable**, **performant**, and **cost-effective** solution for real-time YouTube comment sentiment analysis.
