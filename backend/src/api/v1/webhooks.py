"""Webhook handlers for payment gateway callbacks.

Implements T115-T117 from tasks.md.
Handles callbacks from Khalti, eSewa, and IME Pay payment gateways.
"""
import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_current_user
from ...core.database import get_async_db
from ...models.payment import Payment, PaymentStatus
from ...models.tenant import Tenant
from ...models.user import User
from ...models.notification import NotificationPriority, NotificationType
from ...services.payment_gateway import PaymentGateway, PaymentGatewayFactory
from ...services.payment_service import PaymentService
from ...services.notification_service import NotificationService
from ...tasks.notification_tasks import send_payment_confirmation

# Configure logger for webhook endpoints
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/khalti",
    status_code=status.HTTP_200_OK,
    summary="Khalti payment callback handler",
    description="""
    Handle Khalti payment gateway callback after user completes payment.
    Khalti redirects user to this URL with payment status in query parameters.
    
    This endpoint:
    1. Receives callback parameters (pidx, status, transaction_id, etc.)
    2. Verifies payment status with Khalti lookup API
    3. Updates payment record in database
    4. Redirects user to appropriate success/failure page
    """,
)
async def khalti_callback(
    session: Annotated[AsyncSession, Depends(get_async_db)],
    pidx: str = Query(..., description="Khalti payment identifier"),
    purchase_order_id: str = Query(..., description="Original purchase order ID"),
    status_param: str = Query(..., alias="status", description="Payment status"),
    txnId: Optional[str] = Query(None, description="Transaction ID from Khalti"),
    amount: Optional[int] = Query(None, description="Amount in paisa"),
    mobile: Optional[str] = Query(None, description="Payer mobile number"),
    purchase_order_name: Optional[str] = Query(None, description="Purchase order name"),
    transaction_id: Optional[str] = Query(None, description="Transaction ID"),
) -> dict:
    """
    Process Khalti payment callback.
    
    Args:
        pidx: Khalti payment index from initiate response
        txnId: Transaction ID if payment successful
        amount: Payment amount in paisa
        mobile: Payer's Khalti mobile number
        purchase_order_id: Original purchase order ID (format: PAY-{tenant_id}-{timestamp})
        purchase_order_name: Purchase order name
        transaction_id: Same as txnId
        status_param: Payment status ('Completed', 'Pending', 'User canceled', etc.)
        session: Database session
        
    Returns:
        Success/failure message with redirect instructions
        
    Raises:
        HTTPException: If payment not found or verification fails
    """
    logger.info(
        f"Khalti callback received: pidx={pidx}, status={status_param}, "
        f"purchase_order_id={purchase_order_id}, transaction_id={transaction_id}"
    )
    
    try:
        # Extract payment ID from purchase_order_id (format: PAY-{tenant_id}-{timestamp})
        parts = purchase_order_id.split("-")
        if len(parts) < 2:
            logger.error(f"Invalid purchase_order_id format: {purchase_order_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid purchase order ID format"
            )
        
        # Find payment by purchase_order_id in metadata
        query = select(Payment).where(
            Payment.metadata["purchase_order_id"].astext == purchase_order_id
        )
        result = await session.execute(query)
        payment = result.scalar_one_or_none()
        
        if not payment:
            logger.error(f"Payment not found for purchase_order_id: {purchase_order_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment not found for purchase order {purchase_order_id}"
            )
        
        # Verify payment with Khalti lookup API
        gateway = PaymentGatewayFactory.create_gateway(PaymentGateway.KHALTI)
        verification = await gateway.verify_payment(pidx)
        
        logger.info(f"Khalti verification response: {verification}")
        
        # Update payment based on verification status
        if verification.get("status") == "Completed":
            payment.status = PaymentStatus.COMPLETED
            payment.gateway_transaction_id = verification.get("transaction_id")
            payment.metadata = payment.metadata or {}
            payment.metadata.update({
                "khalti_pidx": pidx,
                "khalti_transaction_id": verification.get("transaction_id"),
                "khalti_fee": verification.get("fee", 0),
                "khalti_total_amount": verification.get("total_amount"),
                "payer_mobile": mobile,
                "verified_at": verification.get("verified_at"),
            })
            
            # Commit payment status update first
            await session.commit()
            await session.refresh(payment)
            
            logger.info(
                f"Payment {payment.id} marked as COMPLETED. "
                f"Transaction ID: {verification.get('transaction_id')}"
            )
            
            # T121: Auto-generate receipt after successful payment
            payment_service = PaymentService(session)
            receipt_path = await payment_service.auto_generate_receipt(payment.id)
            
            if receipt_path:
                logger.info(f"Receipt auto-generated at: {receipt_path}")
            else:
                logger.warning(f"Receipt auto-generation failed for payment {payment.id}")
            
            # T242: Send payment notification to intermediary/owner
            try:
                # Get tenant to find property owner/intermediaries
                tenant_result = await session.execute(
                    select(Tenant).where(Tenant.id == payment.tenant_id)
                )
                tenant = tenant_result.scalar_one_or_none()
                
                if tenant:
                    # Notify property owner and assigned intermediaries
                    property_result = await session.execute(
                        select(User).where(User.id == tenant.property.owner_id)
                    )
                    owner = property_result.scalar_one_or_none()
                    
                    if owner:
                        await NotificationService.create_notification(
                            db=session,
                            user_id=owner.id,
                            title="Payment Received",
                            body=(
                                f"Payment of {payment.currency} {payment.amount} "
                                f"received from {tenant.user.full_name}"
                            ),
                            notification_type=NotificationType.PAYMENT_RECEIVED,
                            priority=NotificationPriority.HIGH,
                            deep_link=f"meroghar://payments/{payment.id}",
                            metadata={
                                "payment_id": str(payment.id),
                                "tenant_id": str(payment.tenant_id),
                                "amount": float(payment.amount),
                                "transaction_id": verification.get("transaction_id"),
                            },
                            send_push=True,
                        )
                        logger.info(f"Payment notification sent to owner {owner.id}")
            except Exception as e:
                # Don't fail payment if notification fails
                logger.error(f"Failed to send payment notification: {e}")
            
            # T122: Send payment confirmation notification
            try:
                # Queue notification task asynchronously (non-blocking)
                send_payment_confirmation.delay(str(payment.id))
                logger.info(f"Payment confirmation notification queued for payment {payment.id}")
            except Exception as e:
                # Don't fail payment if notification fails
                logger.error(f"Failed to queue payment notification: {e}")
            
            response_message = {
                "status": "success",
                "message": "Payment completed successfully",
                "payment_id": str(payment.id),
                "transaction_id": verification.get("transaction_id"),
                "receipt_generated": receipt_path is not None,
                "redirect_url": f"/payments/{payment.id}/receipt"  # Frontend route
            }
            
        elif verification.get("status") == "Pending":
            payment.status = PaymentStatus.PENDING
            payment.metadata = payment.metadata or {}
            payment.metadata.update({
                "khalti_pidx": pidx,
                "khalti_status": "Pending",
                "payer_mobile": mobile,
            })
            
            logger.warning(
                f"Payment {payment.id} is PENDING. "
                f"Manual verification may be required."
            )
            
            response_message = {
                "status": "pending",
                "message": "Payment is being processed. Please contact support if not updated within 24 hours.",
                "payment_id": str(payment.id),
                "redirect_url": f"/payments/{payment.id}/status"  # Frontend route
            }
            
        elif verification.get("status") in ["User canceled", "Expired"]:
            payment.status = PaymentStatus.FAILED
            payment.metadata = payment.metadata or {}
            payment.metadata.update({
                "khalti_pidx": pidx,
                "khalti_status": verification.get("status"),
                "failure_reason": verification.get("status"),
            })
            
            logger.info(
                f"Payment {payment.id} marked as FAILED. "
                f"Reason: {verification.get('status')}"
            )
            
            response_message = {
                "status": "failed",
                "message": f"Payment {verification.get('status').lower()}",
                "payment_id": str(payment.id),
                "redirect_url": "/payments/retry"  # Frontend route
            }
            
        else:
            # Unknown status - hold and contact support
            payment.status = PaymentStatus.PENDING
            payment.metadata = payment.metadata or {}
            payment.metadata.update({
                "khalti_pidx": pidx,
                "khalti_status": verification.get("status"),
                "requires_manual_review": True,
            })
            
            logger.error(
                f"Payment {payment.id} has unknown status: {verification.get('status')}. "
                f"Manual review required."
            )
            
            response_message = {
                "status": "error",
                "message": "Payment status unclear. Our team will review and contact you.",
                "payment_id": str(payment.id),
                "redirect_url": "/support"  # Frontend route
            }
        
        # Commit changes (only for non-completed status, completed already committed above)
        if verification.get("status") != "Completed":
            await session.commit()
            await session.refresh(payment)
        
        return response_message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing Khalti callback: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process payment callback: {str(e)}"
        )


@router.get(
    "/esewa",
    status_code=status.HTTP_200_OK,
    summary="eSewa payment callback handler",
    description="""
    Handle eSewa payment gateway callback after user completes payment.
    eSewa redirects user to this URL with payment status in query parameters.
    
    This endpoint will be implemented when eSewa service is added.
    """,
)
async def esewa_callback(
    session: Annotated[AsyncSession, Depends(get_async_db)],
    oid: Optional[str] = Query(None, description="Order ID / Transaction ID"),
    amt: Optional[float] = Query(None, description="Amount"),
    refId: Optional[str] = Query(None, description="eSewa reference ID"),
) -> dict:
    """
    Process eSewa payment callback.
    
    Note: Implementation pending - requires eSewa service (T111).
    
    Args:
        oid: Order/transaction ID from eSewa
        amt: Transaction amount
        refId: eSewa reference ID
        session: Database session
        
    Returns:
        Success/failure message with redirect instructions
        
    Raises:
        HTTPException: Service not implemented yet
    """
    logger.warning("eSewa callback received but service not yet implemented")
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="eSewa payment gateway integration is not yet implemented. Please use Khalti."
    )


@router.get(
    "/imepay",
    status_code=status.HTTP_200_OK,
    summary="IME Pay callback handler",
    description="""
    Handle IME Pay payment gateway callback after user completes payment.
    IME Pay redirects user to this URL with payment status in query parameters.
    
    This endpoint will be implemented when IME Pay service is added.
    """,
)
async def imepay_callback(
    session: Annotated[AsyncSession, Depends(get_async_db)],
    TransactionId: Optional[str] = Query(None, description="IME Pay transaction ID"),
    RefId: Optional[str] = Query(None, description="Merchant reference ID"),
    Msisdn: Optional[str] = Query(None, description="Customer mobile number"),
    Amount: Optional[float] = Query(None, description="Transaction amount"),
    Status: Optional[str] = Query(None, description="Payment status"),
) -> dict:
    """
    Process IME Pay callback.
    
    Note: Implementation pending - requires IME Pay service (T112).
    
    Args:
        TransactionId: IME Pay transaction ID
        RefId: Merchant reference ID (purchase_order_id)
        Msisdn: Customer mobile number
        Amount: Transaction amount
        Status: Payment status
        session: Database session
        
    Returns:
        Success/failure message with redirect instructions
        
    Raises:
        HTTPException: Service not implemented yet
    """
    logger.warning("IME Pay callback received but service not yet implemented")
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="IME Pay payment gateway integration is not yet implemented. Please use Khalti."
    )
