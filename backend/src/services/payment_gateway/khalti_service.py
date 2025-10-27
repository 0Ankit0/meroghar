"""Khalti Payment Gateway integration service.

Implements T110 from tasks.md.

Khalti Payment Gateway (KPG) is Nepal's leading digital wallet and payment solution.
This service handles payment initiation, verification, and webhook processing.

Documentation: https://docs.khalti.com/khalti-epayment/

Key Features:
- Payment initiation with unique purchase_order_id
- Payment verification via lookup API
- Support for sandbox and production environments
- Secure API authorization using secret keys

Flow:
1. Initiate payment -> Get pidx and payment_url
2. Redirect user to payment_url
3. User completes payment on Khalti portal
4. Khalti redirects to return_url with status
5. Verify payment using lookup API with pidx
6. Process payment confirmation
"""

import logging
from decimal import Decimal
from typing import Any

import httpx

from ...core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class KhaltiPaymentGateway:
    """Service for Khalti Payment Gateway integration."""

    # API Endpoints
    SANDBOX_BASE_URL = "https://dev.khalti.com/api/v2"
    PRODUCTION_BASE_URL = "https://khalti.com/api/v2"

    # Payment Portal URLs
    SANDBOX_PAYMENT_URL = "https://test-pay.khalti.com"
    PRODUCTION_PAYMENT_URL = "https://pay.khalti.com"

    # Status constants
    STATUS_COMPLETED = "Completed"
    STATUS_PENDING = "Pending"
    STATUS_INITIATED = "Initiated"
    STATUS_EXPIRED = "Expired"
    STATUS_USER_CANCELED = "User canceled"
    STATUS_REFUNDED = "Refunded"
    STATUS_PARTIALLY_REFUNDED = "Partially refunded"

    def __init__(
        self,
        secret_key: str | None = None,
        is_sandbox: bool = True,
        timeout: int = 30,
    ):
        """Initialize Khalti Payment Gateway service.

        Args:
            secret_key: Khalti secret key (live_secret_key from merchant dashboard)
            is_sandbox: Use sandbox environment for testing
            timeout: HTTP request timeout in seconds
        """
        self.secret_key = secret_key or settings.khalti_secret_key
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
                "Authorization": f"Key {self.secret_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

        logger.info(
            f"Khalti Payment Gateway initialized "
            f"(environment={'sandbox' if is_sandbox else 'production'})"
        )

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()

    async def initiate_payment(
        self,
        amount: Decimal,
        purchase_order_id: str,
        purchase_order_name: str,
        return_url: str,
        website_url: str,
        customer_name: str | None = None,
        customer_email: str | None = None,
        customer_phone: str | None = None,
        amount_breakdown: list[dict[str, Any]] | None = None,
        product_details: list[dict[str, Any]] | None = None,
        **merchant_extra,
    ) -> dict[str, Any]:
        """Initiate a payment request with Khalti.

        Args:
            amount: Total payment amount in rupees (will be converted to paisa)
            purchase_order_id: Unique order identifier from merchant system
            purchase_order_name: Name/description of the purchase
            return_url: URL where user will be redirected after payment
            website_url: Merchant website URL
            customer_name: Customer's full name (optional)
            customer_email: Customer's email (optional)
            customer_phone: Customer's phone number (optional)
            amount_breakdown: List of amount breakdown items (optional)
            product_details: List of product detail items (optional)
            **merchant_extra: Additional merchant-specific data (prefixed with merchant_)

        Returns:
            Dict containing:
                - pidx: Payment identifier
                - payment_url: URL to redirect user for payment
                - expires_at: Payment link expiration timestamp
                - expires_in: Expiration time in seconds

        Raises:
            ValueError: If validation fails
            httpx.HTTPStatusError: If API request fails
        """
        # Convert amount from rupees to paisa (1 rupee = 100 paisa)
        amount_in_paisa = int(amount * 100)

        # Validate amount (minimum 10 rupees = 1000 paisa)
        if amount_in_paisa < 1000:
            raise ValueError("Amount must be at least Rs. 10")

        # Build request payload
        payload = {
            "return_url": return_url,
            "website_url": website_url,
            "amount": amount_in_paisa,
            "purchase_order_id": purchase_order_id,
            "purchase_order_name": purchase_order_name,
        }

        # Add customer info if provided
        if customer_name or customer_email or customer_phone:
            payload["customer_info"] = {}
            if customer_name:
                payload["customer_info"]["name"] = customer_name
            if customer_email:
                payload["customer_info"]["email"] = customer_email
            if customer_phone:
                payload["customer_info"]["phone"] = customer_phone

        # Add amount breakdown if provided
        if amount_breakdown:
            # Validate that breakdown sum equals total amount
            breakdown_sum = sum(item.get("amount", 0) for item in amount_breakdown)
            if breakdown_sum != amount_in_paisa:
                raise ValueError(
                    f"Amount breakdown sum ({breakdown_sum}) "
                    f"does not match total amount ({amount_in_paisa})"
                )
            payload["amount_breakdown"] = amount_breakdown

        # Add product details if provided
        if product_details:
            payload["product_details"] = product_details

        # Add merchant extra data (prefixed with merchant_)
        for key, value in merchant_extra.items():
            if key.startswith("merchant_"):
                payload[key] = value

        try:
            logger.info(
                f"Initiating Khalti payment: order={purchase_order_id}, " f"amount=Rs.{amount}"
            )

            response = await self.client.post("/epayment/initiate/", json=payload)
            response.raise_for_status()

            data = response.json()

            logger.info(
                f"Khalti payment initiated successfully: "
                f"pidx={data.get('pidx')}, order={purchase_order_id}"
            )

            return data

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.text else {}
            logger.error(
                f"Khalti payment initiation failed: {e.response.status_code} - " f"{error_detail}"
            )
            raise ValueError(f"Payment initiation failed: {error_detail}")

        except Exception as e:
            logger.error(f"Unexpected error during payment initiation: {str(e)}")
            raise

    async def verify_payment(self, pidx: str) -> dict[str, Any]:
        """Verify payment status using lookup API.

        This should be called after receiving the payment callback to confirm
        the payment was actually completed.

        Args:
            pidx: Payment identifier received from initiate_payment

        Returns:
            Dict containing:
                - pidx: Payment identifier
                - total_amount: Total amount in paisa
                - status: Payment status (Completed, Pending, Expired, etc.)
                - transaction_id: Khalti transaction ID (if completed)
                - fee: Gateway fee charged
                - refunded: Whether payment has been refunded

        Raises:
            ValueError: If validation fails
            httpx.HTTPStatusError: If API request fails
        """
        if not pidx:
            raise ValueError("pidx is required for payment verification")

        payload = {"pidx": pidx}

        try:
            logger.info(f"Verifying Khalti payment: pidx={pidx}")

            response = await self.client.post("/epayment/lookup/", json=payload)
            response.raise_for_status()

            data = response.json()
            status = data.get("status")

            logger.info(f"Khalti payment verification result: pidx={pidx}, status={status}")

            return data

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.text else {}
            logger.error(
                f"Khalti payment verification failed: {e.response.status_code} - " f"{error_detail}"
            )
            raise ValueError(f"Payment verification failed: {error_detail}")

        except Exception as e:
            logger.error(f"Unexpected error during payment verification: {str(e)}")
            raise

    def is_payment_successful(self, verification_result: dict[str, Any]) -> bool:
        """Check if payment was successful based on verification result.

        Only "Completed" status should be treated as success.

        Args:
            verification_result: Result from verify_payment()

        Returns:
            True if payment is completed successfully, False otherwise
        """
        status = verification_result.get("status", "")
        return status == self.STATUS_COMPLETED

    def get_transaction_amount_in_rupees(self, verification_result: dict[str, Any]) -> Decimal:
        """Get transaction amount in rupees from verification result.

        Args:
            verification_result: Result from verify_payment()

        Returns:
            Amount in rupees (converted from paisa)
        """
        amount_in_paisa = verification_result.get("total_amount", 0)
        return Decimal(amount_in_paisa) / 100

    def get_transaction_id(self, verification_result: dict[str, Any]) -> str | None:
        """Get Khalti transaction ID from verification result.

        Args:
            verification_result: Result from verify_payment()

        Returns:
            Transaction ID if payment is completed, None otherwise
        """
        return verification_result.get("transaction_id")

    def parse_callback_params(self, callback_params: dict[str, str]) -> dict[str, Any]:
        """Parse and validate callback parameters from return_url.

        Khalti redirects to return_url with query parameters after payment.

        Args:
            callback_params: Query parameters from callback URL

        Returns:
            Parsed callback data with validated fields
        """
        return {
            "pidx": callback_params.get("pidx"),
            "txn_id": callback_params.get("txnId") or callback_params.get("transaction_id"),
            "amount": int(callback_params.get("amount", 0)),
            "total_amount": int(callback_params.get("total_amount", 0)),
            "status": callback_params.get("status"),
            "mobile": callback_params.get("mobile"),
            "purchase_order_id": callback_params.get("purchase_order_id"),
            "purchase_order_name": callback_params.get("purchase_order_name"),
        }

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Singleton instance for the application
_khalti_gateway: KhaltiPaymentGateway | None = None


def get_khalti_gateway() -> KhaltiPaymentGateway:
    """Get singleton Khalti gateway instance.

    Returns:
        KhaltiPaymentGateway instance
    """
    global _khalti_gateway

    if _khalti_gateway is None:
        _khalti_gateway = KhaltiPaymentGateway(
            secret_key=settings.khalti_secret_key,
            is_sandbox=settings.khalti_use_sandbox,
        )

    return _khalti_gateway


async def close_khalti_gateway():
    """Close the singleton Khalti gateway instance."""
    global _khalti_gateway

    if _khalti_gateway is not None:
        await _khalti_gateway.close()
        _khalti_gateway = None


__all__ = [
    "KhaltiPaymentGateway",
    "get_khalti_gateway",
    "close_khalti_gateway",
]
