from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from rest_framework import authentication, exceptions


def build_jwt_payload(*, user_id, email, user_type, role="user", issuer):
    now = datetime.now(timezone.utc)
    return {
        "sub": str(user_id),
        "email": email,
        "user_type": user_type,
        "role": role,
        "iss": issuer,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=24)).timestamp()),
    }


def encode_token(payload):
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def decode_token(token):
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])


class ServicePrincipal:
    is_authenticated = True
    role = "service"
    user_type = "service"

    def __init__(self, name="internal-service"):
        self.id = name
        self.email = f"{name}@internal.local"


class TokenPrincipal:
    is_authenticated = True

    def __init__(self, payload):
        self.id = payload.get("sub")
        self.email = payload.get("email")
        self.role = payload.get("role")
        self.user_type = payload.get("user_type")
        self.payload = payload


class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
        except jwt.PyJWTError as exc:
            raise exceptions.AuthenticationFailed("Invalid token") from exc

        return (TokenPrincipal(payload), token)


class InternalServiceAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get("X-Internal-Service-Token")
        if not token:
            return None
        if token != settings.INTERNAL_SERVICE_TOKEN:
            raise exceptions.AuthenticationFailed("Invalid internal service token")
        service_name = request.headers.get("X-Service-Name", "customer-service")
        return (ServicePrincipal(service_name), token)
