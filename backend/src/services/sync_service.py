"""
Offline synchronization service with conflict resolution.

Implements Last-Write-Wins (LWW) conflict resolution strategy based on updated_at timestamps.
Handles bulk sync operations, retry logic, and conflict detection.
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.bill import Bill
from ..models.expense import Expense
from ..models.payment import Payment
from ..models.property import Property
from ..models.sync import SyncLog, SyncOperation, SyncStatus
from ..models.tenant import Tenant
from ..models.user import User


class ConflictResolutionError(Exception):
    """Raised when a conflict cannot be automatically resolved."""

    pass


class SyncService:
    """Service for handling offline synchronization and conflict resolution."""

    # Model mapping for dynamic lookup
    MODEL_MAP = {
        "property": Property,
        "tenant": Tenant,
        "payment": Payment,
        "bill": Bill,
        "expense": Expense,
    }

    # Exponential backoff parameters
    BASE_RETRY_DELAY = timedelta(minutes=5)
    MAX_RETRY_DELAY = timedelta(hours=24)
    MAX_RETRIES = 10

    @staticmethod
    async def create_sync_log(
        session: AsyncSession,
        user_id: int,
        device_id: str,
        device_name: str | None,
        operation: SyncOperation,
    ) -> SyncLog:
        """Create a new sync log entry."""
        sync_log = SyncLog(
            user_id=user_id,
            device_id=device_id,
            device_name=device_name,
            operation=operation,
            status=SyncStatus.PENDING,
        )
        session.add(sync_log)
        await session.commit()
        await session.refresh(sync_log)
        return sync_log

    @staticmethod
    async def update_sync_log_status(
        session: AsyncSession,
        sync_log_id: int,
        status: SyncStatus,
        error_message: str | None = None,
        conflict_details: dict[str, Any] | None = None,
        records_synced: int = 0,
        records_failed: int = 0,
        records_conflict: int = 0,
    ) -> SyncLog:
        """Update sync log status and statistics."""
        result = await session.execute(select(SyncLog).where(SyncLog.id == sync_log_id))
        sync_log = result.scalar_one()

        sync_log.status = status
        sync_log.records_synced += records_synced
        sync_log.records_failed += records_failed
        sync_log.records_conflict += records_conflict

        if error_message:
            sync_log.error_message = error_message

        if conflict_details:
            sync_log.conflict_details = conflict_details

        if status in (SyncStatus.SUCCESS, SyncStatus.FAILED, SyncStatus.CONFLICT):
            sync_log.completed_at = datetime.utcnow()

        await session.commit()
        await session.refresh(sync_log)
        return sync_log

    @staticmethod
    async def schedule_retry(
        session: AsyncSession,
        sync_log_id: int,
    ) -> SyncLog:
        """Schedule a retry for a failed sync operation using exponential backoff."""
        result = await session.execute(select(SyncLog).where(SyncLog.id == sync_log_id))
        sync_log = result.scalar_one()

        # Check if we've exceeded max retries
        if sync_log.retry_count >= SyncService.MAX_RETRIES:
            sync_log.status = SyncStatus.FAILED
            sync_log.error_message = f"Max retries ({SyncService.MAX_RETRIES}) exceeded"
            sync_log.completed_at = datetime.utcnow()
        else:
            # Calculate next retry time using exponential backoff
            delay_minutes = min(
                SyncService.BASE_RETRY_DELAY.total_seconds() * (2**sync_log.retry_count),
                SyncService.MAX_RETRY_DELAY.total_seconds(),
            )
            sync_log.next_retry_at = datetime.utcnow() + timedelta(seconds=delay_minutes)
            sync_log.retry_count += 1
            sync_log.status = SyncStatus.PENDING

        await session.commit()
        await session.refresh(sync_log)
        return sync_log

    @staticmethod
    def resolve_conflict_lww(
        server_record: Any,
        client_record: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """
        Resolve conflict using Last-Write-Wins (LWW) strategy.

        Args:
            server_record: Server-side database record
            client_record: Client-side record data with 'updated_at' field

        Returns:
            Tuple of (should_update, reason)
            - should_update: True if client record should overwrite server
            - reason: Explanation of the decision
        """
        if not hasattr(server_record, "updated_at"):
            raise ConflictResolutionError(
                f"Server record {type(server_record).__name__} missing updated_at field"
            )

        if "updated_at" not in client_record:
            raise ConflictResolutionError(
                "Client record missing updated_at field for conflict resolution"
            )

        server_updated_at = server_record.updated_at

        # Parse client updated_at (could be string or datetime)
        client_updated_at = client_record["updated_at"]
        if isinstance(client_updated_at, str):
            client_updated_at = datetime.fromisoformat(client_updated_at.replace("Z", "+00:00"))

        # LWW: Client wins if its timestamp is newer
        if client_updated_at > server_updated_at:
            return (
                True,
                f"Client record is newer (client: {client_updated_at}, server: {server_updated_at})",
            )
        elif client_updated_at < server_updated_at:
            return (
                False,
                f"Server record is newer (server: {server_updated_at}, client: {client_updated_at})",
            )
        else:
            # Timestamps are equal - prefer server to avoid unnecessary updates
            return False, f"Timestamps are equal, keeping server record (both: {server_updated_at})"

    @staticmethod
    async def sync_record(
        session: AsyncSession,
        user: User,
        model_name: str,
        operation: str,
        record_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Sync a single record with conflict detection.

        Args:
            session: Database session
            user: User performing the sync
            model_name: Name of the model (e.g., 'property', 'tenant')
            operation: 'create', 'update', or 'delete'
            record_data: Record data from client

        Returns:
            Dict with keys: status ('success', 'failed', 'conflict'), message, conflict_details (if any)
        """
        # Validate model name
        if model_name not in SyncService.MODEL_MAP:
            return {
                "status": "failed",
                "message": f"Unknown model: {model_name}",
            }

        model_class = SyncService.MODEL_MAP[model_name]
        record_id = record_data.get("id")

        try:
            if operation == "create":
                # Create new record
                new_record = model_class(**record_data)
                session.add(new_record)
                await session.flush()
                return {
                    "status": "success",
                    "message": f"Created {model_name} with ID {new_record.id}",
                    "server_id": new_record.id,
                }

            elif operation == "update":
                # Find existing record
                if not record_id:
                    return {
                        "status": "failed",
                        "message": "Update operation requires 'id' field",
                    }

                result = await session.execute(
                    select(model_class).where(model_class.id == record_id)
                )
                server_record = result.scalar_one_or_none()

                if not server_record:
                    return {
                        "status": "failed",
                        "message": f"{model_name} with ID {record_id} not found",
                    }

                # Check for conflicts using LWW
                should_update, reason = SyncService.resolve_conflict_lww(server_record, record_data)

                if should_update:
                    # Update server record with client data
                    for key, value in record_data.items():
                        if key != "id" and hasattr(server_record, key):
                            setattr(server_record, key, value)

                    await session.flush()
                    return {
                        "status": "success",
                        "message": f"Updated {model_name} ID {record_id}. {reason}",
                    }
                else:
                    # Conflict detected - server record is newer
                    return {
                        "status": "conflict",
                        "message": f"Conflict detected for {model_name} ID {record_id}. {reason}",
                        "conflict_details": {
                            "model": model_name,
                            "record_id": record_id,
                            "client_data": record_data,
                            "server_data": {
                                "id": server_record.id,
                                "updated_at": (
                                    server_record.updated_at.isoformat()
                                    if hasattr(server_record, "updated_at")
                                    else None
                                ),
                            },
                            "reason": reason,
                        },
                    }

            elif operation == "delete":
                # Delete record
                if not record_id:
                    return {
                        "status": "failed",
                        "message": "Delete operation requires 'id' field",
                    }

                result = await session.execute(
                    select(model_class).where(model_class.id == record_id)
                )
                server_record = result.scalar_one_or_none()

                if not server_record:
                    # Already deleted - consider success
                    return {
                        "status": "success",
                        "message": f"{model_name} with ID {record_id} already deleted",
                    }

                await session.delete(server_record)
                await session.flush()
                return {
                    "status": "success",
                    "message": f"Deleted {model_name} with ID {record_id}",
                }

            else:
                return {
                    "status": "failed",
                    "message": f"Unknown operation: {operation}",
                }

        except Exception as e:
            return {
                "status": "failed",
                "message": f"Error syncing {model_name}: {str(e)}",
            }

    @staticmethod
    async def get_pending_retries(
        session: AsyncSession,
        user_id: int | None = None,
    ) -> list[SyncLog]:
        """Get sync logs that are ready for retry."""
        query = select(SyncLog).where(
            and_(
                SyncLog.status == SyncStatus.PENDING,
                SyncLog.next_retry_at <= datetime.utcnow(),
                SyncLog.retry_count < SyncService.MAX_RETRIES,
            )
        )

        if user_id:
            query = query.where(SyncLog.user_id == user_id)

        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_conflicts(
        session: AsyncSession,
        user_id: int,
        device_id: str | None = None,
    ) -> list[SyncLog]:
        """Get sync logs with unresolved conflicts."""
        query = (
            select(SyncLog)
            .where(
                and_(
                    SyncLog.user_id == user_id,
                    SyncLog.status == SyncStatus.CONFLICT,
                )
            )
            .order_by(SyncLog.started_at.desc())
        )

        if device_id:
            query = query.where(SyncLog.device_id == device_id)

        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_sync_status(
        session: AsyncSession,
        user_id: int,
        device_id: str | None = None,
    ) -> dict[str, Any]:
        """Get sync status summary for a user/device."""
        query = select(SyncLog).where(SyncLog.user_id == user_id)

        if device_id:
            query = query.where(SyncLog.device_id == device_id)

        result = await session.execute(query)
        sync_logs = result.scalars().all()

        # Calculate statistics
        total = len(sync_logs)
        pending = sum(1 for log in sync_logs if log.status == SyncStatus.PENDING)
        in_progress = sum(1 for log in sync_logs if log.status == SyncStatus.IN_PROGRESS)
        success = sum(1 for log in sync_logs if log.status == SyncStatus.SUCCESS)
        failed = sum(1 for log in sync_logs if log.status == SyncStatus.FAILED)
        conflict = sum(1 for log in sync_logs if log.status == SyncStatus.CONFLICT)

        records_synced = sum(log.records_synced for log in sync_logs)
        records_failed = sum(log.records_failed for log in sync_logs)
        records_conflict = sum(log.records_conflict for log in sync_logs)

        # Get latest sync
        latest_sync = max(
            (log for log in sync_logs if log.started_at),
            key=lambda log: log.started_at,
            default=None,
        )

        return {
            "user_id": user_id,
            "device_id": device_id,
            "total_syncs": total,
            "pending": pending,
            "in_progress": in_progress,
            "success": success,
            "failed": failed,
            "conflict": conflict,
            "records_synced": records_synced,
            "records_failed": records_failed,
            "records_conflict": records_conflict,
            "latest_sync_at": latest_sync.started_at.isoformat() if latest_sync else None,
            "latest_sync_status": latest_sync.status.value if latest_sync else None,
        }
