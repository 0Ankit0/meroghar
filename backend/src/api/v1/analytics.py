"""Analytics API endpoints for financial data and insights.

Implements T096-T101, T109 from tasks.md.
"""
import logging
from datetime import date
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.security import get_current_user
from ...models.user import User, UserRole
from ...services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/rent-trends")
async def get_rent_collection_trends(
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    property_id: Optional[UUID] = Query(None, description="Filter by property ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Get rent collection trends over time.
    
    Returns monthly aggregated rent collection data including:
    - Total collected per month
    - Payment count
    - Completed vs pending amounts
    
    Accessible by: OWNER, INTERMEDIARY
    """
    # Check authorization
    if current_user.role not in [UserRole.OWNER, UserRole.INTERMEDIARY]:
        raise HTTPException(
            status_code=403,
            detail="Only owners and intermediaries can view analytics"
        )
    
    try:
        service = AnalyticsService(session)
        trends = await service.get_rent_collection_trends(
            user_id=current_user.id,
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        logger.info(
            f"User {current_user.id} retrieved rent collection trends "
            f"(property={property_id}, period={start_date} to {end_date})"
        )
        return trends
        
    except Exception as e:
        logger.error(f"Error retrieving rent collection trends: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve rent collection trends"
        )


@router.get("/payment-status")
async def get_payment_status_overview(
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    property_id: Optional[UUID] = Query(None, description="Filter by property ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get payment status overview (completed, pending, failed).
    
    Returns breakdown of payment statuses with counts and amounts.
    
    Accessible by: OWNER, INTERMEDIARY
    """
    # Check authorization
    if current_user.role not in [UserRole.OWNER, UserRole.INTERMEDIARY]:
        raise HTTPException(
            status_code=403,
            detail="Only owners and intermediaries can view analytics"
        )
    
    try:
        service = AnalyticsService(session)
        overview = await service.get_payment_status_overview(
            user_id=current_user.id,
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        logger.info(
            f"User {current_user.id} retrieved payment status overview "
            f"(property={property_id}, period={start_date} to {end_date})"
        )
        return overview
        
    except Exception as e:
        logger.error(f"Error retrieving payment status overview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve payment status overview"
        )


@router.get("/expense-breakdown")
async def get_expense_breakdown(
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    property_id: Optional[UUID] = Query(None, description="Filter by property ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Get expense breakdown by bill type.
    
    Returns aggregated expense data grouped by bill type including:
    - Total amount per type
    - Bill count
    - Average amount
    - Percentage of total
    
    Accessible by: OWNER, INTERMEDIARY
    """
    # Check authorization
    if current_user.role not in [UserRole.OWNER, UserRole.INTERMEDIARY]:
        raise HTTPException(
            status_code=403,
            detail="Only owners and intermediaries can view analytics"
        )
    
    try:
        service = AnalyticsService(session)
        breakdown = await service.get_expense_breakdown(
            user_id=current_user.id,
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        logger.info(
            f"User {current_user.id} retrieved expense breakdown "
            f"(property={property_id}, period={start_date} to {end_date})"
        )
        return breakdown
        
    except Exception as e:
        logger.error(f"Error retrieving expense breakdown: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve expense breakdown"
        )


@router.get("/revenue-expenses")
async def get_revenue_vs_expenses(
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    property_id: Optional[UUID] = Query(None, description="Filter by property ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get revenue vs expenses comparison.
    
    Returns:
    - Total revenue (completed rent payments)
    - Total expenses (bills)
    - Net profit
    - Profit margin percentage
    
    Accessible by: OWNER, INTERMEDIARY
    """
    # Check authorization
    if current_user.role not in [UserRole.OWNER, UserRole.INTERMEDIARY]:
        raise HTTPException(
            status_code=403,
            detail="Only owners and intermediaries can view analytics"
        )
    
    try:
        service = AnalyticsService(session)
        comparison = await service.get_revenue_vs_expenses(
            user_id=current_user.id,
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        logger.info(
            f"User {current_user.id} retrieved revenue vs expenses "
            f"(property={property_id}, period={start_date} to {end_date})"
        )
        return comparison
        
    except Exception as e:
        logger.error(f"Error retrieving revenue vs expenses: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve revenue vs expenses"
        )


@router.get("/property-performance")
async def get_property_performance(
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Get performance comparison across all properties.
    
    Returns per-property data including:
    - Tenant count
    - Total revenue
    - Total expenses
    - Net profit
    - Occupancy rate
    
    Accessible by: OWNER, INTERMEDIARY
    """
    # Check authorization
    if current_user.role not in [UserRole.OWNER, UserRole.INTERMEDIARY]:
        raise HTTPException(
            status_code=403,
            detail="Only owners and intermediaries can view analytics"
        )
    
    try:
        service = AnalyticsService(session)
        performance = await service.get_property_performance(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
        )
        
        logger.info(
            f"User {current_user.id} retrieved property performance "
            f"(period={start_date} to {end_date})"
        )
        return performance
        
    except Exception as e:
        logger.error(f"Error retrieving property performance: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve property performance"
        )


@router.post("/export")
async def export_analytics_data(
    report_type: str = Query(..., description="Type of report: rent-trends, payment-status, expense-breakdown, revenue-expenses, property-performance"),
    format: str = Query("excel", description="Export format: excel or pdf"),
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    property_id: Optional[UUID] = Query(None, description="Filter by property ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Export analytics data to Excel or PDF.
    
    Generates a downloadable file with the requested analytics data.
    
    Accessible by: OWNER, INTERMEDIARY
    """
    # Check authorization
    if current_user.role not in [UserRole.OWNER, UserRole.INTERMEDIARY]:
        raise HTTPException(
            status_code=403,
            detail="Only owners and intermediaries can export analytics"
        )
    
    # Validate report type
    valid_report_types = [
        "rent-trends",
        "payment-status",
        "expense-breakdown",
        "revenue-expenses",
        "property-performance"
    ]
    if report_type not in valid_report_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report type. Must be one of: {', '.join(valid_report_types)}"
        )
    
    # Validate format
    if format not in ["excel", "pdf"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Must be 'excel' or 'pdf'"
        )
    
    try:
        service = AnalyticsService(session)
        
        # Get the appropriate data based on report type
        data = None
        if report_type == "rent-trends":
            data = await service.get_rent_collection_trends(
                user_id=current_user.id,
                property_id=property_id,
                start_date=start_date,
                end_date=end_date,
            )
        elif report_type == "payment-status":
            data = await service.get_payment_status_overview(
                user_id=current_user.id,
                property_id=property_id,
                start_date=start_date,
                end_date=end_date,
            )
        elif report_type == "expense-breakdown":
            data = await service.get_expense_breakdown(
                user_id=current_user.id,
                property_id=property_id,
                start_date=start_date,
                end_date=end_date,
            )
        elif report_type == "revenue-expenses":
            data = await service.get_revenue_vs_expenses(
                user_id=current_user.id,
                property_id=property_id,
                start_date=start_date,
                end_date=end_date,
            )
        elif report_type == "property-performance":
            data = await service.get_property_performance(
                user_id=current_user.id,
                start_date=start_date,
                end_date=end_date,
            )
        
        # TODO: Implement actual file generation with openpyxl/reportlab
        # For now, return the data with export metadata
        logger.info(
            f"User {current_user.id} exported {report_type} analytics "
            f"(format={format}, property={property_id}, period={start_date} to {end_date})"
        )
        
        return {
            "success": True,
            "report_type": report_type,
            "format": format,
            "data": data,
            "message": "Export functionality will be implemented with openpyxl/reportlab",
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting analytics data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to export analytics data"
        )
