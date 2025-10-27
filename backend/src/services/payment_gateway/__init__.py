"""Payment Gateway Factory and Base Classes.

Implements T113 from tasks.md.

This module provides a factory pattern for payment gateway integration,
allowing the system to support multiple payment providers (Khalti, eSewa, IME Pay)
with a unified interface.
"""

from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional, Protocol
from uuid import UUID


class PaymentGateway(str, Enum):
    """Supported payment gateways."""

    KHALTI = "khalti"
    ESEWA = "esewa"
    IMEPAY = "imepay"


class PaymentGatewayInterface(Protocol):
    """Protocol defining the interface all payment gateways must implement.

    This ensures consistent behavior across different payment providers.
    """

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
        **kwargs,
    ) -> dict[str, Any]:
        """Initiate a payment request.

        Args:
            amount: Payment amount in rupees
            purchase_order_id: Unique order identifier
            purchase_order_name: Order description
            return_url: Callback URL after payment
            website_url: Merchant website URL
            customer_name: Customer name (optional)
            customer_email: Customer email (optional)
            customer_phone: Customer phone (optional)
            **kwargs: Gateway-specific parameters

        Returns:
            Dict with payment_url, transaction_id, and expiration info
        """
        ...

    async def verify_payment(self, transaction_id: str) -> dict[str, Any]:
        """Verify payment status.

        Args:
            transaction_id: Payment transaction identifier

        Returns:
            Dict with status, amount, and transaction details
        """
        ...

    def is_payment_successful(self, verification_result: dict[str, Any]) -> bool:
        """Check if payment was successful.

        Args:
            verification_result: Result from verify_payment()

        Returns:
            True if payment completed successfully
        """
        ...

    def get_transaction_amount_in_rupees(self, verification_result: dict[str, Any]) -> Decimal:
        """Extract transaction amount in rupees.

        Args:
            verification_result: Result from verify_payment()

        Returns:
            Amount in rupees
        """
        ...

    def get_transaction_id(self, verification_result: dict[str, Any]) -> str | None:
        """Extract transaction ID.

        Args:
            verification_result: Result from verify_payment()

        Returns:
            Transaction ID if available
        """
        ...


class PaymentGatewayFactory:
    """Factory for creating payment gateway instances.

    Implements the factory pattern to instantiate appropriate payment gateway
    services based on the selected provider.
    """

    _gateways: dict[PaymentGateway, type] = {}

    @classmethod
    def register_gateway(cls, gateway: PaymentGateway, gateway_class: type) -> None:
        """Register a payment gateway implementation.

        Args:
            gateway: Gateway identifier
            gateway_class: Gateway implementation class
        """
        cls._gateways[gateway] = gateway_class

    @classmethod
    def create_gateway(cls, gateway: PaymentGateway, **kwargs) -> PaymentGatewayInterface:
        """Create a payment gateway instance.

        Args:
            gateway: Gateway to instantiate
            **kwargs: Gateway-specific configuration

        Returns:
            Payment gateway instance

        Raises:
            ValueError: If gateway is not registered
        """
        if gateway not in cls._gateways:
            raise ValueError(
                f"Payment gateway '{gateway}' is not registered. "
                f"Available gateways: {list(cls._gateways.keys())}"
            )

        gateway_class = cls._gateways[gateway]
        return gateway_class(**kwargs)

    @classmethod
    def get_available_gateways(cls) -> list[PaymentGateway]:
        """Get list of registered gateways.

        Returns:
            List of available payment gateways
        """
        return list(cls._gateways.keys())


# Register Khalti gateway
try:
    from .khalti_service import KhaltiPaymentGateway

    PaymentGatewayFactory.register_gateway(PaymentGateway.KHALTI, KhaltiPaymentGateway)
except ImportError:
    pass

# Register eSewa gateway (when implemented)
try:
    from .esewa_service import ESewaPaymentGateway

    PaymentGatewayFactory.register_gateway(PaymentGateway.ESEWA, ESewaPaymentGateway)
except ImportError:
    pass

# Register IME Pay gateway (when implemented)
try:
    from .imepay_service import IMEPayPaymentGateway

    PaymentGatewayFactory.register_gateway(PaymentGateway.IMEPAY, IMEPayPaymentGateway)
except ImportError:
    pass


__all__ = [
    "PaymentGateway",
    "PaymentGatewayInterface",
    "PaymentGatewayFactory",
]
