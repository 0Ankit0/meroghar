from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.iam.api.deps import get_db
from src.apps.search.schemas.asset import AssetSearchResponse
from src.apps.search.services.assets import search_assets

router = APIRouter(prefix="/assets")


@router.get("/", response_model=AssetSearchResponse)
async def search_public_assets(
    category: str | None = Query(default=None),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    location: str | None = Query(default=None),
    radius_km: float | None = Query(default=None, ge=0),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> AssetSearchResponse:
    if (start is None) != (end is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start and end must either both be provided or both be omitted",
        )
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_price cannot be greater than max_price",
        )
    result = await search_assets(
        db,
        category=category,
        start_at=start,
        end_at=end,
        location=location,
        radius_km=radius_km,
        min_price=min_price,
        max_price=max_price,
        page=page,
        per_page=per_page,
    )
    return AssetSearchResponse.model_validate(result)
