from fastapi import Header, HTTPException

ADMIN_API_KEY = "kjtheog123"


def verify_admin(
    x_admin_key: str | None = Header(default=None),
):
    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    return True