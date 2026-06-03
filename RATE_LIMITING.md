# Rate Limiting Configuration Guide

The Malaysia Postcodes API implements **two types of rate limiting**:

1. **Per-API-Key Rate Limiting** - Each API key has its own configurable limit
2. **IP-Based Rate Limiting** - Limits requests from each IP address (applies to all endpoints)

This provides multiple layers of protection against abuse while allowing flexible configuration per client.

## How Rate Limiting Works

### Per-API-Key Limits
- Each API key has its own rate limit
- Rate limits are configured per-key in `api_keys.json`
- Format: `"number/period"` where period can be: `second`, `minute`, `hour`, or `day`
- Applied to all authenticated endpoints

### IP-Based Limits
- Limits requests from each IP address
- Applies to **all endpoints** including public ones (/, /health)
- Provides protection even before authentication
- Configured via `IP_RATE_LIMIT` environment variable
- Can be disabled by setting to empty string or removing the variable

### Combined Behavior
For authenticated endpoints, **both limits are checked**:
1. First, IP rate limit is checked (if configured)
2. Then, API key-specific rate limit is checked
3. Request must pass both checks to succeed

When a client exceeds either limit, they receive HTTP 429 (Too Many Requests)

## Rate Limit Examples

| Configuration | Meaning |
|--------------|---------|
| `100/minute` | 100 requests per minute |
| `1000/hour` | 1,000 requests per hour |
| `10/second` | 10 requests per second |
| `5000/day` | 5,000 requests per day |

## Setting Rate Limits

### 1. Per-API-Key Rate Limits

#### When Generating a New API Key

Use the `--rate-limit` parameter:

```bash
# Standard tier: 100 requests/minute
python3 api/key_generator.py --name "Standard Client" --rate-limit "100/minute"

# Premium tier: 1000 requests/minute
python3 api/key_generator.py --name "Premium Client" --rate-limit "1000/minute"

# Enterprise tier: 10,000 requests/hour
python3 api/key_generator.py --name "Enterprise Client" --rate-limit "10000/hour"

# High-frequency: 50 requests/second
python3 api/key_generator.py --name "HF Trading Bot" --rate-limit "50/second"
```

#### Editing Existing API Keys

Manually edit `api_keys.json`:

```json
{
  "keys": [
    {
      "key": "your-api-key-here",
      "name": "Standard Client",
      "created": "2026-06-03T20:41:58.420376",
      "rate_limit": "100/minute"
    },
    {
      "key": "premium-api-key-here",
      "name": "Premium Client",
      "created": "2026-06-03T20:50:33.910672",
      "rate_limit": "1000/minute"
    }
  ]
}
```

After editing, restart the API:
```bash
docker-compose restart
```

#### Default Rate Limit for API Keys

If an API key doesn't have a `rate_limit` specified, it defaults to the value in the `RATE_LIMIT` environment variable (default: `100/minute`).

Set in `.env`:
```bash
RATE_LIMIT=100/minute
```

Or in `docker-compose.yml`:
```yaml
environment:
  - RATE_LIMIT=100/minute
```

### 2. IP-Based Rate Limits

IP rate limiting applies to all requests from an IP address, regardless of API key.

#### Enable IP Rate Limiting

Set in `.env`:
```bash
# Limit each IP to 1000 requests per hour
IP_RATE_LIMIT=1000/hour
```

Or in `docker-compose.yml`:
```yaml
environment:
  - IP_RATE_LIMIT=1000/hour
```

#### Disable IP Rate Limiting

To disable IP rate limiting entirely:
```bash
# Set to empty or comment out
IP_RATE_LIMIT=

# Or remove the line entirely
```

#### Recommended IP Limits

| Environment | Recommended Limit | Reasoning |
|-------------|------------------|-----------|
| Development | `5000/hour` | Generous for testing |
| Staging | `2000/hour` | Moderate protection |
| Production | `1000/hour` | Stricter control |
| High-security | `500/hour` | Maximum protection |
| Public API | `100/hour` | Very restrictive for public endpoints |

**Note:** IP limits apply to **all endpoints** including `/` and `/health`, so set them appropriately.

## Rate Limit Tiers (Suggested)

### Free Tier
```bash
python3 api/key_generator.p (either IP or API key)y --name "Free User" --rate-limit "60/minute"
```
- 60 requests/minute
- 3,600 requests/hour
- Suitable for small apps and testing

### Standard Tier
```bash
python3 api/key_generator.py --name "Standard User" --rate-limit "100/minute"
```

Or for IP limits:
```json
{
  "detail": "Rate limit exceeded: 1000/hour"
}
```
- 100 requests/minute
- 6,000 requests/hour
- Suitable for most applications

### Premium Tier
```bash
python3 api/key_generator.py --name "Premium User" --rate-limit "1000/minute"
```
- 1,000 requests/minute
- 60,000 requests/hour
- Suitable for high-traffic applications

### Enterprise Tier
```bash
python3 api/key_generator.py --name "Enterprise User" --rate-limit "10000/hour"
```
- 10,000 requests/hour
- 240,000 requests/day
- Suitable for large-scale integrations

### Real-Time/Streaming
```bash
python3 api/key_generator.py --name "Real-Time Service" --rate-limit "50/second"
```
- 50 requests/second
- 3,000 requests/minute
- Suitable for real-time applications

## Rate Limit Response

When rate limit is exceeded, the API returns:

**Status Code:** `429 Too Many Requests`

**Response:**
```json
{
  "detail": "Rate limit exceeded: 100/minute"
}
```

**Headers:**
```
Retry-After: 45
```

The `Retry-After` header indicates how many seconds to wait before trying again.

## Testing Rate Limits

### Test Standard Limit (100/minute)
```bash
# Make rapid requests
for i in {1..105}; do
  curl -H "X-API-Key: YOUR_KEY" http://localhost:8000/states
  sleep 0.5
done
```

### Test Premium Limit (1000/minute)
```bash
# Make many rapid requests
for i in {1..1005}; do
  curl -H "X-API-Key: YOUR_PREMIUM_KEY" http://localhost:8000/states
  sleep 0.05
done
```

## Monitoring Rate Limits

### Check Current API Keys
```bash
cat api_keys.json | python3 -m json.tool
```

### View Rate Limit in Key Info
```json
{
  "keys": [
    {
      "key": "...",
      "name": "Client Name",
   Configuration Examples

### Scenario 1: Public API with Mixed Tiers

```bash
# IP limit: protect public endpoints
IP_RATE_LIMIT=1000/hour

# API keys with different tiers
python3 api/key_generator.py --name "Free User" --rate-limit "60/minute"
python3 api/key_generator.py --name "Premium User" --rate-limit "1000/minute"
```

Result:
- Free user: Limited to 60 req/min per key AND 1000 req/hour per IP
- Premium user: Limited to 1000 req/min per key AND 1000 req/hour per IP
- Public endpoints (/health): Limited to 1000 req/hour per IP

### Scenario 2: Internal API (No IP Limits)

```bash
# Disable IP limiting for internal network
IP_RATE_LIMIT=

# Only API key limits apply
python3 api/key_generator.py --name "Internal Service A" --rate-limit "5000/minute"
python3 api/key_generator.py --name "Internal Service B" --rate-limit "10000/minute"
```

Result:
- Only API key-specific limits are enforced
- No IP-based restrictions

### Scenario 3: High-Security Public API

```bash
# Very strict IP limits
IP_RATE_LIMIT=100/hour

# Moderate API key limits
python3 api/key_generator.py --name "Verified User" --rate-limit "500/hour"
```

Result:
- Even with valid API key, each IP limited to 100 req/hour
- Additional limit of 500 req/hour per API key
- Strong protection against abuse

### Scenario 4: Real-Time Application

```bash
# Higher frequency for both
IP_RATE_LIMIT=10/secondAPI keys without explicit limit |
| `IP_RATE_LIMIT` | `1000/hour` | Rate limit per IP address (all endpoints). Set to empty to disable

python3 api/key_generator.py --name "Real-Time App" --rate-limit "50/second"
```

Result:
- Each IP can make 10 req/second
- Each API key can make 50 req/second
- Suitable for high-frequency applications

## Best Practices

### IP Rate Limiting

1. **Set appropriate limits**: Balance security with legitimate use
2. **Consider CDNs**: If behind CDN/proxy, all requests may appear from same IP
3. **Whitelist IPs**: For trusted sources, consider higher or no IP limits
4. **Monitor patterns**: Track IP-based abuse patterns
5. **Gradual rollout**: Start generous, tighten based on abuse patterns

### Combined Limiting Strategy

1. **IP as first defense**: Use IP limiting to catch broad abuse
2. **API key for granular control**: Use key-specific limits for client management
3. **Layer the limits**: IP limit >= highest API key limit (usually)
4. **Different periods**: Consider IP limit per hour, API key limit per minute
5. **Public vs Protected**: Stricter IP limits on public endpoints

## Configuration by Use Case

| Use Case | IP Limit | API Key Limit | Reasoning |
|----------|----------|---------------|-----------|
| Public API (Free) | 1000/hour | 60/minute | Prevent IP abuse, allow moderate key usage |
| Public API (Premium) | 2000/hour | 1000/minute | Higher limits for paid users |
| Internal API | None | 5000/minute | No IP restriction internally |
| Developer Sandbox | 5000/hour | 100/minute | Generous for testing |
| Production Service | 1000/hour | 500/minute | Balanced protection |
| High-Security API | 100/hour | 100/hour | Maximum protection |
| Real-Time Streaming | 50/second | 100/second | High-frequency support |

## Monitoring & Debugging

### Check Current Configuration

```bash
# View IP rate limit setting
docker exec malaysia-postcodes-api env | grep IP_RATE_LIMIT

# View API key limits
cat api_keys.json | python3 -m json.tool
```

### Test IP Rate Limiting

```bash
# Test public endpoint IP limit
for i in {1..1005}; do
  curl -s http://localhost:8000/health > /dev/null
  echo "Request $i"
  sleep 3.5  # Just under 1000/hour
done
```

### Test Combined Limits

```bash
# This will hit BOTH IP and API key limits
for i in {1..105}; do
  curl -s -H "X-API-Key: YOUR_KEY" http://localhost:8000/states > /dev/null
  echo "Request $i"
  sleep 0.5
done
```
For more sophisticated rate limiting (e.g., based on time of day, client tier, endpoint), consider:

1. **Redis-based limiting**: For distributed rate limiting across multiple instances
2. **Tier-based routing**: Different endpoints for different tiers
3. **Usage-based limits**: Adjust limits based on historical usage
4. **Burst allowance**: Allow short bursts above the sustained rate
5. **Cost-based limiting**: Different "costs" for different endpoints

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT` | `100/minute` | Default rate limit for keys without explicit limit |

## See Also

- [API Key Generator](api/key_generator.py) - Generate new keys with custom limits
- [Authentication Guide](README.md#authentication) - API key setup
- [API Documentation](http://localhost:8000/docs) - Interactive API docs
