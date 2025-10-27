"""IME Pay Payment Gateway integration service.

Implements T112 from tasks.md.

IME Pay is a leading digital wallet and payment service in Nepal, operated by
IME Group. This service handles payment initiation, verification, and webhook
processing for IME Pay payments.

Documentation: https://developer.imepay.com.np/

Key Features:
- Payment initiation with unique reference ID
- Payment verification via transaction status API
- Support for QR code and web-based payments
- Secure token-based authentication
- Real-time payment notifications

Flow:
1. Initiate payment -> Get transaction token and payment URL
2. Redirect user to IME Pay portal or show QR code
3. User completes payment via IME Pay app or web
4. IME Pay sends webhook notification
5. Verify payment using status API
6. Process payment confirmation
"""

import hashlib
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx

from ...core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class IMEPayPaymentGateway:
    """Service for IME Pay Payment Gateway integration."""

    # API Endpoints
    SANDBOX_BASE_URL = "https://stg.imepay.com.np:7979/api"
    PRODUCTION_BASE_URL = "https://payment.imepay.com.np:7979/api"

    # Payment Portal URLs
    SANDBOX_PAYMENT_URL = "https://stg.imepay.com.np:7979/WebCheckout"
    PRODUCTION_PAYMENT_URL = "https://payment.imepay.com.np:7979/WebCheckout"

    # Status constants
    STATUS_SUCCESS = "SUCCESS"
    STATUS_PENDING = "PENDING"
    STATUS_FAILED = "FAILED"
    STATUS_PROCESSING = "PROCESSING"
    STATUS_CANCELED = "CANCELED"
    STATUS_REFUNDED = "REFUNDED"
    STATUS_EXPIRED = "EXPIRED"

    def __init__(
        self,
        merchant_code: str | None = None,
        merchant_username: str | None = None,
        merchant_password: str | None = None,
        is_sandbox: bool = True,
        timeout: int = 30,
    ):
        """Initialize IME Pay Payment Gateway service.

        Args:
            merchant_code: IME Pay merchant code
            merchant_username: IME Pay merchant username for authentication
            merchant_password: IME Pay merchant password for authentication
            is_sandbox: Use sandbox environment for testing
            timeout: HTTP request timeout in seconds
        """
        self.merchant_code = merchant_code or settings.imepay_merchant_code
        self.merchant_username = merchant_username or settings.imepay_merchant_username
        self.merchant_password = merchant_password or settings.imepay_merchant_password
        self.is_sandbox = is_sandbox
        self.timeout = timeout

        # Set appropriate URLs based on environment
        self.base_url = self.SANDBOX_BASE_URL if is_sandbox else self.PRODUCTION_BASE_URL
        self.payment_portal_url = (
            self.SANDBOX_PAYMENT_URL if is_sandbox else self.PRODUCTION_PAYMENT_URL
        )

        # HTTP client configuration
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=timeout,
        )

        # Authentication token (will be obtained on first API call)
        self._auth_token: str | None = None
        self._token_expires: datetime | None = None

        logger.info(
            f"IME Pay Payment Gateway initialized "
            f"(environment={'sandbox' if is_sandbox else 'production'})"
        )

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()

    def _generate_token_hash(self) -> str:
        """Generate authentication token hash.

        IME Pay uses SHA256 hash of Username:Password:MerchantCode

        Returns:
            SHA256 hash string
        """
        auth_string = f"{self.merchant_username}:{self.merchant_password}:{self.merchant_code}"
        return hashlib.sha256(auth_string.encode("utf-8")).hexdigest().upper()

    async def _get_auth_token(self, force_refresh: bool = False) -> str:
        """Get authentication token (cached or fetch new).

        Args:
            force_refresh: Force token refresh even if cached token is valid

        Returns:
            Authentication token

        Raises:
            ValueError: If authentication fails
        """
        # Check if we have a valid cached token
        if (
            not force_refresh
            and self._auth_token
            and self._token_expires
            and datetime.now() < self._token_expires
        ):
            return self._auth_token

        try:
            # Get new token
            token_hash = self._generate_token_hash()

            payload = {
                "MerchantCode": self.merchant_code,
                "TokenHash": token_hash,
            }

            logger.info("Requesting IME Pay authentication token")

            response = await self.client.post("/WebCheckout/GetToken", json=payload)
            response.raise_for_status()

            data = response.json()

            if data.get("ResponseCode") != "0":
                raise ValueError(f"Token request failed: {data.get('ResponseMessage')}")

            self._auth_token = data.get("TokenId")
            # Token typically valid for 30 minutes
            self._token_expires = datetime.now() + timedelta(minutes=25)

            logger.info("IME Pay authentication token obtained successfully")

            return self._auth_token

        except Exception as e:
            logger.error(f"Error obtaining IME Pay auth token: {str(e)}")
            raise ValueError(f"Authentication failed: {str(e)}")

    async def initiate_payment(
        self,
        amount: Decimal,
        reference_id: str,
        merchant_name: str,
        success_url: str,
        failure_url: str,
        cancel_url: str,
        customer_name: str | None = None,
        customer_email: str | None = None,
        customer_phone: str | None = None,
        delivery_charge: Decimal | None = None,
        service_charge: Decimal | None = None,
        tax_amount: Decimal | None = None,
        product_details: str | None = None,
    ) -> dict[str, Any]:
        """Initiate a payment request with IME Pay.

        Args:
            amount: Payment amount in rupees
            reference_id: Unique merchant reference ID
            merchant_name: Merchant/business name
            success_url: URL for successful payment redirect
            failure_url: URL for failed payment redirect
            cancel_url: URL for canceled payment redirect
            customer_name: Customer's full name (optional)
            customer_email: Customer's email (optional)
            customer_phone: Customer's phone number (optional)
            delivery_charge: Delivery charge amount (optional)
            service_charge: Service charge amount (optional)
            tax_amount: Tax amount (optional)
            product_details: Product description (optional)

        Returns:
            Dict containing:
                - transaction_id: IME Pay transaction identifier
                - payment_url: URL to redirect user for payment
                - qr_code_url: URL for QR code (if supported)
                - expires_at: Payment expiration timestamp

        Raises:
            ValueError: If validation fails
            httpx.HTTPStatusError: If API request fails
        """
        # Validate amount (minimum 10 rupees)
        if amount < Decimal("10.00"):
            raise ValueError("Amount must be at least Rs. 10")

        # Get authentication token
        token = await self._get_auth_token()

        # Calculate total amount
        total_amount = amount
        if delivery_charge:
            total_amount += delivery_charge
        if service_charge:
            total_amount += service_charge
        if tax_amount:
            total_amount += tax_amount

        # Build request payload
        payload = {
            "TokenId": token,
            "MerchantCode": self.merchant_code,
            "Amount": str(amount),
            "RefId": reference_id,
            "TranAmount": str(total_amount),
            "Method": "GET",
            "RespUrl": success_url,
            "CancelUrl": cancel_url,
            "FailUrl": failure_url,
            "Msisdn": customer_phone or "",
            "CustomerName": customer_name or "",
            "CustomerEmail": customer_email or "",
            "MerchantName": merchant_name,
            "DeliveryCharge": str(delivery_charge or 0),
            "ServiceCharge": str(service_charge or 0),
            "TaxAmount": str(tax_amount or 0),
            "ProductDetails": product_details or "",
        }

        try:
            logger.info(f"Initiating IME Pay payment: ref={reference_id}, " f"amount=Rs.{amount}")

            response = await self.client.post(
                "/WebCheckout/Checkout",
                json=payload,
            )
            response.raise_for_status()

            data = response.json()

            # Check response code
            if data.get("ResponseCode") != "0":
                raise ValueError(f"Payment initiation failed: {data.get('ResponseMessage')}")

            transaction_id = data.get("TransactionId")
            payment_url = f"{self.payment_portal_url}/?TranToken={transaction_id}"

            logger.info(
                f"IME Pay payment initiated successfully: "
                f"txn={transaction_id}, ref={reference_id}"
            )

            return {
                "transaction_id": transaction_id,
                "reference_id": reference_id,
                "payment_url": payment_url,
                "token": token,
                "total_amount": float(total_amount),
                "expires_at": datetime.now() + timedelta(minutes=30),
                "raw_response": data,
            }

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.text else {}
            logger.error(
                f"IME Pay payment initiation failed: {e.response.status_code} - " f"{error_detail}"
            )
            raise ValueError(f"Payment initiation failed: {error_detail}")

        except Exception as e:
            logger.error(f"Unexpected error during payment initiation: {str(e)}")
            raise

    async def verify_payment(
        self,
        transaction_id: str,
        reference_id: str,
        amount: Decimal,
    ) -> dict[str, Any]:
        """Verify payment status using IME Pay confirmation API.

        This should be called after receiving the payment callback to confirm
        the payment was actually completed.

        Args:
            transaction_id: IME Pay transaction identifier
            reference_id: Merchant reference ID
            amount: Transaction amount for verification

        Returns:
            Dict containing:
                - transaction_id: Transaction identifier
                - reference_id: Merchant reference ID
                - status: Payment status
                - amount: Transaction amount
                - msisdn: Customer phone number
                - transaction_date: Transaction completion date

        Raises:
            ValueError: If validation fails
            httpx.HTTPStatusError: If API request fails
        """
        if not transaction_id:
            raise ValueError("transaction_id is required for payment verification")

        # Get authentication token
        token = await self._get_auth_token()

        payload = {
            "TokenId": token,
            "MerchantCode": self.merchant_code,
            "TransactionId": transaction_id,
            "RefId": reference_id,
            "Amount": str(amount),
        }

        try:
            logger.info(f"Verifying IME Pay payment: txn={transaction_id}")

            response = await self.client.post(
                "/WebCheckout/ConfirmTransaction",
                json=payload,
            )
            response.raise_for_status()

            data = response.json()

            # Check response code
            response_code = data.get("ResponseCode")
            if response_code == "0":
                status = self.STATUS_SUCCESS
                logger.info(
                    f"IME Pay payment verified successfully: "
                    f"txn={transaction_id}, ref={reference_id}"
                )
            elif response_code == "1":
                status = self.STATUS_PENDING
                logger.warning(f"IME Pay payment pending: txn={transaction_id}")
            else:
                status = self.STATUS_FAILED
                logger.warning(
                    f"IME Pay payment verification failed: "
                    f"txn={transaction_id}, msg={data.get('ResponseMessage')}"
                )

            return {
                "transaction_id": transaction_id,
                "reference_id": reference_id,
                "status": status,
                "amount": float(amount),
                "msisdn": data.get("Msisdn"),
                "transaction_date": data.get("TransactionDate"),
                "response_code": response_code,
                "response_message": data.get("ResponseMessage"),
                "raw_response": data,
            }

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.text else {}
            logger.error(
                f"IME Pay payment verification failed: {e.response.status_code} - "
                f"{error_detail}"
            )
            raise ValueError(f"Payment verification failed: {error_detail}")

        except Exception as e:
            logger.error(f"Unexpected error during payment verification: {str(e)}")
            raise

    async def refund_payment(
        self,
        transaction_id: str,
        reference_id: str,
        amount: Decimal,
        remarks: str | None = None,
    ) -> dict[str, Any]:
        """Request refund for a completed payment.

        Args:
            transaction_id: IME Pay transaction identifier
            reference_id: Merchant reference ID
            amount: Amount to refund
            remarks: Refund reason/remarks (optional)

        Returns:
            Dict containing refund status and details

        Raises:
            ValueError: If validation fails
            httpx.HTTPStatusError: If API request fails
        """
        # Get authentication token
        token = await self._get_auth_token()

        payload = {
            "TokenId": token,
            "MerchantCode": self.merchant_code,
            "TransactionId": transaction_id,
            "RefId": reference_id,
            "Amount": str(amount),
            "Remarks": remarks or "Refund requested",
        }

        try:
            logger.info(f"Requesting IME Pay refund: txn={transaction_id}, " f"amount=Rs.{amount}")

            response = await self.client.post(
                "/WebCheckout/ReconfirmTransaction",
                json=payload,
            )
            response.raise_for_status()

            data = response.json()

            logger.info(
                f"IME Pay refund processed: txn={transaction_id}, "
                f"status={data.get('ResponseMessage')}"
            )

            return {
                "transaction_id": transaction_id,
                "reference_id": reference_id,
                "status": (
                    self.STATUS_REFUNDED if data.get("ResponseCode") == "0" else self.STATUS_FAILED
                ),
                "amount": float(amount),
                "response_message": data.get("ResponseMessage"),
                "raw_response": data,
            }

        except Exception as e:
            logger.error(f"Error processing IME Pay refund: {str(e)}")
            raise
