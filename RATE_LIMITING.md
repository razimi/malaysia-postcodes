# Rate Limiting Configuration Guide

The Malaysia Postcodes API implements per-API-key rate limiting, allowing you to assign different rate limits to different clients.

## How Rate Limiting Works

- Each API key has its own rate limit
- Rate limits are configured per-key in `api_keys.json`
- Format: `"number/period"` where period can be: `second`, `minute`, `hour`, or `day`
- When a client exceeds their limit, they receive HTTP 429 (Too Many Requests)

## Rate Limit Examples

| Configuration | Meaning |
|--------------|---------|
| `100/minute` | 100 requests per minute |
| `1000/hour` | 1,000 requests per hour |
| `10/second` | 10 requests per second |
| `5000/day` | 5,000 requests per day |

## Setting Rate Limits

### 1. When Generating a New API Key

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

### 2. Editing Existing API Keys

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

### 3. Default Rate Limit

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

## Rate Limit Tiers (Suggested)

### Free Tier
```bash
python3 api/key_generator.py --name "Free User" --rate-limit "60/minute"
```
- 60 requests/minute
- 3,600 requests/hour
- Suitable for small apps and testing

### Standard Tier
```bash
python3 api/key_generator.py --name "Standard User" --rate-limit "100/minute"
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
      "created": "2026-06-03T20:41:58.420376",
      "rate_limit": "100/minute"  ← Rate limit here
    }
  ]
}
```

## Best Practices

1. **Set appropriate limits**: Match rate limits to client needs
2. **Monitor usage**: Track which keys hit limits frequently
3. **Gradual limits**: Start conservative, increase as needed
4. **Document limits**: Clearly communicate rate limits to API consumers
5. **Provide headers**: Include rate limit info in response headers (future enhancement)
6. **Grace period**: Consider short bursts above limit before blocking
7. **Different periods**: Use appropriate period (second/minute/hour/day) based on use case

## Configuration by Use Case

| Use Case | Suggested Limit | Reasoning |
|----------|----------------|-----------|
| Mobile app | `100/minute` | Typical user interactions |
| Web dashboard | `500/minute` | Multiple users, periodic updates |
| Background sync | `1000/hour` | Scheduled batch operations |
| Real-time updates | `10/second` | Frequent polling |
| Data analytics | `10000/day` | Large batch processing |
| Microservice | `1000/minute` | Service-to-service calls |

## Troubleshooting

### Rate Limit Not Applied
1. Check if `rate_limit` field exists in `api_keys.json`
2. Restart the API: `docker-compose restart`
3. Verify the limit format is correct: `"number/period"`

### Rate Limit Too Restrictive
1. Edit `api_keys.json`
2. Increase the limit: `"rate_limit": "1000/minute"`
3. Restart the API

### Rate Limit Not Restrictive Enough
1. Lower the limit in `api_keys.json`
2. Or add validation at application level
3. Consider using `second` period for tighter control

## Advanced: Dynamic Rate Limiting

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
