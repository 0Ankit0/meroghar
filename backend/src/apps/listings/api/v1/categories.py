from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from src.apps.iam.api.deps import get_current_active_superuser, get_db
from src.apps.iam.models.user import User
from src.apps.listings.models.property_type import PropertyType, PropertyTypeFeature
from src.apps.listings.schemas.property_type import (
    PropertyTypeCreate,
    PropertyTypeDetailRead,
    PropertyTypeFeatureCreate,
    PropertyTypeFeatureRead,
    PropertyTypeRead,
    PropertyTypeUpdate,
)
from src.apps.listings.services.properties import get_property_type_or_404, list_property_type_features

router = APIRouter(prefix="/categories")


async def _build_category_detail(db: AsyncSession, property_type: PropertyType) -> PropertyTypeDetailRead:
    attributes = await list_property_type_features(db, property_type.id)
    return PropertyTypeDetailRead.model_validate({**property_type.model_dump(), "attributes": attributes})


@router.get("/", response_model=list[PropertyTypeRead])
async def list_categories(db: AsyncSession = Depends(get_db)) -> list[PropertyTypeRead]:
    result = await db.execute(
        select(PropertyType)
        .where(PropertyType.is_active == True)
        .order_by(col(PropertyType.display_order), col(PropertyType.name))
    )
    return [PropertyTypeRead.model_validate(property_type) for property_type in result.scalars().all()]


@router.get("/{category_id}", response_model=PropertyTypeDetailRead)
async def get_category(category_id: str, db: AsyncSession = Depends(get_db)) -> PropertyTypeDetailRead:
    from src.apps.iam.utils.hashid import decode_id_or_404

    property_type = await get_property_type_or_404(db, decode_id_or_404(category_id))
    if not property_type.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property category not found")
    return await _build_category_detail(db, property_type)


@router.post("/", response_model=PropertyTypeDetailRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: PropertyTypeCreate,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> PropertyTypeDetailRead:
    existing = (await db.execute(select(PropertyType).where(PropertyType.slug == data.slug))).scalars().first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category slug already exists")
    if data.parent_category_id is not None:
        await get_property_type_or_404(db, data.parent_category_id)

    property_type = PropertyType(**data.model_dump())
    db.add(property_type)
    await db.commit()
    await db.refresh(property_type)
    return await _build_category_detail(db, property_type)


@router.put("/{category_id}", response_model=PropertyTypeDetailRead)
async def update_category(
    category_id: str,
    data: PropertyTypeUpdate,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> PropertyTypeDetailRead:
    from src.apps.iam.utils.hashid import decode_id_or_404

    property_type = await get_property_type_or_404(db, decode_id_or_404(category_id))
    update_fields = data.model_dump(exclude_unset=True)
    if "slug" in update_fields and update_fields["slug"] != property_type.slug:
        existing = (
            await db.execute(select(PropertyType).where(PropertyType.slug == update_fields["slug"]))
        ).scalars().first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category slug already exists")
    if update_fields.get("parent_category_id") is not None:
        await get_property_type_or_404(db, update_fields["parent_category_id"])
    for field, value in update_fields.items():
        setattr(property_type, field, value)
    db.add(property_type)
    await db.commit()
    await db.refresh(property_type)
    return await _build_category_detail(db, property_type)


@router.post(
    "/{category_id}/attributes",
    response_model=PropertyTypeFeatureRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_category_attribute(
    category_id: str,
    data: PropertyTypeFeatureCreate,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db),
) -> PropertyTypeFeatureRead:
    from src.apps.iam.utils.hashid import decode_id_or_404

    property_type_id = decode_id_or_404(category_id)
    await get_property_type_or_404(db, property_type_id)
    existing = (
        await db.execute(
            select(PropertyTypeFeature).where(
                PropertyTypeFeature.property_type_id == property_type_id,
                PropertyTypeFeature.slug == data.slug,
            )
        )
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category attribute slug already exists")

    attribute = PropertyTypeFeature(property_type_id=property_type_id, **data.model_dump())
    db.add(attribute)
    await db.commit()
    await db.refresh(attribute)
    return PropertyTypeFeatureRead.model_validate(attribute)
