from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from src.apps.core.storage import delete_media, save_media_bytes
from src.apps.iam.api.deps import get_current_user, get_current_user_optional, get_db
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404
from src.apps.listings.models.property import Property, PropertyPhoto, PropertyStatus
from src.apps.listings.schemas.property import (
    PropertyDetailRead,
    PropertyListRead,
    PropertyManageRead,
    PropertyPhotoRead,
    PropertyUpdate,
)
from src.apps.listings.services.properties import (
    build_property_payload,
    delete_property_feature_values,
    ensure_property_publishable,
    get_property_or_404,
    get_property_type_or_404,
    list_property_photos,
    require_property_owner,
    set_fallback_cover_photo,
    sync_property_availability_blocks,
    sync_property_feature_values,
    touch_property,
    unset_cover_photo,
)

router = APIRouter(prefix="/properties")
_ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.get("/mine", response_model=PropertyListRead)
async def list_my_properties(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyListRead:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")

    result = await db.execute(
        select(Property)
        .where(Property.owner_user_id == current_user.id)
        .order_by(col(Property.updated_at).desc(), col(Property.id).desc())
    )
    properties = list(result.scalars().all())
    total = len(properties)
    start_index = (page - 1) * per_page
    items = [
        PropertyManageRead.model_validate(await build_property_payload(db, property_obj))
        for property_obj in properties[start_index : start_index + per_page]
    ]
    return PropertyListRead(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        has_more=start_index + len(items) < total,
    )


@router.get("/{property_id}", response_model=PropertyDetailRead)
async def get_property_detail(
    property_id: str,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> PropertyDetailRead:
    property_obj = await get_property_or_404(db, decode_id_or_404(property_id))
    if not property_obj.is_published or property_obj.status != PropertyStatus.PUBLISHED:
        if current_user is None or current_user.id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        if property_obj.owner_user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return PropertyDetailRead.model_validate(await build_property_payload(db, property_obj))


@router.put("/{property_id}", response_model=PropertyManageRead)
async def update_property(
    property_id: str,
    data: PropertyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyManageRead:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")

    property_obj = await require_property_owner(db, decode_id_or_404(property_id), current_user.id)
    update_fields = data.model_dump(exclude_unset=True)

    property_type_changed = False
    if "property_type_id" in update_fields:
        await get_property_type_or_404(db, update_fields["property_type_id"])
        property_type_changed = update_fields["property_type_id"] != property_obj.property_type_id

    feature_values = update_fields.pop("feature_values", None)
    availability_blocks = update_fields.pop("availability_blocks", None)
    for field, value in update_fields.items():
        setattr(property_obj, field, value)

    if property_type_changed:
        await delete_property_feature_values(db, property_obj.id)
    if feature_values is not None:
        await delete_property_feature_values(db, property_obj.id)
        await sync_property_feature_values(db, property_obj, feature_values)
    if availability_blocks is not None:
        await sync_property_availability_blocks(db, property_obj, availability_blocks)

    await touch_property(property_obj)
    db.add(property_obj)
    await db.commit()
    await db.refresh(property_obj)
    return PropertyManageRead.model_validate(await build_property_payload(db, property_obj))


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_property(
    property_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")

    property_obj = await require_property_owner(db, decode_id_or_404(property_id), current_user.id)
    property_obj.status = PropertyStatus.ARCHIVED
    property_obj.is_published = False
    await touch_property(property_obj)
    db.add(property_obj)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{property_id}/publish", response_model=PropertyManageRead)
async def publish_property(
    property_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyManageRead:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")

    property_obj = await require_property_owner(db, decode_id_or_404(property_id), current_user.id)
    if property_obj.status == PropertyStatus.ARCHIVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archived properties cannot be published")
    await ensure_property_publishable(db, property_obj)
    property_obj.status = PropertyStatus.PUBLISHED
    property_obj.is_published = True
    await touch_property(property_obj)
    db.add(property_obj)
    await db.commit()
    await db.refresh(property_obj)
    return PropertyManageRead.model_validate(await build_property_payload(db, property_obj))


@router.post("/{property_id}/unpublish", response_model=PropertyManageRead)
async def unpublish_property(
    property_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyManageRead:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")

    property_obj = await require_property_owner(db, decode_id_or_404(property_id), current_user.id)
    if property_obj.status == PropertyStatus.ARCHIVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archived properties cannot be unpublished")
    property_obj.status = PropertyStatus.DRAFT
    property_obj.is_published = False
    await touch_property(property_obj)
    db.add(property_obj)
    await db.commit()
    await db.refresh(property_obj)
    return PropertyManageRead.model_validate(await build_property_payload(db, property_obj))


@router.post("/{property_id}/photos", response_model=PropertyPhotoRead, status_code=status.HTTP_201_CREATED)
async def upload_property_photo(
    property_id: str,
    file: UploadFile = File(...),
    caption: str = Form(default=""),
    position: int = Form(default=0),
    is_cover: bool = Form(default=False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PropertyPhotoRead:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")
    if file.content_type not in _ALLOWED_PHOTO_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported photo content type")

    property_obj = await require_property_owner(db, decode_id_or_404(property_id), current_user.id)
    contents = await file.read()
    extension = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "jpg"
    url = save_media_bytes(
        f"property-photos/{property_obj.id}/{uuid.uuid4().hex}.{extension}",
        contents,
        content_type=file.content_type,
    )

    existing_photos = await list_property_photos(db, property_obj.id)
    cover_photo = is_cover or not existing_photos
    if cover_photo:
        await unset_cover_photo(db, property_obj.id)

    photo = PropertyPhoto(
        property_id=property_obj.id,
        url=url,
        thumbnail_url=url,
        position=position,
        is_cover=cover_photo,
        caption=caption,
    )
    db.add(photo)
    await touch_property(property_obj)
    db.add(property_obj)
    await db.commit()
    await db.refresh(photo)
    return PropertyPhotoRead.model_validate(photo)


@router.delete("/{property_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property_photo(
    property_id: str,
    photo_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    if current_user.id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user is invalid")

    property_db_id = decode_id_or_404(property_id)
    property_obj = await require_property_owner(db, property_db_id, current_user.id)
    photo = (
        await db.execute(
            select(PropertyPhoto).where(
                PropertyPhoto.id == decode_id_or_404(photo_id),
                PropertyPhoto.property_id == property_db_id,
            )
        )
    ).scalars().first()
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property photo not found")

    deleted_cover = photo.is_cover
    delete_media(photo.url)
    await db.delete(photo)
    await touch_property(property_obj)
    db.add(property_obj)
    await db.commit()
    if deleted_cover:
        await set_fallback_cover_photo(db, property_db_id)
        await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
