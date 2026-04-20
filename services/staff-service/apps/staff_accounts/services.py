from shared.common.auth import build_jwt_payload, encode_token


def issue_staff_token(user, issuer):
    payload = build_jwt_payload(
        user_id=user.id,
        email=user.email,
        user_type="staff",
        role=user.role,
        issuer=issuer,
    )
    token = encode_token(payload)
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 86400,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        },
    }
