"""
Offline synchronization API endpoints.

Provides bulk sync, status tracking, and conflict resolution endpoints.
"""
from typing import List, Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models.user import User
from ...models.sync import SyncLog, SyncStatus, SyncOperation
from ...schemas.sync import (
    SyncRequest,
    SyncResponse,
    SyncRecordRequest,
    SyncRecordResponse,
    SyncStatusResponse,
    ConflictResponse,
)
from ...services.sync_service import SyncService
from ..dependencies import get_current_user

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("", response_model=SyncResponse, status_code=status.HTTP_200_OK)
async def bulk_sync(
    sync_request: SyncRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    x_device_id: Annotated[str, Header(..., description="Unique device identifier")],
    x_device_name: Annotated[Optional[str], Header(None, description="Human-readable device name")] = None,
):
    """
    Bulk sync endpoint for offline data synchronization.
    
    Accepts an array of sync operations (create, update, delete) and processes them
    with conflict detection using Last-Write-Wins (LWW) strategy.
    
    Headers:
        - X-Device-ID: Unique device identifier (required)
        - X-Device-Name: Human-readable device name (optional)
    
    Returns:
        - sync_log_id: ID of the sync log for tracking
        - total_records: Total records in request
        - successful: Number of successfully synced records
        - failed: Number of failed records
        - conflicts: Number of conflicted records
        - results: Detailed results for each record
    """
    if not sync_request.records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No records provided for sync"
        )
    
    # Create sync log
    sync_log = await SyncService.create_sync_log(
        session=session,
        user_id=current_user.id,
        device_id=x_device_id,
        device_name=x_device_name,
        operation=SyncOperation.BULK,
    )
    
    # Update status to in_progress
    await SyncService.update_sync_log_status(
        session=session,
        sync_log_id=sync_log.id,
        status=SyncStatus.IN_PROGRESS,
    )
    
    # Process each record
    results: List[SyncRecordResponse] = []
    records_synced = 0
    records_failed = 0
    records_conflict = 0
    conflict_details_list = []
    
    for record_request in sync_request.records:
        result = await SyncService.sync_record(
            session=session,
            user=current_user,
            model_name=record_request.model,
            operation=record_request.operation,
            record_data=record_request.data,
        )
        
        # Create response
        record_response = SyncRecordResponse(
            model=record_request.model,
            operation=record_request.operation,
            client_id=record_request.client_id,
            status=result['status'],
            message=result['message'],
            server_id=result.get('server_id'),
            conflict_details=result.get('conflict_details'),
        )
        results.append(record_response)
        
        # Update counters
        if result['status'] == 'success':
            records_synced += 1
        elif result['status'] == 'conflict':
            records_conflict += 1
            if result.get('conflict_details'):
                conflict_details_list.append(result['conflict_details'])
        else:
            records_failed += 1
    
    # Commit all changes
    try:
        await session.commit()
        
        # Determine final status
        if records_conflict > 0:
            final_status = SyncStatus.CONFLICT
        elif records_failed > 0:
            final_status = SyncStatus.FAILED
        else:
            final_status = SyncStatus.SUCCESS
        
        # Update sync log with final results
        await SyncService.update_sync_log_status(
            session=session,
            sync_log_id=sync_log.id,
            status=final_status,
            records_synced=records_synced,
            records_failed=records_failed,
            records_conflict=records_conflict,
            conflict_details={'conflicts': conflict_details_list} if conflict_details_list else None,
        )
        
        return SyncResponse(
            sync_log_id=sync_log.id,
            total_records=len(sync_request.records),
            successful=records_synced,
            failed=records_failed,
            conflicts=records_conflict,
            results=results,
        )
    
    except Exception as e:
        await session.rollback()
        
        # Update sync log as failed
        await SyncService.update_sync_log_status(
            session=session,
            sync_log_id=sync_log.id,
            status=SyncStatus.FAILED,
            error_message=str(e),
            records_failed=len(sync_request.records),
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/status", response_model=SyncStatusResponse, status_code=status.HTTP_200_OK)
async def get_sync_status(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    x_device_id: Annotated[Optional[str], Header(None, description="Filter by device ID")] = None,
):
    """
    Get sync status summary for the current user.
    
    Provides statistics about sync operations including:
    - Total syncs, pending, in_progress, success, failed, conflicts
    - Record counts (synced, failed, conflict)
    - Latest sync information
    
    Headers:
        - X-Device-ID: Filter by specific device (optional)
    """
    status_data = await SyncService.get_sync_status(
        session=session,
        user_id=current_user.id,
        device_id=x_device_id,
    )
    
    return SyncStatusResponse(**status_data)


@router.get("/conflicts", response_model=List[ConflictResponse], status_code=status.HTTP_200_OK)
async def get_conflicts(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    x_device_id: Annotated[Optional[str], Header(None, description="Filter by device ID")] = None,
):
    """
    Get unresolved sync conflicts for the current user.
    
    Returns sync logs with conflict status, including:
    - Conflict details (model, record_id, client_data, server_data)
    - Timestamps and device information
    - Conflict resolution recommendations
    
    Headers:
        - X-Device-ID: Filter by specific device (optional)
    """
    conflicts = await SyncService.get_conflicts(
        session=session,
        user_id=current_user.id,
        device_id=x_device_id,
    )
    
    return [
        ConflictResponse(
            sync_log_id=conflict.id,
            device_id=conflict.device_id,
            device_name=conflict.device_name,
            started_at=conflict.started_at,
            conflict_details=conflict.conflict_details,
            records_conflict=conflict.records_conflict,
        )
        for conflict in conflicts
    ]
