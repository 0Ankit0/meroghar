# Research & Technology Decisions
# Meroghar Rental Management System

**Date**: 2025-10-26  
**Feature**: 001-rental-management  
**Purpose**: Document all technology choices, best practices, and alternatives considered

---

## 1. Conflict Resolution Strategy for Offline Sync

### Decision
- **Non-financial data** (tenant profiles, settings): Last-write-wins based on timestamp comparison
- **Financial data** (payments, bills, expenses): Append-only with manual conflict resolution UI

### Rationale
Financial transactions require stronger consistency guarantees than profile data. Last-write-wins is acceptable for profile updates (name, phone) where occasional overwrites don't cause financial harm. However, for payments and bills, losing a transaction due to conflict resolution would violate financial integrity. Append-only ensures both conflicting records are preserved and flagged for human review.

### Alternatives Considered
1. **CRDTs (Conflict-free Replicated Data Types)**: Rejected due to complexity and limited SQLite support. Overkill for our use case.
2. **Vector clocks**: Rejected as too complex for mobile implementation and difficult to debug.
3. **Always prompt user for all conflicts**: Rejected as poor UX for non-critical profile changes.

### Implementation Notes
- Use `updated_at` timestamp (server-generated) as tie-breaker for LWW
- Device ID + local timestamp for conflict detection
- Conflict log table: `sync_conflicts` with both versions stored as JSON
- Intermediary UI shows side-by-side comparison: version A (device X, time T1) vs version B (device Y, time T2)

### References
- [Firebase Offline Capabilities](https://firebase.google.com/docs/database/android/offline-capabilities)
- [CouchDB Conflict Resolution](https://docs.couchdb.org/en/stable/replication/conflicts.html)
- [Stripe idempotency approach](https://stripe.com/docs/api/idempotent_requests)

---

## 2. PostgreSQL Row-Level Security (RLS) Implementation

### Decision
Use PostgreSQL Row-Level Security policies to enforce multi-tenant data isolation at database level.

### Rationale
RLS provides defense-in-depth: even if application-level query filtering fails, database enforces access control. Prevents entire class of authorization bugs. Performance impact minimal with proper indexes on `property_id` and `user_id`.

### Implementation Pattern
```sql
-- Enable RLS on tenants table
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

-- Policy: Tenants see only their own data
CREATE POLICY tenant_self_access ON tenants
  FOR ALL
  TO authenticated_user
  USING (user_id = current_setting('app.current_user_id')::uuid);

-- Policy: Intermediaries see their managed tenants
CREATE POLICY intermediary_access ON tenants
  FOR ALL
  TO authenticated_user
  USING (
    property_id IN (
      SELECT property_id FROM property_assignments
      WHERE intermediary_id = current_setting('app.current_user_id')::uuid
    )
  );

-- Policy: Owners see all tenants in their properties
CREATE POLICY owner_access ON tenants
  FOR ALL
  TO authenticated_user
  USING (
    property_id IN (
      SELECT id FROM properties
      WHERE owner_id = current_setting('app.current_user_id')::uuid
    )
  );
```

### Session Variable Pattern
FastAPI middleware sets session variable on each request:
```python
@app.middleware("http")
async def set_rls_context(request: Request, call_next):
    user_id = get_user_from_jwt(request)
    async with db.begin():
        await db.execute(f"SET LOCAL app.current_user_id = '{user_id}'")
        response = await call_next(request)
    return response
```

### Alternatives Considered
1. **Application-level filtering only**: Rejected due to risk of forgotten WHERE clauses causing data leaks
2. **Separate databases per tenant**: Rejected due to operational complexity (migrations, backups)
3. **Schema-based multi-tenancy**: Rejected as harder to query across properties for owner dashboard

### References
- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/14/ddl-rowsecurity.html)
- [Multi-tenant SaaS patterns](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/)

---

## 3. Bill Division Algorithm with Deterministic Remainder Handling

### Decision
Use Python's `decimal` module for exact arithmetic. Assign remainder cents to first tenant in sorted order (by ID) for deterministic results.

### Rationale
Floating-point arithmetic causes cumulative rounding errors in financial calculations. DECIMAL type with scale=2 for currency ensures exact cent-level precision. Remainder assignment must be deterministic to prevent disputes.

### Implementation
```python
from decimal import Decimal, ROUND_HALF_UP

def divide_bill(total_amount: Decimal, allocations: list[tuple[int, Decimal]]) -> dict[int, Decimal]:
    """
    Divide bill among tenants with deterministic remainder handling.
    
    Args:
        total_amount: Total bill amount
        allocations: List of (tenant_id, percentage) tuples
    
    Returns:
        Dict mapping tenant_id to allocated amount
    """
    # Calculate base amounts with 2 decimal places
    results = {}
    allocated_sum = Decimal('0.00')
    
    # Sort by tenant_id for deterministic order
    sorted_allocations = sorted(allocations, key=lambda x: x[0])
    
    for tenant_id, percentage in sorted_allocations[:-1]:
        amount = (total_amount * percentage / 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        results[tenant_id] = amount
        allocated_sum += amount
    
    # Last tenant gets remainder (handles rounding errors)
    last_tenant_id, last_percentage = sorted_allocations[-1]
    results[last_tenant_id] = total_amount - allocated_sum
    
    return results
```

### Alternatives Considered
1. **Round remainder up to nearest cent**: Rejected as changes total bill amount
2. **Split remainder equally**: Rejected as creates fractional cents
3. **Random remainder assignment**: Rejected as non-deterministic (different results on re-calculation)

### Test Cases
- Bill of ₹100.00 split 33.33% / 33.33% / 33.34% = ₹33.33 + ₹33.33 + ₹33.34 = ₹100.00 ✓
- Bill of ₹1000.00 split 25% / 25% / 25% / 25% = ₹250.00 × 4 = ₹1000.00 ✓
- Edge: ₹0.01 split 50% / 50% = ₹0.00 + ₹0.01 = ₹0.01 ✓

### References
- [Python decimal module](https://docs.python.org/3/library/decimal.html)
- [Stripe rounding approach](https://stripe.com/docs/currencies#zero-decimal)

---

## 4. JWT Token Strategy (Access + Refresh Tokens)

### Decision
Implement dual-token pattern:
- **Access token**: Short-lived (15 minutes), carries user ID and role
- **Refresh token**: Long-lived (7 days), stored securely, used to obtain new access tokens

### Rationale
Short-lived access tokens limit damage from token theft while avoiding constant re-authentication. Refresh tokens allow revocation (server-side blacklist) without invalidating all sessions. Balance between security and UX.

### Implementation
```python
# Token generation
def create_access_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=7),
        "type": "refresh",
        "jti": str(uuid4())  # Unique ID for revocation
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    # Store jti in Redis for revocation checks
    redis_client.setex(f"refresh_token:{payload['jti']}", 7*24*60*60, user_id)
    return token
```

### Token Refresh Flow
1. Client sends refresh token to `/api/v1/auth/refresh`
2. Backend validates refresh token and checks if revoked (Redis lookup)
3. If valid, issue new access token + new refresh token
4. Invalidate old refresh token in Redis

### Mobile Storage
- Access token: In-memory only (cleared on app kill)
- Refresh token: flutter_secure_storage (iOS Keychain, Android Keystore)

### Alternatives Considered
1. **Long-lived access tokens only**: Rejected due to security risk (no revocation)
2. **Session cookies**: Rejected as incompatible with mobile apps
3. **OAuth 2.0 with external provider**: Rejected as adds complexity for MVP (can add later)

### References
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)

---

## 5. Celery Task Queue Configuration for Recurring Bills

### Decision
Use Celery with Redis broker for background task processing. Celery Beat for periodic tasks (CRON-like scheduling).

### Rationale
Celery is mature, well-documented, and integrates seamlessly with FastAPI. Redis provides fast in-memory task queue. Celery Beat handles recurring bill creation without external CRON dependency.

### Configuration
```python
# celery_app.py
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "meroghar",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.beat_schedule = {
    "create-recurring-bills": {
        "task": "tasks.recurring_bills.create_monthly_bills",
        "schedule": crontab(hour=0, minute=0, day_of_month=1),  # 1st of month at midnight
    },
    "send-rent-reminders": {
        "task": "tasks.notifications.send_rent_reminders",
        "schedule": crontab(hour=9, minute=0),  # Daily at 9 AM
    },
}
```

### Task Example
```python
@celery_app.task
def create_monthly_bills():
    """Create bills for all recurring bill templates."""
    from models import RecurringBill, Bill
    from services.bill_service import create_bill_from_template
    
    recurring_bills = session.query(RecurringBill).filter_by(active=True).all()
    for template in recurring_bills:
        create_bill_from_template(template)
```

### Alternatives Considered
1. **APScheduler**: Rejected due to lack of distributed task support (single-process limitation)
2. **RQ (Redis Queue)**: Rejected as less feature-rich than Celery (no built-in Beat equivalent)
3. **System CRON**: Rejected as harder to monitor, test, and deploy

### Monitoring
- Flower: Web-based Celery monitoring tool
- Task retry policy: 3 retries with exponential backoff

### References
- [Celery Documentation](https://docs.celeryproject.org/en/stable/)
- [FastAPI with Celery](https://fastapi.tiangolo.com/tutorial/background-tasks/)

---

## 6. Flutter State Management: Provider vs Riverpod

### Decision
Start with **Provider** for MVP. Migrate to **Riverpod** if state complexity increases.

### Rationale
Provider is simpler, has extensive documentation, and sufficient for current requirements. Riverpod offers compile-time safety and better testing but steeper learning curve. Since spec doesn't indicate complex state interactions, Provider's simplicity wins for MVP.

### Provider Pattern
```dart
// Auth provider
class AuthProvider with ChangeNotifier {
  String? _accessToken;
  User? _currentUser;

  Future<void> login(String email, String password) async {
    final response = await apiService.login(email, password);
    _accessToken = response.accessToken;
    _currentUser = response.user;
    await secureStorage.write('refresh_token', response.refreshToken);
    notifyListeners();
  }

  void logout() {
    _accessToken = null;
    _currentUser = null;
    secureStorage.delete('refresh_token');
    notifyListeners();
  }
}

// Usage in widget
class TenantListScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);
    return Scaffold(/* ... */);
  }
}
```

### When to Consider Riverpod
- State management becomes error-prone (context issues)
- Need for complex dependency injection
- Testing requires heavy mocking

### Alternatives Considered
1. **Bloc**: Rejected as overkill for straightforward CRUD operations
2. **GetX**: Rejected due to anti-pattern concerns (global state, service locator)
3. **MobX**: Rejected as less idiomatic in Flutter community

### References
- [Provider Package](https://pub.dev/packages/provider)
- [Riverpod Documentation](https://riverpod.dev/)
- [Flutter State Management](https://docs.flutter.dev/data-and-backend/state-mgmt/options)

---

## 7. Payment Gateway Integration Strategy

### Decision
Implement adapter pattern for multiple payment gateways (Stripe, Razorpay, PayPal). Common interface with provider-specific implementations.

### Rationale
Different markets require different payment providers (Razorpay for India, Stripe for international). Adapter pattern allows easy addition of new providers without changing core payment logic. Single provider lock-in creates business risk.

### Interface Design
```python
from abc import ABC, abstractmethod

class PaymentGateway(ABC):
    @abstractmethod
    async def create_payment_intent(self, amount: Decimal, currency: str, metadata: dict) -> str:
        """Create payment intent, return client_secret."""
        pass
    
    @abstractmethod
    async def confirm_payment(self, payment_intent_id: str) -> PaymentResult:
        """Confirm payment and return result."""
        pass
    
    @abstractmethod
    async def refund_payment(self, transaction_id: str, amount: Decimal) -> RefundResult:
        """Process refund."""
        pass
    
    @abstractmethod
    async def handle_webhook(self, payload: bytes, signature: str) -> WebhookEvent:
        """Verify and process webhook."""
        pass

class StripeGateway(PaymentGateway):
    def __init__(self, api_key: str):
        self.stripe = stripe
        self.stripe.api_key = api_key
    
    async def create_payment_intent(self, amount: Decimal, currency: str, metadata: dict) -> str:
        intent = await self.stripe.PaymentIntent.create_async(
            amount=int(amount * 100),  # Stripe uses smallest currency unit
            currency=currency.lower(),
            metadata=metadata
        )
        return intent.client_secret

class RazorpayGateway(PaymentGateway):
    # Similar implementation for Razorpay
    pass
```

### Configuration
```python
# config.py
PAYMENT_GATEWAY = os.getenv("PAYMENT_GATEWAY", "stripe")  # stripe | razorpay | paypal

def get_payment_gateway() -> PaymentGateway:
    if PAYMENT_GATEWAY == "stripe":
        return StripeGateway(api_key=os.getenv("STRIPE_API_KEY"))
    elif PAYMENT_GATEWAY == "razorpay":
        return RazorpayGateway(key_id=os.getenv("RAZORPAY_KEY_ID"), key_secret=os.getenv("RAZORPAY_SECRET"))
    elif PAYMENT_GATEWAY == "paypal":
        return PayPalGateway(client_id=os.getenv("PAYPAL_CLIENT_ID"), secret=os.getenv("PAYPAL_SECRET"))
```

### Webhook Security
- Verify webhook signature using provider-specific method
- Idempotency: Use `transaction_id` or `payment_intent_id` to prevent duplicate processing
- Store raw webhook payload in `webhook_events` table for debugging

### Alternatives Considered
1. **Single gateway only**: Rejected due to market limitations (Razorpay India-only, Stripe limited in some countries)
2. **Payment aggregator (Chargebee, Paddle)**: Rejected due to added complexity and fees
3. **Cryptocurrency payments**: Rejected as not required for MVP (can add later)

### References
- [Stripe API Reference](https://stripe.com/docs/api)
- [Razorpay API Docs](https://razorpay.com/docs/api/)
- [PayPal REST API](https://developer.paypal.com/api/rest/)

---

## 8. Document Storage: S3 vs Local Filesystem

### Decision
Use **AWS S3** (or compatible: MinIO, DigitalOcean Spaces) for document storage.

### Rationale
S3 provides:
- Scalability without manual disk management
- Built-in redundancy (99.999999999% durability)
- Versioning support for document history
- Pre-signed URLs for secure temporary access
- Integration with CDN (CloudFront) for fast document delivery

Filesystem storage doesn't scale horizontally and requires manual backup/replication.

### Implementation
```python
import boto3
from datetime import timedelta

class DocumentService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    async def upload_document(self, file_content: bytes, property_id: str, tenant_id: str, doc_type: str) -> str:
        """Upload document and return S3 key."""
        key = f"properties/{property_id}/tenants/{tenant_id}/{doc_type}/{uuid4()}.pdf"
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=file_content,
            ServerSideEncryption='AES256',  # Encryption at rest
            Metadata={'property_id': property_id, 'tenant_id': tenant_id}
        )
        return key
    
    async def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate temporary URL for document access."""
        url = self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': key},
            ExpiresIn=expiration
        )
        return url
```

### Security
- **Encryption at rest**: S3 server-side encryption (AES-256)
- **Access control**: IAM roles, bucket policies (no public access)
- **Temporary access**: Pre-signed URLs (expire after 1 hour)
- **Virus scanning**: Integrate ClamAV for file upload scanning (async job)

### Cost Optimization
- S3 Standard for active documents
- S3 Glacier for archived documents (>2 years old)
- Lifecycle policies for automatic archival

### Alternatives Considered
1. **Local filesystem**: Rejected due to scalability and backup complexity
2. **Database BLOB storage**: Rejected due to poor performance at scale
3. **Google Cloud Storage**: Equivalent to S3, choice based on existing infrastructure

### References
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [boto3 Library](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [MinIO (S3-compatible)](https://min.io/docs/minio/linux/index.html)

---

## 9. Push Notifications: FCM Implementation

### Decision
Use **Firebase Cloud Messaging (FCM)** for both iOS and Android push notifications.

### Rationale
FCM provides unified API for both platforms, eliminating need for separate APNs integration. Free for unlimited messages. Well-documented Flutter integration via `firebase_messaging` package.

### Implementation
```dart
// Flutter notification service
class NotificationService {
  final FirebaseMessaging _fcm = FirebaseMessaging.instance;

  Future<void> initialize() async {
    // Request permission (iOS)
    NotificationSettings settings = await _fcm.requestPermission();
    
    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      String? token = await _fcm.getToken();
      await _sendTokenToServer(token);
      
      // Listen for token refresh
      _fcm.onTokenRefresh.listen(_sendTokenToServer);
      
      // Handle foreground messages
      FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
      
      // Handle background messages
      FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
    }
  }
  
  Future<void> _sendTokenToServer(String? token) async {
    if (token != null) {
      await apiService.updateDeviceToken(token);
    }
  }
}

// Background message handler (top-level function)
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  // Handle notification
}
```

### Backend Integration
```python
from firebase_admin import messaging

def send_notification(device_token: str, title: str, body: str, data: dict):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        data=data,
        token=device_token,
        android=messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                sound='default',
                channel_id='rent_reminders'
            )
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    sound='default',
                    badge=1
                )
            )
        )
    )
    response = messaging.send(message)
    return response
```

### Notification Categories
- **rent_reminders**: Payment due date approaching
- **bill_allocations**: New bill assigned to tenant
- **payment_confirmations**: Payment received
- **document_updates**: New document uploaded
- **system_alerts**: Account or security notifications

### Alternatives Considered
1. **OneSignal**: Rejected as FCM is free and sufficient for our needs
2. **Native APNs only (iOS)**: Rejected as requires separate Android solution
3. **SMS notifications only**: Rejected as more expensive and less rich (no actions, images)

### References
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)
- [flutter_messaging package](https://pub.dev/packages/firebase_messaging)

---

## 10. Internationalization (i18n) Implementation

### Decision
Use Flutter's built-in `intl` package with ARB (Application Resource Bundle) files for translations.

### Rationale
Flutter's official approach is well-integrated with tooling (code generation). ARB format is JSON-based and human-readable. Supports ICU message format for plurals, genders, and complex formatting.

### Implementation
```yaml
# pubspec.yaml
dependencies:
  flutter_localizations:
    sdk: flutter
  intl: ^0.18.0

flutter:
  generate: true
```

```yaml
# l10n.yaml
arb-dir: lib/l10n
template-arb-file: app_en.arb
output-localization-file: app_localizations.dart
```

```json
// lib/l10n/app_en.arb
{
  "@@locale": "en",
  "appTitle": "Meroghar",
  "login": "Login",
  "tenantCount": "{count, plural, =0{No tenants} =1{1 tenant} other{{count} tenants}}",
  "@tenantCount": {
    "placeholders": {
      "count": {"type": "int"}
    }
  },
  "paymentAmount": "₹{amount}",
  "@paymentAmount": {
    "placeholders": {
      "amount": {"type": "double", "format": "currency"}
    }
  }
}
```

```json
// lib/l10n/app_hi.arb (Hindi)
{
  "@@locale": "hi",
  "appTitle": "मेरोघर",
  "login": "लॉगिन",
  "tenantCount": "{count, plural, =0{कोई किरायेदार नहीं} =1{1 किरायेदार} other{{count} किरायेदार}}"
}
```

```dart
// Usage in widgets
Text(AppLocalizations.of(context)!.login)
Text(AppLocalizations.of(context)!.tenantCount(tenants.length))
```

### Supported Languages (MVP)
1. English (en) - default
2. Hindi (hi)
3. Spanish (es)

### RTL Support
```dart
MaterialApp(
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  localeResolutionCallback: (locale, supportedLocales) {
    // Auto-detect user's language
    for (var supportedLocale in supportedLocales) {
      if (supportedLocale.languageCode == locale?.languageCode) {
        return supportedLocale;
      }
    }
    return supportedLocales.first; // Fallback to English
  },
  builder: (context, child) {
    return Directionality(
      textDirection: AppLocalizations.of(context)!.localeName == 'ar' 
        ? TextDirection.rtl 
        : TextDirection.ltr,
      child: child!,
    );
  },
)
```

### Alternatives Considered
1. **easy_localization package**: Rejected as less official than Flutter's built-in approach
2. **JSON files with custom loader**: Rejected due to lack of tooling support
3. **Hardcoded translations**: Rejected as unmaintainable

### References
- [Flutter Internationalization](https://docs.flutter.dev/ui/accessibility-and-internationalization/internationalization)
- [ICU Message Format](https://unicode-org.github.io/icu/userguide/format_parse/messages/)

---

## 11. Testing Strategy: Pytest Configuration

### Decision
Use **pytest** with plugins for async testing, database fixtures, and coverage reporting.

### Rationale
pytest is the de facto standard for Python testing. Rich plugin ecosystem. Excellent fixture system for managing test database lifecycle.

### Configuration
```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for tests."""
    with PostgresContainer("postgres:14") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def test_db_engine(postgres_container):
    """Create SQLAlchemy engine connected to test database."""
    engine = create_engine(postgres_container.get_connection_url())
    # Run migrations
    alembic_upgrade(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(test_db_engine):
    """Provide clean database session for each test."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def auth_headers(db_session):
    """Create test user and return auth headers."""
    user = User(email="test@example.com", role="intermediary")
    db_session.add(user)
    db_session.commit()
    
    access_token = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {access_token}"}
```

### Test Organization
```python
# tests/unit/test_bill_division.py
from services.bill_service import divide_bill
from decimal import Decimal

def test_bill_division_three_equal_shares():
    """Test equal division among three tenants."""
    result = divide_bill(
        total_amount=Decimal('100.00'),
        allocations=[(1, Decimal('33.33')), (2, Decimal('33.33')), (3, Decimal('33.34'))]
    )
    assert result[1] == Decimal('33.33')
    assert result[2] == Decimal('33.33')
    assert result[3] == Decimal('33.34')
    assert sum(result.values()) == Decimal('100.00')

# tests/integration/test_payment_flow.py
@pytest.mark.asyncio
async def test_record_payment_updates_balance(client, auth_headers, db_session):
    """Test that recording payment updates tenant balance."""
    # Create tenant
    tenant = Tenant(name="John Doe", monthly_rent=Decimal('10000.00'))
    db_session.add(tenant)
    db_session.commit()
    
    # Record payment
    response = await client.post(
        "/api/v1/payments",
        json={"tenant_id": tenant.id, "amount": 5000.00, "payment_method": "cash"},
        headers=auth_headers
    )
    assert response.status_code == 201
    
    # Verify balance updated
    tenant = db_session.get(Tenant, tenant.id)
    assert tenant.calculate_balance() == Decimal('5000.00')
```

### Coverage Requirements
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = 
    --cov=src
    --cov-report=html
    --cov-report=term
    --cov-fail-under=80
    --asyncio-mode=auto
```

### CI Integration
```yaml
# .github/workflows/backend_ci.yml
- name: Run tests with coverage
  run: |
    pytest --cov=src --cov-report=xml
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Alternatives Considered
1. **unittest (stdlib)**: Rejected due to verbose syntax and lack of fixtures
2. **nose2**: Rejected as pytest has better plugin ecosystem
3. **Django's test framework**: N/A (not using Django)

### References
- [pytest Documentation](https://docs.pytest.org/)
- [testcontainers-python](https://testcontainers-python.readthedocs.io/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

---

## 12. Security: Certificate Pinning for Mobile

### Decision
Implement certificate pinning in Flutter mobile app to prevent man-in-the-middle (MITM) attacks.

### Rationale
Certificate pinning ensures mobile app only trusts specific SSL certificates for API communication. Protects against compromised CAs and network-level attacks. Critical for financial application security.

### Implementation
```dart
// Using dio with certificate pinning
import 'package:dio/dio.dart';
import 'package:dio/adapter.dart';

class ApiService {
  late Dio _dio;
  
  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: 'https://api.meroghar.com',
      connectTimeout: 10000,
      receiveTimeout: 10000,
    ));
    
    // Certificate pinning
    (_dio.httpClientAdapter as DefaultHttpClientAdapter).onHttpClientCreate = 
        (client) {
      client.badCertificateCallback = 
          (X509Certificate cert, String host, int port) {
        // Pin specific certificate fingerprint (SHA-256)
        const expectedFingerprint = 
            'E7:3E:4E:96:65:7F:9A:F7:05:4F:3E:9C:4C:0E:97:5B:51:71:D4:C0:4E:3C:57:1A:CA:67:05:26:CB:49:38:8C';
        
        String certFingerprint = sha256
            .convert(cert.der)
            .bytes
            .map((b) => b.toRadixString(16).padLeft(2, '0').toUpperCase())
            .join(':');
        
        if (certFingerprint == expectedFingerprint && host == 'api.meroghar.com') {
          return true; // Trust this certificate
        }
        return false; // Reject all other certificates
      };
      return client;
    };
  }
}
```

### Certificate Rotation Strategy
1. Backend serves multiple certificates (current + next)
2. Mobile app pins multiple fingerprints
3. When rotating, add new cert to backend first
4. Release app update with new fingerprint
5. Remove old cert after sufficient adoption

### Testing
```dart
// Integration test for certificate pinning
void main() {
  test('API rejects invalid certificate', () async {
    final apiService = ApiService();
    
    // Attempt connection to server with wrong certificate
    expect(
      () => apiService.get('/health'),
      throwsA(isA<DioError>().having(
        (e) => e.type, 
        'error type', 
        DioErrorType.other
      ))
    );
  });
}
```

### Alternatives Considered
1. **No pinning**: Rejected due to security risk for financial data
2. **Public key pinning**: Equivalent security, chose cert pinning for simpler rotation
3. **Pinning only in production**: Rejected as should test in staging too

### References
- [OWASP Certificate Pinning](https://owasp.org/www-community/controls/Certificate_and_Public_Key_Pinning)
- [Flutter Dio Package](https://pub.dev/packages/dio)

---

## Summary of Key Decisions

| Area | Decision | Primary Rationale |
|------|----------|-------------------|
| Sync Conflicts | LWW for profiles, append-only for financial | Financial data needs stronger consistency |
| Database Security | PostgreSQL RLS policies | Defense-in-depth, prevents SQL authorization bugs |
| Bill Division | Decimal arithmetic + deterministic remainder | Exact financial calculations, no disputes |
| Authentication | JWT access (15min) + refresh (7day) tokens | Balance security and UX |
| Background Jobs | Celery with Redis + Beat for CRON | Mature, distributed-ready, integrated monitoring |
| State Management | Provider (MVP), Riverpod (future) | Simplicity for current complexity level |
| Payment Gateways | Adapter pattern (Stripe, Razorpay, PayPal) | Market flexibility, avoid vendor lock-in |
| Document Storage | AWS S3 (or compatible) | Scalability, durability, versioning |
| Push Notifications | Firebase Cloud Messaging (FCM) | Unified iOS/Android, free, well-documented |
| Internationalization | Flutter intl + ARB files | Official approach, ICU format support |
| Testing | pytest + testcontainers + 80% coverage | Real database tests, industry standard |
| API Security | Certificate pinning in mobile | MITM protection for financial data |

---

**Research Complete**: All technology choices documented with rationale, alternatives, and implementation guidance. Ready for Phase 1 (data model and contracts).

**Next Steps**: Generate `data-model.md` and `/contracts/*.yaml` OpenAPI specifications.