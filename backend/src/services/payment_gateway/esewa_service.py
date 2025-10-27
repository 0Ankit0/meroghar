"""eSewa Payment Gateway integration service.

Implements T111 from tasks.md.

eSewa is one of Nepal's most popular digital payment solutions, providing
digital wallet and payment services. This service handles payment initiation,
verification, and webhook processing for eSewa payments.

Documentation: https://developer.esewa.com.np/

Key Features:
- Payment initiation with unique transaction UUID
- Payment verification via status check API
- Support for sandbox and production environments
- Secure signature-based authentication

Flow:
1. Initiate payment -> Generate payment form data
2. Submit form to eSewa portal (POST)
3. User completes payment on eSewa
4. eSewa redirects to success/failure URL
5. Verify payment using status API
6. Process payment confirmation
"""
import hashlib
import hmac
import logging
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import uuid4

import httpx

from ...core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ESewaPaymentGateway:
    """Service for eSewa Payment Gateway integration."""

    # API Endpoints
    SANDBOX_BASE_URL = "https://rc-epay.esewa.com.np/api"
    PRODUCTION_BASE_URL = "https://epay.esewa.com.np/api"

    # Payment Portal URLs
    SANDBOX_PAYMENT_URL = "https://rc-epay.esewa.com.np/main/v2/form"
    PRODUCTION_PAYMENT_URL = "https://epay.esewa.com.np/main/v2/form"

    # Status constants
    STATUS_SUCCESS = "COMPLETE"
    STATUS_PENDING = "PENDING"
    STATUS_FAILED = "FAILED"
    STATUS_INITIATED = "INITIATED"
    STATUS_CANCELED = "CANCELED"
    STATUS_REFUNDED = "REFUNDED"

    def __init__(
        self,
        merchant_id: Optional[str] = None,
        merchant_secret: Optional[str] = None,
        is_sandbox: bool = True,
        timeout: int = 30,
    ):
        """Initialize eSewa Payment Gateway service.

        Args:
            merchant_id: eSewa merchant ID
            merchant_secret: eSewa merchant secret key for signature generation
            is_sandbox: Use sandbox environment for testing
            timeout: HTTP request timeout in seconds
        """
        self.merchant_id = merchant_id or settings.esewa_merchant_id
        self.merchant_secret = merchant_secret or settings.esewa_merchant_secret
        self.is_sandbox = is_sandbox
        self.timeout = timeout

        # Set appropriate URLs based on environment
        self.base_url = (
            self.SANDBOX_BASE_URL if is_sandbox else self.PRODUCTION_BASE_URL
        )
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

        logger.info(
            f"eSewa Payment Gateway initialized "
            f"(environment={'sandbox' if is_sandbox else 'production'})"
        )

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()

    def _generate_signature(
        self,
        total_amount: str,
        transaction_uuid: str,
        product_code: str,
    ) -> str:
        """Generate HMAC-SHA256 signature for payment request.

        Args:
            total_amount: Total amount as string
            transaction_uuid: Unique transaction identifier
            product_code: Merchant product code

        Returns:
            Base64 encoded signature
        """
        # Create message in format: total_amount,transaction_uuid,product_code
        message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"

        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.merchant_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        # Convert to base64
        import base64
        return base64.b64encode(signature).decode("utf-8")

    async def initiate_payment(
        self,
        amount: Decimal,
        product_code: str,
        product_name: str,
        success_url: str,
        failure_url: str,
        transaction_uuid: Optional[str] = None,
        tax_amount: Optional[Decimal] = None,
        service_charge: Optional[Decimal] = None,
        delivery_charge: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """Initiate a payment request with eSewa.

        Args:
            amount: Product amount (excluding tax, service, and delivery charges)
            product_code: Merchant product code (NP-ES-XXXX from eSewa)
            product_name: Name/description of the product
            success_url: URL where user will be redirected on successful payment
            failure_url: URL where user will be redirected on failed payment
            transaction_uuid: Unique transaction identifier (auto-generated if not provided)
            tax_amount: Tax amount (optional)
            service_charge: Service charge amount (optional)
            delivery_charge: Delivery charge amount (optional)

        Returns:
            Dict containing:
                - transaction_uuid: Unique transaction identifier
                - payment_url: URL to redirect user for payment
                - form_data: Data to be submitted in payment form
                - signature: Generated signature for verification

        Raises:
            ValueError: If validation fails
        """
        # Generate transaction UUID if not provided
        if not transaction_uuid:
            transaction_uuid = str(uuid4())

        # Validate amount (minimum 10 rupees)
        if amount < Decimal("10.00"):
            raise ValueError("Amount must be at least Rs. 10")

        # Calculate total amount
        total_amount = amount
        if tax_amount:
            total_amount += tax_amount
        if service_charge:
            total_amount += service_charge
        if delivery_charge:
            total_amount += delivery_charge

        # Format amounts as strings with 2 decimal places
        amount_str = f"{amount:.2f}"
        total_amount_str = f"{total_amount:.2f}"
        tax_amount_str = f"{tax_amount:.2f}" if tax_amount else "0.00"
        service_charge_str = f"{service_charge:.2f}" if service_charge else "0.00"
        delivery_charge_str = f"{delivery_charge:.2f}" if delivery_charge else "0.00"

        # Generate signature
        signature = self._generate_signature(
            total_amount_str,
            transaction_uuid,
            product_code,
        )

        # Build form data for payment
        form_data = {
            "amount": amount_str,
            "tax_amount": tax_amount_str,
            "total_amount": total_amount_str,
            "transaction_uuid": transaction_uuid,
            "product_code": product_code,
            "product_service_charge": service_charge_str,
            "product_delivery_charge": delivery_charge_str,
            "success_url": success_url,
            "failure_url": failure_url,
            "signed_field_names": "total_amount,transaction_uuid,product_code",
            "signature": signature,
        }

        logger.info(
            f"Initiated eSewa payment: uuid={transaction_uuid}, "
            f"amount=Rs.{amount}, total=Rs.{total_amount}"
        )

        return {
            "transaction_uuid": transaction_uuid,
            "payment_url": self.payment_portal_url,
            "form_data": form_data,
            "signature": signature,
            "product_name": product_name,
        }

    async def verify_payment(
        self,
        transaction_uuid: str,
        product_code: str,
        total_amount: Decimal,
        reference_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Verify payment status using eSewa transaction status API.

        This should be called after receiving the success callback to confirm
        the payment was actually completed.

        Args:
            transaction_uuid: Unique transaction identifier
            product_code: Merchant product code
            total_amount: Total payment amount for verification
            reference_id: eSewa reference ID from callback (optional)

        Returns:
            Dict containing:
                - transaction_uuid: Transaction identifier
                - product_code: Product code
                - status: Payment status
                - total_amount: Total amount
                - reference_id: eSewa reference ID
                - transaction_code: eSewa transaction code

        Raises:
            ValueError: If validation fails
            httpx.HTTPStatusError: If API request fails
        """
        if not transaction_uuid:
            raise ValueError("transaction_uuid is required for payment verification")

        # Format amount as string
        total_amount_str = f"{total_amount:.2f}"

        # Build query parameters
        params = {
            "product_code": product_code,
            "total_amount": total_amount_str,
            "transaction_uuid": transaction_uuid,
        }

        try:
            logger.info(f"Verifying eSewa payment: uuid={transaction_uuid}")

            response = await self.client.get(
                "/epay/transaction/status/",
                params=params,
            )
            response.raise_for_status()

            data = response.json()

            # Check if payment is successful
            status = data.get("status", "").upper()
            if status == self.STATUS_SUCCESS:
                logger.info(
                    f"eSewa payment verified successfully: "
                    f"uuid={transaction_uuid}, ref={data.get('reference_id')}"
                )
            else:
                logger.warning(
                    f"eSewa payment verification returned status: "
                    f"{status} for uuid={transaction_uuid}"
                )

            return {
                "transaction_uuid": transaction_uuid,
                "product_code": product_code,
                "status": status,
                "total_amount": float(data.get("total_amount", 0)),
                "reference_id": data.get("reference_id"),
                "transaction_code": data.get("transaction_code"),
                "raw_response": data,
            }

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.text else {}
            logger.error(
                f"eSewa payment verification failed: {e.response.status_code} - "
                f"{error_detail}"
            )
            raise ValueError(f"Payment verification failed: {error_detail}")

        except Exception as e:
            logger.error(f"Unexpected error during payment verification: {str(e)}")
            raise

    def verify_callback_signature(
        self,
        transaction_uuid: str,
        product_code: str,
        total_amount: str,
        received_signature: str,
    ) -> bool:
        """Verify the signature received in payment callback.

        Args:
            transaction_uuid: Transaction UUID from callback
            product_code: Product code from callback
            total_amount: Total amount from callback
            received_signature: Signature received in callback

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Generate expected signature
            expected_signature = self._generate_signature(
                total_amount,
                transaction_uuid,
                product_code,
            )

            # Compare signatures
            is_valid = hmac.compare_digest(expected_signature, received_signature)

            if is_valid:
                logger.info(f"eSewa callback signature verified: uuid={transaction_uuid}")
            else:
                logger.warning(
                    f"eSewa callback signature mismatch: uuid={transaction_uuid}"
                )

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying callback signature: {str(e)}")
            return False

    async def check_transaction_status(self, transaction_uuid: str) -> str:
        """Quick check of transaction status.

        Args:
            transaction_uuid: Unique transaction identifier

        Returns:
            Transaction status (SUCCESS, PENDING, FAILED, etc.)
        """
        try:
            # Note: This requires knowing the product_code and amount
            # In practice, these should be retrieved from your database
            # This is a simplified version
            logger.info(f"Checking eSewa transaction status: uuid={transaction_uuid}")

            # Return pending by default - actual implementation should query the database
            # and then verify with eSewa if needed
            return self.STATUS_PENDING

        except Exception as e:
            logger.error(f"Error checking transaction status: {str(e)}")
            return self.STATUS_FAILED
