# Redis Caching Guide

This guide explains the Redis caching implementation in MeroGhar for optimizing performance of analytics and reports endpoints.

**Implements**: T259 from tasks.md

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Cache Configuration](#cache-configuration)
4. [Using the Cache Decorator](#using-the-cache-decorator)
5. [Cache Invalidation](#cache-invalidation)
6. [Cached Endpoints](#cached-endpoints)
7. [Cache Keys](#cache-keys)
8. [Performance Metrics](#performance-metrics)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Overview

### What is Cached?

The caching system optimizes **read-heavy analytics and reports endpoints** by storing results in Redis. This dramatically reduces database load and improves response times for frequently accessed data.

**Cached Data Types**:

- Analytics dashboards (rent trends, payment status, expense breakdown)
- Revenue vs expenses comparisons
- Property performance metrics
- Tax reports (income, deductions, GST)
- Financial statements (profit/loss, cash flow)

**Cache Strategy**:

- **Time-based expiration (TTL)**: Cached data expires after a set duration
- **Event-based invalidation**: Cache is cleared when underlying data changes (new payments, bills)
- **User-scoped caching**: Cache keys include user_id to ensure data isolation

### Why Redis?

- **Fast**: In-memory storage provides sub-millisecond response times
- **Scalable**: Can handle high request volumes across multiple app servers
- **Persistent**: Optional RDB persistence for cache warmth across restarts
- **Distributed**: Shared cache across multiple FastAPI workers/pods

### Performance Impact

**Expected Improvements**:

- Analytics endpoints: **10-100x faster** (5-50ms vs 500-5000ms)
- Database load reduction: **80-90%** for cached endpoints
- Concurrent user capacity: **5-10x increase**
- Server resources: **50-70%** CPU/memory reduction for analytics queries

---

## Architecture

### System Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI    │────▶│  PostgreSQL │
│   (Mobile/  │◀────│   Server    │◀────│  Database   │
│    Web)     │     └─────┬───────┘     └─────────────┘
└─────────────┘           │
                          │ Cache Hit/Miss
                          ▼
                    ┌─────────────┐
                    │    Redis    │
                    │    Cache    │
                    └─────────────┘
```

### Request Flow

#### Cache Hit (Fast Path)

```
1. Client requests /api/v1/analytics/rent-trends
2. CacheService checks Redis for key "cache:analytics:rent_trends:user_id=..."
3. Cache HIT → Return cached JSON
4. Response time: 5-20ms
```

#### Cache Miss (Slow Path)

```
1. Client requests /api/v1/analytics/rent-trends
2. CacheService checks Redis for key
3. Cache MISS → Execute database query
4. Store result in Redis with TTL
5. Return fresh data
6. Response time: 500-5000ms
```

#### Cache Invalidation

```
1. Client creates payment via POST /api/v1/payments
2. PaymentService commits payment to database
3. PaymentService calls invalidate_cache("cache:analytics:*")
4. Redis deletes all analytics cache keys
5. Next analytics request will be cache MISS (refreshing data)
```

---

## Cache Configuration

### Environment Variables

**Required**:

```env
# Redis connection URL
REDIS_URL=redis://localhost:6379/0

# Production example with auth
REDIS_URL=redis://:password@redis.example.com:6379/1
```

**Optional** (via `CACHE_TTL` constants):

```python
CACHE_TTL = {
    "short": 60,       # 1 minute
    "medium": 300,     # 5 minutes (default)
    "long": 900,       # 15 minutes
    "hour": 3600,      # 1 hour
    "day": 86400,      # 24 hours
}
```

### Redis Configuration

**docker-compose.yml**:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  redis_data:
```

**Production Settings**:

- **Maxmemory**: `maxmemory 2gb` (adjust based on cache size needs)
- **Eviction Policy**: `maxmemory-policy allkeys-lru` (least recently used eviction)
- **Persistence**: `appendonly yes` (AOF for durability)
- **Timeout**: `timeout 300` (close idle clients after 5 minutes)

---

## Using the Cache Decorator

### Basic Usage

**Import**:

```python
from ..core.cache import cached, CACHE_TTL
```

**Apply to async functions**:

```python
@cached(ttl=CACHE_TTL["medium"], key_prefix="analytics:rent_trends")
async def get_rent_collection_trends(
    user_id: UUID,
    property_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    # Expensive database query
    return results
```

### Decorator Parameters

| Parameter       | Type      | Default         | Description                                    |
| --------------- | --------- | --------------- | ---------------------------------------------- |
| `ttl`           | int       | 300             | Time-to-live in seconds                        |
| `key_prefix`    | str       | `func.__name__` | Cache key prefix                               |
| `invalidate_on` | list[str] | None            | Patterns to invalidate when function is called |

### TTL Selection Guide

| TTL             | Use Case                 | Examples                                   |
| --------------- | ------------------------ | ------------------------------------------ |
| `short` (60s)   | Rapidly changing data    | Current payment status, live notifications |
| `medium` (300s) | Default analytics        | Rent trends, expense breakdown             |
| `long` (900s)   | Slow-changing aggregates | Revenue vs expenses, property performance  |
| `hour` (3600s)  | Semi-static reports      | Tax reports, annual income                 |
| `day` (86400s)  | Reference data           | Property lists, tenant lists               |

### Key Generation

**Automatic key generation** based on function arguments:

```python
# Function call
get_rent_collection_trends(
    user_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
    property_id=UUID("789e4567-e89b-12d3-a456-426614174001"),
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
)

# Generated cache key
"cache:analytics:rent_trends:user_id=123e4567-e89b-12d3-a456-426614174000:property_id=789e4567-e89b-12d3-a456-426614174001:start_date=2024-01-01:end_date=2024-12-31"
```

**Key hashing** (for long keys):

- If key > 100 characters, MD5 hash is used:
  ```
  cache:analytics:rent_trends:a3f5c8d1b2e4f6a7...
  ```

---

## Cache Invalidation

### Automatic Invalidation

**On Payment Creation**:

```python
# backend/src/services/payment_service.py
await self.session.commit()
invalidate_cache("cache:analytics:*")  # Clear all analytics caches
```

**On Bill Creation**:

```python
# backend/src/services/bill_service.py
await self.session.commit()
invalidate_cache("cache:analytics:*")  # Clear all analytics caches
```

### Manual Invalidation

**From Python code**:

```python
from ..core.cache import invalidate_cache

# Invalidate specific pattern
invalidate_cache("cache:analytics:rent_trends:*")

# Invalidate all analytics
invalidate_cache("cache:analytics:*")

# Invalidate all caches (use with caution)
from ..core.cache import get_cache_service
get_cache_service().clear_all()
```

**From Redis CLI**:

```bash
# Connect to Redis
docker exec -it meroghar-redis redis-cli

# Delete analytics caches
KEYS cache:analytics:*
DEL cache:analytics:rent_trends:user_id=...

# Flush all (DANGER: clears entire database)
FLUSHDB
```

### Invalidation Strategies

| Strategy          | When to Use                     | Example                                                      |
| ----------------- | ------------------------------- | ------------------------------------------------------------ |
| **Pattern-based** | Invalidate related caches       | `invalidate_cache("cache:analytics:*")`                      |
| **Time-based**    | Rely on TTL expiration          | Set appropriate TTL values                                   |
| **Selective**     | Invalidate specific user caches | `invalidate_cache(f"cache:analytics:*:user_id={user_id}:*")` |
| **Full clear**    | Major data migration            | `get_cache_service().clear_all()`                            |

---

## Cached Endpoints

### Analytics Endpoints

| Endpoint                                     | TTL  | Key Prefix                       | Invalidated By        |
| -------------------------------------------- | ---- | -------------------------------- | --------------------- |
| `GET /api/v1/analytics/rent-trends`          | 300s | `analytics:rent_trends`          | Payment creation      |
| `GET /api/v1/analytics/payment-status`       | 300s | `analytics:payment_status`       | Payment creation      |
| `GET /api/v1/analytics/expense-breakdown`    | 900s | `analytics:expense_breakdown`    | Bill creation         |
| `GET /api/v1/analytics/revenue-expenses`     | 900s | `analytics:revenue_vs_expenses`  | Payment/Bill creation |
| `GET /api/v1/analytics/property-performance` | 900s | `analytics:property_performance` | Payment/Bill creation |

### Reports Endpoints

**Tax Reports**:

- `GET /api/v1/reports/tax/income` - Annual income report
- `GET /api/v1/reports/tax/deductions` - Tax deductions report
- `GET /api/v1/reports/tax/gst` - GST quarterly report

**Financial Statements**:

- `GET /api/v1/reports/financial/profit-loss` - Profit & loss statement
- `GET /api/v1/reports/financial/cash-flow` - Cash flow statement

**Note**: Reports endpoints use longer TTL (15-60 minutes) as they are less time-sensitive.

---

## Cache Keys

### Key Naming Convention

**Format**:

```
cache:{category}:{function}:{arg1}={val1}:{arg2}={val2}...
```

**Examples**:

```
cache:analytics:rent_trends:user_id=123:property_id=456:start_date=2024-01-01
cache:analytics:payment_status:user_id=789
cache:analytics:expense_breakdown:user_id=123:property_id=456
```

### Key Patterns

**Pattern matching** for bulk operations:

| Pattern                           | Matches                 | Use Case                        |
| --------------------------------- | ----------------------- | ------------------------------- |
| `cache:analytics:*`               | All analytics caches    | Invalidate on data change       |
| `cache:analytics:rent_trends:*`   | All rent trend caches   | Invalidate rent-specific caches |
| `cache:analytics:*:user_id=123:*` | All caches for user 123 | User-specific invalidation      |
| `cache:*`                         | All application caches  | Full cache clear                |

---

## Performance Metrics

### Monitoring Cache Performance

**Redis INFO command**:

```bash
docker exec -it meroghar-redis redis-cli INFO stats

# Key metrics:
keyspace_hits:15234      # Cache hits
keyspace_misses:3421     # Cache misses
hit_rate: 81.7%          # Hit rate = hits / (hits + misses)
```

**Application logs** (DEBUG level):

```
Cache HIT: cache:analytics:rent_trends:user_id=123
Cache MISS: cache:analytics:payment_status:user_id=456
Cache SET: cache:analytics:expense_breakdown:user_id=789 (TTL: 900s)
Cache invalidated: cache:analytics:* (47 keys)
```

### Expected Metrics

**Healthy Cache**:

- **Hit rate**: 70-90% (after warm-up period)
- **Average response time**: 10-50ms (cached), 500-5000ms (uncached)
- **Cache size**: 50-500 MB (depending on data volume)
- **Evictions**: < 5% (if higher, increase Redis maxmemory)

**Warning Signs**:

- Hit rate < 50%: Check TTL values, cache invalidation frequency
- High evictions: Increase Redis memory or reduce TTL
- Cache size > 2GB: Review cache strategy, add selective caching

### Load Testing

**Simulate high traffic**:

```bash
# Install siege
sudo apt-get install siege

# Test analytics endpoint (100 concurrent users, 60 seconds)
siege -c 100 -t 60S http://localhost:8000/api/v1/analytics/rent-trends?start_date=2024-01-01

# Expected results:
# - First request: 2000ms (cache miss)
# - Subsequent requests: 15ms (cache hit)
# - Throughput: 5000+ requests/minute
```

---

## Troubleshooting

### Issue: Cache Not Working

**Symptoms**: All requests are slow, no cache hits in logs

**Diagnosis**:

```bash
# Check Redis connectivity
docker exec -it meroghar-redis redis-cli PING
# Expected: PONG

# Check if cache service initialized
grep "Redis cache service initialized" backend/logs/app.log

# Check for cache errors
grep "Cache .* error" backend/logs/app.log
```

**Solutions**:

1. Verify Redis is running: `docker ps | grep redis`
2. Check `REDIS_URL` environment variable
3. Verify Redis port is accessible: `telnet localhost 6379`
4. Check Redis logs: `docker logs meroghar-redis`

### Issue: High Cache Miss Rate

**Symptoms**: Hit rate < 50%, slow response times

**Diagnosis**:

```bash
# Check cache invalidation frequency
grep "Cache invalidated" backend/logs/app.log | wc -l

# Check average TTL
docker exec -it meroghar-redis redis-cli
> KEYS cache:analytics:*
> TTL cache:analytics:rent_trends:...
```

**Solutions**:

1. **Increase TTL** if data changes infrequently
2. **Reduce invalidation scope**: Instead of `cache:analytics:*`, invalidate specific patterns
3. **Pre-warm cache**: Run analytics queries after data changes
4. **Review query parameters**: Ensure consistent parameter order

### Issue: Stale Data in Cache

**Symptoms**: Users see outdated analytics after creating payments/bills

**Diagnosis**:

```bash
# Check if invalidation is called
grep "Cache invalidated" backend/logs/app.log

# Verify invalidation happens after commit
# Should see: "Payment recorded" followed by "Cache invalidated"
```

**Solutions**:

1. Verify `invalidate_cache()` is called after database commit
2. Check invalidation pattern matches cache keys
3. Manually flush cache: `docker exec -it meroghar-redis redis-cli FLUSHDB`
4. Reduce TTL for affected endpoints

### Issue: Redis Out of Memory

**Symptoms**: `OOM command not allowed when used memory > 'maxmemory'`

**Diagnosis**:

```bash
docker exec -it meroghar-redis redis-cli INFO memory

# Check:
used_memory_human:1.8G
maxmemory_human:2.0G
evicted_keys:15234  # High eviction count
```

**Solutions**:

1. **Increase Redis maxmemory**:
   ```yaml
   # docker-compose.yml
   redis:
     command: redis-server --maxmemory 4gb
   ```
2. **Enable LRU eviction**:
   ```yaml
   command: redis-server --maxmemory-policy allkeys-lru
   ```
3. **Reduce TTL** for large cache entries
4. **Selective caching**: Cache only frequently accessed endpoints

### Issue: Cache Stampede

**Symptoms**: Multiple simultaneous cache misses cause database overload

**Example**:

```
100 concurrent requests → All cache MISS → 100 DB queries → Database timeout
```

**Solution** (future enhancement):

```python
# Implement cache locking (not yet implemented)
@cached_with_lock(ttl=300, lock_timeout=10)
async def expensive_query():
    # Only one request executes query
    # Others wait for cache to populate
    pass
```

**Workaround**:

- **Pre-warm cache** after data changes:
  ```python
  # After payment creation
  invalidate_cache("cache:analytics:*")
  await analytics_service.get_rent_collection_trends(user_id)  # Warm cache
  ```
- **Rate limiting** on analytics endpoints

---

## Best Practices

### 1. Choose Appropriate TTL

**Guidelines**:

- **Real-time data** (< 1 minute old): Don't cache, or use short TTL (60s)
- **Near-real-time** (< 5 minutes old): Medium TTL (300s)
- **Periodic reports** (updated hourly): Long TTL (3600s)
- **Historical data** (rarely changes): Very long TTL (86400s)

**Example**:

```python
# Real-time payment status (60s)
@cached(ttl=CACHE_TTL["short"])
async def get_current_payment_status():
    pass

# Daily revenue report (1 hour)
@cached(ttl=CACHE_TTL["hour"])
async def get_daily_revenue():
    pass
```

### 2. Invalidate Precisely

**❌ Bad** (over-invalidation):

```python
# Clears ALL caches, even unrelated ones
invalidate_cache("cache:*")
```

**✅ Good** (targeted invalidation):

```python
# Only clears analytics caches
invalidate_cache("cache:analytics:*")

# Even better - only rent-related analytics
invalidate_cache("cache:analytics:rent_trends:*")
```

### 3. Handle Cache Failures Gracefully

**Cache should be transparent** - application works even if Redis is down:

```python
# cache.py already implements this
if not self.is_enabled():
    return None  # Falls back to database query
```

**Logging**:

```python
# Warn but don't fail
logger.warning(f"Cache get error: {e}. Falling back to database.")
```

### 4. Monitor Cache Health

**Set up alerts**:

```yaml
# Prometheus/Grafana alerts
- alert: LowCacheHitRate
  expr: redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total) < 0.5
  for: 10m
  annotations:
    summary: "Cache hit rate below 50%"

- alert: HighCacheEvictions
  expr: rate(redis_evicted_keys_total[5m]) > 100
  annotations:
    summary: "High cache eviction rate"
```

**Weekly review**:

- Check hit rate trends
- Review slow queries (cache misses)
- Analyze cache size growth
- Identify most cached endpoints

### 5. Version Cache Keys

**For schema changes**:

```python
# Before deployment with schema changes
invalidate_cache("cache:analytics:*")

# Or version cache keys
@cached(ttl=300, key_prefix="analytics:rent_trends:v2")
async def get_rent_collection_trends():
    pass
```

### 6. Document Caching Decisions

**In code comments**:

```python
# Cache for 15 minutes because:
# - Expense data changes infrequently (bills created monthly)
# - Aggregation query is expensive (5-10 seconds)
# - Users typically view this report multiple times per session
@cached(ttl=CACHE_TTL["long"], key_prefix="analytics:expense_breakdown")
async def get_expense_breakdown():
    pass
```

### 7. Test Cache Behavior

**Unit tests**:

```python
async def test_analytics_caching():
    # First call - cache MISS
    result1 = await service.get_rent_collection_trends(user_id)

    # Second call - cache HIT (should be faster)
    result2 = await service.get_rent_collection_trends(user_id)

    assert result1 == result2

    # Invalidate and verify refresh
    invalidate_cache("cache:analytics:*")
    result3 = await service.get_rent_collection_trends(user_id)
```

### 8. Security Considerations

**User isolation**:

- Cache keys include `user_id` to prevent data leakage
- RLS policies still apply to database queries
- Cache invalidation respects user permissions

**Sensitive data**:

```python
# Don't cache PII or sensitive data
@cached(ttl=300)
async def get_payment_summary():  # ✅ OK - aggregated data
    return {"total": 15000, "count": 45}

async def get_payment_details():  # ❌ Don't cache - contains PII
    return {"tenant_name": "John Doe", "amount": 1500}
```

---

## Appendix: Cache Implementation Details

### CacheService Class

**Location**: `backend/src/core/cache.py`

**Key Methods**:

- `get(key)`: Retrieve cached value
- `set(key, value, ttl)`: Store value with TTL
- `delete(key)`: Delete single key
- `delete_pattern(pattern)`: Delete matching keys
- `clear_all()`: Flush entire cache database

**Error Handling**:

- All cache operations wrapped in try/except
- Failures logged but don't crash application
- Returns None on cache errors (triggers cache miss)

### Cached Decorator

**Supports**:

- ✅ Async functions
- ✅ Sync functions
- ✅ Variable arguments (\*args, \*\*kwargs)
- ✅ Custom key prefixes
- ✅ Automatic serialization (JSON)
- ✅ Cache invalidation triggers

**Limitations**:

- ❌ Cannot cache non-JSON-serializable types (use `default=str`)
- ❌ Cache keys limited to 1KB (hashing applied for long keys)
- ❌ No cache locking (stampede protection not implemented)

---

## Support and Resources

**Documentation**:

- Redis Documentation: https://redis.io/documentation
- FastAPI Caching: https://fastapi.tiangolo.com/advanced/custom-response/
- Cache Patterns: https://redis.io/docs/manual/patterns/

**Monitoring Tools**:

- Redis CLI: Built-in monitoring commands
- RedisInsight: GUI for Redis management
- Prometheus/Grafana: Metrics and alerting

**Contact**:

- For caching issues: Check logs first, then contact DevOps team
- For performance tuning: Review this guide, test TTL adjustments
- For new caching features: Submit feature request with use case

---

_Last Updated_: January 2025  
_Version_: 1.0.0  
_Implements_: T259 - Redis response caching
