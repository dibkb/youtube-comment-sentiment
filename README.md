# BroTube - YouTube Comment Sentiment Analysis API

A high-performance FastAPI service that analyzes YouTube comment sentiments in real-time using Large Language Models (LLMs).

## 🎯 Features

- **Real-time Sentiment Analysis**: Analyzes YouTube comments as positive, negative, or neutral
- **Intelligent Caching**: Multi-level Redis caching to minimize LLM API calls and reduce costs
- **Batch Processing**: Concurrent sentiment analysis with configurable concurrency limits
- **YouTube Integration**: Fetch videos, comments, trending content, and related videos
- **Monitoring**: Prometheus metrics for observability
- **Production Ready**: Docker-based deployment with development and production configurations

## 🏗️ Architecture

```
FastAPI App → YouTube API → Batch Sentiment Analysis → Groq (LLaMA 3.3) → Redis Cache → Response
```

### Key Components

1. **FastAPI Application**: Async web framework for high performance
2. **Groq LLM**: LLaMA 3.3 70B for sentiment classification
3. **Redis Cache**: Multi-level caching (response + individual sentiments)
4. **YouTube API v3**: Fetch comments and video data
5. **Prometheus**: Metrics collection and monitoring

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Poetry (dependency management)
- YouTube Data API key
- Groq API key

### Development Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd youtube-comment-sentiment
   ```

2. **Create environment file**

   ```bash
   # Create .env file
   echo "GROQ_API_KEY=your_groq_key" >> .env
   echo "YOUTUBE_API_KEY=your_youtube_key" >> .env
   ```

3. **Start services**

   ```bash
   docker-compose -f docker-compose-dev.yml up
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Prometheus: http://localhost:9090

## 📡 API Endpoints

### Comment Sentiment

```bash
# Analyze comments for a video
POST /comment-sentiment/{video_id}
Body: {"next_page_token": "optional_token"}
```

### Video Search & Discovery

```bash
# Search for videos
POST /videos/search?query="your search term"

# Get related videos
GET /videos/search-related?title="video title"

# Get video information
GET /videos/info/{videoId}

# Get trending videos
GET /videos/trending-videos?country=US
```

## ⚙️ Configuration

Edit `app/settings.py` to adjust:

- `MAX_RESULTS`: Comments per page (default: 20)
- `MAX_CONCURRENT_REQUESTS`: LLM concurrency limit (default: 20)
- `REDIS_CACHE_EXPIRATION`: Cache TTL in seconds (default: 86400 = 24h)
- `BATCH_SIZE`: Sentiment analysis batch size (default: 5)

## 🐳 Deployment

### Production

```bash
docker-compose -f docker-compose-prod.yml up -d
```

Uses pre-built image: `dibkb/neo-tube-server:production`

### Development

```bash
docker-compose -f docker-compose-dev.yml up --build
```

Includes hot reload for code changes.

## 📊 How It Works

1. **Request Received**: Client requests comments for a video
2. **Cache Check**: System checks Redis for cached complete response
3. **YouTube API**: If cache miss, fetches comments from YouTube
4. **Pre-filtering**: Identifies which comments need sentiment analysis
5. **Batch Analysis**: Concurrently analyzes uncached comments via Groq LLM
6. **Cache Results**: Stores sentiments in Redis (persistent) and full response (24h TTL)
7. **Enrich & Return**: Enriches comments with sentiments and returns to client

## 🔧 Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **LLM**: Groq (LLaMA 3.3 70B)
- **Cache**: Redis 7
- **APIs**: YouTube Data API v3
- **Monitoring**: Prometheus
- **Containerization**: Docker & Docker Compose
- **Package Manager**: Poetry

## 📈 Performance Optimizations

1. **Smart Caching**: Two-level caching (full responses + individual sentiments)
2. **Concurrent Processing**: Batch sentiment analysis with semaphore control
3. **Pipeline Operations**: Bulk Redis reads/writes for performance
4. **Pre-filtering**: Only analyzes comments not in cache
5. **Singleton Connections**: Reuse YouTube API, LLM, and Redis connections

## 🛠️ Development

### Local Setup (without Docker)

1. **Install dependencies**

   ```bash
   poetry install
   ```

2. **Run Redis**

   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```

3. **Run application**
   ```bash
   poetry run uvicorn app.main:app --reload --port 8000
   ```

### Code Formatting

```bash
poetry run format
```

## 📖 Documentation

For detailed system design, architecture, and API specifications, see [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md).

## 🔐 Security

- CORS configured for whitelisted origins
- API keys stored in environment variables
- Production credentials separate from development
- `.env` file excluded from version control

## 📝 License

[Specify your license]

## 👤 Author

dibkb (dibas9110@gmail.com)

---

**Note**: This is a production-ready service with intelligent caching, batch processing, and monitoring. Designed for scalability and cost efficiency.
