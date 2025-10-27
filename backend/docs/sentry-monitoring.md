# Sentry Monitoring and Alerting Guide

**Task**: T266 - Setup monitoring and alerting with Sentry  
**Date**: October 27, 2025  
**Version**: 1.0

## Table of Contents

1. [Overview](#overview)
2. [Setup Instructions](#setup-instructions)
3. [Configuration](#configuration)
4. [Error Tracking](#error-tracking)
5. [Performance Monitoring](#performance-monitoring)
6. [Alert Configuration](#alert-configuration)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

Sentry is configured to provide comprehensive error tracking and performance monitoring for the MeroGhar Rental Management System. This includes:

- **Error Tracking**: Automatic capture of exceptions and errors
- **Performance Monitoring**: Transaction tracing and profiling
- **Release Tracking**: Version-specific error tracking
- **User Context**: Track which users experience errors
- **Breadcrumbs**: Event trail leading to errors
- **Integrations**: FastAPI, Celery, and logging integration

### What's Monitored

- FastAPI API endpoints (request/response errors)
- Celery background tasks (task failures)
- Database queries (slow queries, connection errors)
- External API calls (payment gateways, S3, Twilio, Firebase)
- Application logs (ERROR level and above)

---

## Setup Instructions

### 1. Create Sentry Account

1. Sign up at [https://sentry.io](https://sentry.io)
2. Create a new project:
   - **Platform**: Python
   - **Name**: meroghar-backend
   - **Team**: Your organization team
3. Copy your **DSN** (Data Source Name) from Project Settings

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Sentry Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/your-project-id
ENVIRONMENT=production  # or development, staging
```

**Environment-specific DSNs** (recommended):

```bash
# Development
SENTRY_DSN=https://dev-dsn@sentry.io/12345
ENVIRONMENT=development

# Staging
SENTRY_DSN=https://staging-dsn@sentry.io/12346
ENVIRONMENT=staging

# Production
SENTRY_DSN=https://prod-dsn@sentry.io/12347
ENVIRONMENT=production
```

### 3. Install Dependencies

Already included in `requirements.txt`:

```bash
sentry-sdk[fastapi]==1.38.0
```

Install with:

```bash
pip install -r requirements.txt
```

### 4. Verify Integration

Start the application:

```bash
uvicorn src.main:app --reload
```

Check logs for:

```
INFO: Sentry monitoring initialized successfully
```

### 5. Test Error Reporting

Create a test error:

```bash
curl http://localhost:8000/api/v1/sentry-test
```

Check Sentry dashboard for the captured error.

---

## Configuration

### FastAPI Integration

Configured in `src/main.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.environment,
    release=f"{settings.app_name}@{settings.api_version}",

    # Performance monitoring
    traces_sample_rate=1.0,  # 100% in dev, 20% in production
    profiles_sample_rate=1.0,  # 100% in dev, 20% in production

    # Integrations
    integrations=[
        FastApiIntegration(transaction_style="endpoint"),
        LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors as events
        ),
    ],

    # Privacy
    send_default_pii=False,  # Don't send personally identifiable information
)
```

### Celery Integration

Configured in `src/tasks/celery_app.py`:

```python
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.environment,
    integrations=[
        CeleryIntegration(
            monitor_beat_tasks=True,  # Monitor scheduled tasks
            propagate_traces=True,    # Link tasks to API requests
        ),
        LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        ),
    ],
)
```

### Sample Rates by Environment

**Development**:

- `traces_sample_rate=1.0` (100% - capture everything)
- `profiles_sample_rate=1.0` (100% - profile everything)

**Staging**:

- `traces_sample_rate=0.5` (50% - half of transactions)
- `profiles_sample_rate=0.5` (50% - half of profiles)

**Production**:

- `traces_sample_rate=0.2` (20% - reduce overhead)
- `profiles_sample_rate=0.2` (20% - reduce overhead)

Adjust in `src/main.py` and `src/tasks/celery_app.py`:

```python
traces_sample_rate=1.0 if settings.environment == "development" else 0.2
```

---

## Error Tracking

### Automatic Error Capture

Sentry automatically captures:

1. **Unhandled Exceptions**: Any exception that reaches the top level
2. **HTTP Errors**: 4xx and 5xx responses (configurable)
3. **Task Failures**: Celery tasks that fail
4. **Database Errors**: SQLAlchemy exceptions

### Manual Error Capture

Capture specific errors:

```python
import sentry_sdk

try:
    # Risky operation
    process_payment(payment_id)
except PaymentGatewayError as e:
    sentry_sdk.capture_exception(e)
    logger.error(f"Payment gateway error: {e}")
    raise
```

### Adding Context

**User Context**:

```python
from sentry_sdk import set_user

set_user({
    "id": user.id,
    "email": user.email,
    "role": user.role.value,
})
```

**Tags**:

```python
from sentry_sdk import set_tag

set_tag("payment_gateway", "khalti")
set_tag("property_id", property_id)
set_tag("transaction_type", "rent_payment")
```

**Extra Context**:

```python
from sentry_sdk import set_context

set_context("payment", {
    "amount": payment.amount,
    "method": payment.payment_method.value,
    "tenant_id": payment.tenant_id,
    "status": payment.status.value,
})
```

**Breadcrumbs** (custom events):

```python
from sentry_sdk import add_breadcrumb

add_breadcrumb(
    category="payment",
    message="Initiating Khalti payment",
    level="info",
    data={"amount": 15000, "tenant": "tenant_123"}
)
```

### Error Filtering

Filter out specific errors in Sentry dashboard:

1. Go to **Settings** → **Inbound Filters**
2. Add patterns to ignore:
   - `ConnectionResetError` (transient network issues)
   - `404 Not Found` (expected for some endpoints)
   - Test errors during development

---

## Performance Monitoring

### Transaction Tracking

Sentry automatically tracks:

- **API Endpoints**: Request duration, status code
- **Database Queries**: Query duration, SQL statements
- **External Calls**: HTTP requests to payment gateways, S3, etc.
- **Celery Tasks**: Task execution time

### Custom Transactions

Track custom operations:

```python
from sentry_sdk import start_transaction

with start_transaction(op="task", name="generate_monthly_reports"):
    # Your code here
    generate_reports()
```

### Spans (Sub-operations)

Track specific operations within a transaction:

```python
from sentry_sdk import start_span

with start_transaction(op="payment", name="process_rent_payment"):
    with start_span(op="db", description="Fetch tenant"):
        tenant = db.query(Tenant).filter_by(id=tenant_id).first()

    with start_span(op="http", description="Call Khalti API"):
        response = khalti_service.initiate_payment(amount)

    with start_span(op="db", description="Save transaction"):
        db.add(transaction)
        db.commit()
```

### Performance Alerts

Configure in Sentry dashboard:

1. **Slow Endpoints**:

   - Metric: `transaction.duration`
   - Condition: `>= 5000ms` (5 seconds)
   - Action: Send Slack alert

2. **High Error Rate**:

   - Metric: `error_rate`
   - Condition: `>= 5%` in 5 minutes
   - Action: Email alert + PagerDuty

3. **Failed Tasks**:
   - Metric: `celery.task.failure`
   - Condition: `>= 10` failures in 10 minutes
   - Action: Email alert

---

## Alert Configuration

### Alert Rules

Create alerts in Sentry dashboard:

#### 1. Critical Errors

- **When**: Any error occurs
- **Conditions**:
  - `level` is `fatal` or `error`
  - `environment` is `production`
- **Actions**:
  - Send Slack message to `#alerts-production`
  - Email on-call engineer
  - Create PagerDuty incident (for fatal)

#### 2. Payment Gateway Failures

- **When**: Error with specific tag
- **Conditions**:
  - `tags.payment_gateway` is one of `khalti`, `esewa`, `imepay`
  - `event.count` >= 5 in 5 minutes
- **Actions**:
  - Send Slack message with payment details
  - Email finance team

#### 3. Database Connection Issues

- **When**: Database connection error
- **Conditions**:
  - `exception.type` is `OperationalError` or `InterfaceError`
  - `event.count` >= 3 in 5 minutes
- **Actions**:
  - Email DevOps team
  - Create PagerDuty incident

#### 4. High Memory Usage

- **When**: Performance issue
- **Conditions**:
  - `transaction.duration` >= 10000ms (10 seconds)
  - `event.count` >= 10 in 10 minutes
- **Actions**:
  - Send Slack alert
  - Email DevOps team

### Integration Setup

**Slack Integration**:

1. In Sentry: **Settings** → **Integrations** → **Slack**
2. Click **Add to Slack**
3. Select channel: `#alerts-production`
4. Configure alert routing

**Email Alerts**:

1. **Settings** → **Notifications**
2. Add email addresses for alerts
3. Configure frequency (immediate, daily digest, weekly)

**PagerDuty** (for critical alerts):

1. **Settings** → **Integrations** → **PagerDuty**
2. Add PagerDuty service key
3. Configure escalation policies

---

## Best Practices

### 1. Use Releases

Track errors by version:

```python
sentry_sdk.init(
    dsn=settings.sentry_dsn,
    release=f"meroghar-backend@{settings.api_version}",
)
```

Set release during deployment:

```bash
export SENTRY_RELEASE="meroghar-backend@$(git rev-parse HEAD)"
sentry-cli releases new "$SENTRY_RELEASE"
sentry-cli releases set-commits "$SENTRY_RELEASE" --auto
sentry-cli releases finalize "$SENTRY_RELEASE"
```

### 2. Group Errors Properly

Add fingerprinting for better grouping:

```python
from sentry_sdk import configure_scope

with configure_scope() as scope:
    scope.fingerprint = ["{{ default }}", str(tenant_id)]
```

### 3. Scrub Sensitive Data

Prevent sensitive data from being sent:

```python
sentry_sdk.init(
    dsn=settings.sentry_dsn,
    send_default_pii=False,  # Don't send PII
    before_send=scrub_sensitive_data,
)

def scrub_sensitive_data(event, hint):
    """Remove sensitive information before sending to Sentry."""
    # Remove password fields
    if 'request' in event:
        if 'data' in event['request']:
            data = event['request']['data']
            if isinstance(data, dict):
                data.pop('password', None)
                data.pop('secret_key', None)
                data.pop('api_key', None)

    return event
```

### 4. Monitor Business Metrics

Track custom metrics:

```python
from sentry_sdk import metrics

# Count successful payments
metrics.incr("payment.success", tags={"gateway": "khalti"})

# Track payment amounts
metrics.distribution("payment.amount", payment.amount)

# Gauge active users
metrics.gauge("users.active", active_user_count)
```

### 5. Set Context Early

Add context at the start of requests:

```python
from fastapi import Request
from sentry_sdk import set_user, set_tag

@app.middleware("http")
async def add_sentry_context(request: Request, call_next):
    # Add user context if authenticated
    if hasattr(request.state, "user"):
        set_user({
            "id": request.state.user.id,
            "role": request.state.user.role.value,
        })

    # Add request context
    set_tag("endpoint", request.url.path)
    set_tag("method", request.method)

    response = await call_next(request)
    return response
```

### 6. Test in Development

Verify Sentry is working:

```python
@app.get("/api/v1/sentry-test")
async def test_sentry():
    """Test endpoint to verify Sentry error reporting."""
    if settings.environment == "development":
        # This will be captured by Sentry
        raise ValueError("Sentry test error - monitoring is working!")
    return {"message": "Sentry test endpoint (only works in development)"}
```

---

## Troubleshooting

### Issue 1: Events Not Appearing in Sentry

**Symptoms**: No errors showing in Sentry dashboard

**Solutions**:

1. **Verify DSN**:

   ```bash
   echo $SENTRY_DSN
   ```

   Should output your Sentry DSN URL

2. **Check initialization**:
   Look for log message:

   ```
   INFO: Sentry monitoring initialized successfully
   ```

3. **Test manually**:

   ```python
   import sentry_sdk
   sentry_sdk.capture_message("Test message")
   ```

4. **Check firewall**:
   Ensure outbound HTTPS to `sentry.io` is allowed

5. **Verify environment**:
   ```python
   if settings.environment == "test":
       return None  # Events are filtered in test environment
   ```

### Issue 2: Too Many Events

**Symptoms**: Quota exhausted, high Sentry bills

**Solutions**:

1. **Reduce sample rates**:

   ```python
   traces_sample_rate=0.1,  # Only 10% of transactions
   ```

2. **Add inbound filters**:
   Filter out noisy errors in Sentry dashboard

3. **Use `before_send`**:

   ```python
   def before_send(event, hint):
       # Ignore specific errors
       if "ConnectionResetError" in str(hint.get("exc_info")):
           return None
       return event
   ```

4. **Set rate limits**:
   Sentry dashboard → Project Settings → Rate Limits

### Issue 3: Missing Context

**Symptoms**: Errors don't have user or transaction context

**Solutions**:

1. **Set user early**:
   Add middleware to set user context for all requests

2. **Use decorators**:

   ```python
   from functools import wraps

   def with_sentry_context(f):
       @wraps(f)
       async def wrapper(*args, **kwargs):
           set_tag("function", f.__name__)
           return await f(*args, **kwargs)
       return wrapper
   ```

3. **Check integrations**:
   Ensure FastAPI and Celery integrations are enabled

### Issue 4: Slow Performance

**Symptoms**: Application slower after enabling Sentry

**Solutions**:

1. **Reduce sample rates**:
   Set to 10-20% in production

2. **Disable profiling**:

   ```python
   profiles_sample_rate=0.0,  # Disable profiling
   ```

3. **Async transport**:
   Sentry uses async by default, but verify:
   ```python
   transport=sentry_sdk.transport.HttpTransport
   ```

### Issue 5: Database Credentials in Error Reports

**Symptoms**: Sensitive data visible in Sentry events

**Solutions**:

1. **Disable PII**:

   ```python
   send_default_pii=False
   ```

2. **Scrub in `before_send`**:

   ```python
   def scrub_sensitive_data(event, hint):
       # Remove database URLs
       if 'extra' in event:
           event['extra'].pop('DATABASE_URL', None)
       return event
   ```

3. **Use data scrubbing**:
   Sentry dashboard → Project Settings → Data Scrubbing
   - Enable "Scrub data"
   - Add patterns: `password`, `secret`, `api_key`, `dsn`

---

## Dashboard Overview

### Key Metrics to Monitor

1. **Error Rate**: Errors per minute/hour
2. **Crash-Free Sessions**: Percentage of sessions without errors
3. **Apdex Score**: Application performance index (target: >0.95)
4. **P95 Response Time**: 95th percentile response time (target: <500ms)
5. **Failed Celery Tasks**: Background task failures

### Custom Dashboards

Create dashboards for:

1. **Payment Monitoring**:

   - Payment success rate
   - Failed payment errors
   - Average payment processing time
   - Payment gateway performance comparison

2. **User Experience**:

   - Most common errors by user role
   - Slowest endpoints
   - Mobile vs API errors

3. **System Health**:
   - Database query performance
   - External API latency
   - Celery queue length
   - Memory/CPU usage patterns

---

## Resources

- **Sentry Documentation**: https://docs.sentry.io/platforms/python/
- **FastAPI Integration**: https://docs.sentry.io/platforms/python/guides/fastapi/
- **Celery Integration**: https://docs.sentry.io/platforms/python/guides/celery/
- **Performance Monitoring**: https://docs.sentry.io/product/performance/
- **Alert Rules**: https://docs.sentry.io/product/alerts/

---

## Summary

✅ Sentry is configured for comprehensive monitoring  
✅ FastAPI endpoints are tracked  
✅ Celery background tasks are monitored  
✅ Performance profiling is enabled  
✅ Alerts can be configured for critical issues  
✅ User and transaction context is captured  
✅ Sensitive data is protected

**Next Steps**:

1. Create Sentry account and get DSN
2. Add `SENTRY_DSN` to environment variables
3. Deploy to staging/production
4. Configure alert rules
5. Set up Slack/email integration
6. Monitor dashboard for first week
7. Adjust sample rates based on quota usage

For questions or issues, contact DevOps team or refer to the Sentry documentation.
