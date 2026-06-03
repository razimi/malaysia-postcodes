# Malaysia Postcodes

A Comprehensive List of Malaysia Postcodes, Complete with City and State Information, available in JSON format.

## Overview

This repository provides an extensive collection of Malaysia postcodes, indexed by city and state. It serves as a useful resource for developers, researchers, and anyone interested in postal data for Malaysia.

## Data Structure

The data is structured in JSON, and the format is as follows:

```json
{
   "name": "Kelantan",
   "city": [
       {
        "name": "Pasir Mas",
        "postcode": [
            "17000",
            "17007",
            "17009",
            "17010",
            "17020",
            "17030",
            "17040",
            "17050",
            "17060",
            "17070"
        ]
       }
   ]
}
```

## Table of Contents

- [All Postcodes](all.json)
- [Johor](johor.json)
- [Kedah](kedah.json)
- [Kelantan](kelantan.json)
- [Kuala Lumpur](kuala_lumpur.json)
- [Labuan](labuan.json)
- [Melaka](melaka.json)
- [Negeri Sembilan](negeri_sembilan.json)
- [Pahang](pahang.json)
- [Pulau Pinang](pulau_pinang.json)
- [Perak](perak.json)
- [Perlis](perlis.json)
- [Putrajaya](putrajaya.json)
- [Sabah](sabah.json)
- [Sarawak](sarawak.json)
- [Selangor](selangor.json)
- [Terengganu](terengganu.json)

## What's New

For the latest updates, see the [Changelog](CHANGELOG.md).

- [Added new postcode 80888 for Ibrahim International Business District (IIBD) in Johor (2025-12-28)](CHANGELOG.md#2025-12-28)
- [Postcode data accuracy improvements for Pulau Pinang and Johor (2025-06-27)](CHANGELOG.md#2025-06-27)
  - Added missing postcode 79050 to Iskandar Puteri (Johor)
  - Removed 12 invalid postcodes from Pulau Pinang cities to match official reference
  - Removed incorrect postcode 71590 from Pekan Nenas (Johor)
- [Complete coverage review and fixes for multiple states (2025-06-26)](CHANGELOG.md#2025-06-26)
  - Added missing locations: Tenghilan (Sabah), Pusat Mel Miri & Sibu Jaya (Sarawak)
  - Renamed Penang to official name "Pulau Pinang" and updated file name
  - Fixed formatting issues in Negeri Sembilan, Pahang, and Perak
  - Removed invalid postcodes and corrected city names across multiple states
- [Added new postcode for TRX (Tun Razak Exchange) in Kuala Lumpur (2025-03-10)](CHANGELOG.md#2025-03-10)
- [Removed incorrect-length postcodes from various cities (2023-08-27)](CHANGELOG.md#2023-08-27)

## REST API

This repository now includes a **REST API** for programmatic access to Malaysia postcode data with authentication and rate limiting.

### Features

- 🔐 **API Key Authentication** - Secure access control
- ⚡ **Fast In-Memory Lookups** - Sub-10ms response times
- 🚦 **Per-Key Rate Limiting** - Configurable limits per API key
- 🐳 **Docker Ready** - Easy deployment with Docker Compose
- 📚 **Auto-Generated Documentation** - Interactive Swagger UI
- 🔍 **Flexible Search** - Search states and cities by name
- ↔️ **Reverse Lookup** - Find location by postcode

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/AsyrafHussin/malaysia-postcodes.git
   cd malaysia-postcodes
   ```

2. **Generate an API key**
   ```bash
   python3 api/key_generator.py --name "My Application"
   ```
   Save the generated API key - you'll need it to access the API.

3. **Start the API**
   ```bash
   docker-compose up --build
   ```

4. **Access the API**
   - Interactive Documentation: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

### API Endpoints

All endpoints except `/` and `/health` require authentication via `X-API-Key` header.

#### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |

#### Protected Endpoints (Require API Key)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/states` | List all states with summary |
| GET | `/states/{state_name}` | Get state details with all cities |
| GET | `/states/{state_name}/cities` | List all cities in a state |
| GET | `/states/{state_name}/cities/{city_name}` | Get city details with postcodes |
| GET | `/postcodes/{postcode}` | Lookup location by postcode |
| GET | `/search?q={query}` | Search states and cities |

### Usage Examples

**List all states:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8000/states
```

**Get state details:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8000/states/Johor
```

**Lookup postcode:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8000/postcodes/50000
```

**Search for cities:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" "http://localhost:8000/search?q=Kuala"
```

### Authentication

The API uses API key authentication via the `X-API-Key` header. 

**Generate a new API key:**
```bash
python3 api/key_generator.py --name "Client Name"
```

API keys are stored in `api_keys.json` (not committed to git). Keep your API keys secure.

### Rate Limiting

Each API key has its own configurable rate limit:

- **Default Limit:** 100 requests per minute per API key
- **Customizable:** Set different limits for different clients (e.g., 60/minute, 1000/minute, 10000/hour)
- **Response:** HTTP 429 (Too Many Requests) when exceeded
- **Retry-After:** Header indicates when to retry

**Generate key with custom rate limit:**
```bash
# Standard: 100 requests/minute
python3 api/key_generator.py --name "Standard Client" --rate-limit "100/minute"

# Premium: 1000 requests/minute
python3 api/key_generator.py --name "Premium Client" --rate-limit "1000/minute"

# Enterprise: 10,000 requests/hour
python3 api/key_generator.py --name "Enterprise" --rate-limit "10000/hour"
```

See [RATE_LIMITING.md](RATE_LIMITING.md) for detailed configuration guide.

### Local Development

**Without Docker:**

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate API key**
   ```bash
   python3 api/key_generator.py --name "Dev"
   ```

3. **Run the API**
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Run tests**
   ```bash
   pip install -r tests/requirements.txt
   pytest tests/
   ```

### Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | Server port |
| `HOST` | 0.0.0.0 | Server host |
| `LOG_LEVEL` | info | Logging level |
| `API_KEYS_FILE` | api_keys.json | Path to API keys file |
| `CORS_ORIGINS` | * | Allowed CORS origins |

### Deployment

The API is production-ready and can be deployed to:
- Docker containers (recommended)
- Cloud platforms (AWS, GCP, Azure)
- Kubernetes
- Any Python hosting service

For production deployment, ensure:
1. API keys are securely managed (use secrets management)
2. CORS origins are properly configured
3. HTTPS is enabled (use reverse proxy like nginx)
4. Health check endpoint is monitored

## NPM

For those interested in installing this dataset via NPM, you can do so with our [malaysia-postcodes](https://github.com/AsyrafHussin/npm-malaysia-postcodes) package.

## Related

Looking for Malaysia Parliament and DUN constituency data? Check out [malaysia-parliament-dun](https://github.com/AsyrafHussin/malaysia-parliament-dun) — a comprehensive list of Malaysia Parliament (Parlimen) and State Assembly (DUN) constituencies based on GE15 2022, available in JSON format.

## Contributing

If you find any inaccuracies, typos, or missing data, we welcome contributions! Please feel free to open an issue or submit a pull request.

## License

This repository is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
