from fastapi import HTTPException, status


def require_user_id(user_id: int | None) -> int:
    """
    Return a guaranteed integer user id for authenticated flows.

    SQLModel models expose optional primary keys at type level (`int | None`),
    but authenticated request handlers require a persisted user id.
    """
    if not isinstance(user_id, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user id is missing",
        )
    return user_id
