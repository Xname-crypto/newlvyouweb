"""
API Authentication Middleware for lvyou_backend
Verifies Supabase JWT tokens and extracts user information
"""

import os
from functools import wraps
from typing import Callable, Optional

import jwt
import requests
from supabase import create_client
from rest_framework import status
from rest_framework.response import Response

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")


def _get_supabase_admin_client():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception:
        return None


def _get_profile_role(user_id: str) -> str:
    if not user_id:
        return ""

    supabase = _get_supabase_admin_client()
    if not supabase:
        return ""

    try:
        response = supabase.from_("profiles").select("role").eq("id", user_id).limit(1).execute()
        rows = getattr(response, "data", None) or []
        if not rows:
            return ""
        return str(rows[0].get("role") or "").strip()
    except Exception:
        return ""


def _get_profile_role_via_user_token(token: str, user_id: str) -> str:
    if not token or not user_id or not SUPABASE_URL:
        return ""

    auth_token = token[7:] if token.startswith("Bearer ") else token
    api_key = SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY
    if not api_key:
        return ""

    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/profiles",
            params={"select": "role", "id": f"eq.{user_id}", "limit": 1},
            headers={
                "apikey": api_key,
                "Authorization": f"Bearer {auth_token}",
            },
            timeout=5,
        )
        if not response.ok:
            return ""

        rows = response.json() or []
        if not rows:
            return ""
        return str(rows[0].get("role") or "").strip()
    except Exception:
        return ""


def _get_user_via_supabase_auth(token: str) -> Optional[dict]:
    if not token or not SUPABASE_URL:
        return None

    auth_token = token[7:] if token.startswith("Bearer ") else token
    api_key = SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY
    if not api_key:
        return None

    try:
        response = requests.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "apikey": api_key,
                "Authorization": f"Bearer {auth_token}",
            },
            timeout=5,
        )
        if not response.ok:
            return None

        payload = response.json() or {}
        if payload.get("id") and not payload.get("sub"):
            payload["sub"] = payload["id"]
        return payload
    except Exception:
        return None


def get_user_from_token(token: str) -> Optional[dict]:
    """
    Verify and decode a Supabase JWT token.
    Returns user data if valid, None if invalid.
    """
    if not token:
        return None

    try:
        supabase_user = _get_user_via_supabase_auth(token)
        if supabase_user:
            return supabase_user

        if not SUPABASE_JWT_SECRET:
            return None

        auth_token = token[7:] if token.startswith("Bearer ") else token

        options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_iat": True,
            "verify_aud": False,
        }

        return jwt.decode(
            auth_token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options=options,
        )

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


def get_user_id_from_request(request) -> Optional[str]:
    """
    Extract user ID from the Authorization header in the request.
    Returns user_id if authenticated, None otherwise.
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header:
        return None

    user_data = get_user_from_token(auth_header)
    if user_data:
        # Supabase stores user ID in 'sub' claim
        return user_data.get("sub")

    return None


def is_admin_from_token(token: str) -> bool:
    """
    Check if the user has admin role based on their JWT claims.
    """
    if not token:
        return False

    user_data = get_user_from_token(token)
    if not user_data:
        return False

    # Check for admin role in Supabase metadata or custom claims
    role = user_data.get("role", "")
    if role == "admin" or role == "moderator":
        return True

    # Check in app_metadata
    app_meta = user_data.get("app_metadata", {})
    if app_meta.get("role") in ["admin", "moderator"]:
        return True

    user_id = str(user_data.get("sub") or "")

    profile_role = _get_profile_role(user_id)
    if profile_role in ["admin", "moderator"]:
        return True

    profile_role = _get_profile_role_via_user_token(token, user_id)
    if profile_role in ["admin", "moderator"]:
        return True

    return False


def require_auth(view_func: Callable) -> Callable:
    """
    Decorator that requires a valid authentication token.
    Returns 401 if not authenticated.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_id = get_user_id_from_request(request)

        if not user_id:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Attach user_id to request for later use
        request.user_id = user_id
        return view_func(request, *args, **kwargs)

    return wrapper


def require_admin(view_func: Callable) -> Callable:
    """
    Decorator that requires admin or moderator role.
    Returns 401 if not authenticated, 403 if not authorized.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not is_admin_from_token(auth_header):
            return Response(
                {"error": "Admin or moderator access required"},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = get_user_id_from_request(request)
        request.user_id = user_id
        return view_func(request, *args, **kwargs)

    return wrapper


class OptionalAuthMiddleware:
    """
    Middleware that optionally authenticates the user but doesn't require it.
    Sets request.user_id if valid token is provided, otherwise None.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user_id = get_user_id_from_request(request)
        return self.get_response(request)
