from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from typing import Any, Iterable

import requests
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .auth_middleware import get_user_id_from_request
from .discovery_repository import SpotRecord, get_spot_repository, list_available_cities
from .models import TravelBookingIntent, TravelDiscoverySignal, TravelItineraryItem
from .scenic_algorithms import classification_payload, optimize_route, semantic_recommendations
from .serializers import TravelBookingIntentSerializer, TravelItineraryItemSerializer


SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

DEFAULT_RECOMMENDATION_REASON = "高评分且价格适中"


def _auth_token_from_request(request) -> str:
    return str(request.headers.get("Authorization") or "").strip()


def _safe_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_tags(values: Iterable[str]) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        tags.append(text)
    return tags


def _query_tags(request) -> list[str]:
    return _normalize_tags(
        [
            *request.query_params.getlist("tag"),
            *request.query_params.getlist("tags"),
            *str(request.query_params.get("tag") or "").replace("，", ",").split(","),
        ]
    )


def _get_profile_payload(request, user_id: str) -> dict[str, Any]:
    token = _auth_token_from_request(request)
    if not SUPABASE_URL or not token or not user_id:
        return {}

    auth_token = token[7:] if token.startswith("Bearer ") else token
    api_key = SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY
    if not api_key:
        return {}

    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/profiles",
            params={"select": "*", "id": f"eq.{user_id}", "limit": 1},
            headers={
                "apikey": api_key,
                "Authorization": f"Bearer {auth_token}",
            },
            timeout=5,
        )
        if not response.ok:
            return {}
        rows = response.json() or []
        return rows[0] if rows else {}
    except Exception:
        return {}


def _extract_interest_tokens(profile: dict[str, Any]) -> list[str]:
    bio = str(profile.get("bio") or "").strip()
    if not bio:
        return []

    match = re.search(r"兴趣[:：]\s*(.+)", bio)
    raw = match.group(1) if match else bio
    parts = re.split(r"[，,、/\s|]+", raw)
    return [part.strip() for part in parts if part.strip()][:8]


def _serialize_spot(
    spot: SpotRecord,
    *,
    in_itinerary: bool = False,
    recommendation_reason: str = "",
) -> dict[str, Any]:
    return {
        "id": spot.spot_key,
        "spot_key": spot.spot_key,
        "source_type": spot.source_type,
        "source_id": spot.source_id,
        "name": spot.name,
        "city": spot.city,
        "rating": round(float(spot.rating or 0), 1),
        "price": round(float(spot.price or 0), 2),
        "description": spot.description,
        "cover_image": spot.cover_image,
        "tags": list(spot.tags or []),
        "opening_hours": spot.opening_hours,
        "visit_duration": spot.visit_duration,
        "booking_required": spot.booking_required,
        "address": spot.address,
        "recommendation_reason": recommendation_reason,
        "in_itinerary": in_itinerary,
    }


def _itinerary_lookup(user_id: str | None) -> dict[str, TravelItineraryItem]:
    if not user_id:
        return {}
    return {
        item.spot_key: item
        for item in TravelItineraryItem.objects.filter(user_id=user_id)
    }


def _spot_snapshot(spot: SpotRecord, recommendation_reason: str = "") -> dict[str, Any]:
    return {
        "spot_key": spot.spot_key,
        "name": spot.name,
        "city": spot.city,
        "rating": round(float(spot.rating or 0), 1),
        "price": round(float(spot.price or 0), 2),
        "description": spot.description,
        "cover_image": spot.cover_image,
        "tags": list(spot.tags or []),
        "opening_hours": spot.opening_hours,
        "visit_duration": spot.visit_duration,
        "booking_required": spot.booking_required,
        "address": spot.address,
        "recommendation_reason": recommendation_reason,
        "source_type": spot.source_type,
        "source_id": spot.source_id,
    }


def _summary_from_items(items: list[TravelItineraryItem]) -> dict[str, Any]:
    city_groups: dict[str, dict[str, Any]] = {}
    total_budget = 0.0

    for item in items:
        total_budget += float(item.price or 0)
        city_name = str(item.city or "未标注城市")
        group = city_groups.setdefault(
            city_name,
            {
                "city": city_name,
                "count": 0,
                "budget_total": 0.0,
            },
        )
        group["count"] += 1
        group["budget_total"] += float(item.price or 0)

    return {
        "items_count": len(items),
        "budget_total": round(total_budget, 2),
        "city_groups": [
            {
                "city": group["city"],
                "count": group["count"],
                "budget_total": round(group["budget_total"], 2),
            }
            for group in sorted(city_groups.values(), key=lambda value: (-value["count"], value["city"]))
        ],
    }


def _log_signal(user_id: str | None, spot_key: str, signal_type: str, payload: dict[str, Any] | None = None) -> None:
    if not user_id or not spot_key:
        return
    TravelDiscoverySignal.objects.create(
        user_id=user_id,
        spot_key=spot_key,
        signal_type=signal_type,
        payload=payload or {},
    )


def _build_reason(
    spot: SpotRecord,
    *,
    matched_interests: list[str],
    itinerary_similarity: bool,
    has_behavior_match: bool,
) -> str:
    if matched_interests:
        return f"因为你偏好{'与'.join(matched_interests[:2])}"
    if itinerary_similarity:
        return "与你加入行程的景点风格相近"
    if has_behavior_match:
        return "结合你的浏览与收藏偏好推荐"
    if float(spot.rating or 0) >= 4.5 and (float(spot.price or 0) == 0 or float(spot.price or 0) <= 220):
        return "高评分且价格适中"
    if spot.city:
        return f"{spot.city} 热门目的地中的高口碑景点"
    return DEFAULT_RECOMMENDATION_REASON


def _recommendation_items(
    request,
    *,
    spots: list[SpotRecord],
    user_id: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    itinerary_map = _itinerary_lookup(user_id)
    popularity_counts = Counter(
        TravelDiscoverySignal.objects.filter(spot_key__in=[spot.spot_key for spot in spots]).values_list("spot_key", flat=True)
    )

    interest_tokens: list[str] = []
    liked_terms: set[str] = set()
    booked_terms: set[str] = set()
    viewed_terms: set[str] = set()

    if user_id:
        profile = _get_profile_payload(request, user_id)
        interest_tokens = _extract_interest_tokens(profile)
        liked_terms.update(token.lower() for token in interest_tokens)

        for item in TravelItineraryItem.objects.filter(user_id=user_id):
            liked_terms.add(str(item.city or "").lower())
            liked_terms.update(str(tag).lower() for tag in (item.tags or []))

        recent_signals = TravelDiscoverySignal.objects.filter(user_id=user_id).order_by("-created_at")[:50]
        for signal in recent_signals:
            if signal.signal_type == "view":
                viewed_terms.add(signal.spot_key.lower())
            elif signal.signal_type == "booking_intent":
                booked_terms.add(signal.spot_key.lower())

    scored: list[tuple[float, dict[str, Any]]] = []
    for spot in spots:
        base_price = float(spot.price or 0)
        score = float(spot.rating or 0) * 18
        score += min(popularity_counts.get(spot.spot_key, 0), 12) * 1.4

        if base_price == 0:
            score += 8
        elif base_price <= 120:
            score += 10
        elif base_price <= 220:
            score += 6
        elif base_price <= 320:
            score += 3

        matched_interests = [
            token
            for token in interest_tokens
            if token and (
                token.lower() in spot.name.lower()
                or token.lower() in spot.description.lower()
                or token.lower() == spot.city.lower()
                or token.lower() in [str(tag).lower() for tag in spot.tags]
            )
        ]

        itinerary_similarity = any(str(tag).lower() in liked_terms for tag in spot.tags) or spot.city.lower() in liked_terms
        behavior_match = spot.spot_key.lower() in viewed_terms or spot.spot_key.lower() in booked_terms

        if matched_interests:
            score += 20
        if itinerary_similarity:
            score += 14
        if behavior_match:
            score += 8

        reason = _build_reason(
            spot,
            matched_interests=matched_interests,
            itinerary_similarity=itinerary_similarity,
            has_behavior_match=behavior_match,
        )
        scored.append(
            (
                score,
                _serialize_spot(
                    spot,
                    in_itinerary=spot.spot_key in itinerary_map,
                    recommendation_reason=reason,
                ),
            )
        )

    scored.sort(key=lambda pair: (-pair[0], -pair[1]["rating"], pair[1]["price"], pair[1]["name"]))
    return [item for _, item in scored[:limit]]


@api_view(["GET"])
def discovery_spots(request):
    repository = get_spot_repository()
    query = str(request.query_params.get("q") or "").strip()
    city = str(request.query_params.get("city") or "").strip()
    duration = str(request.query_params.get("duration") or "").strip()
    sort = str(request.query_params.get("sort") or "recommended").strip() or "recommended"
    limit = int(request.query_params.get("limit") or 0)
    limit = max(0, min(limit, 60))
    page = int(request.query_params.get("page") or 1)
    page = max(1, page)
    page_size = int(request.query_params.get("page_size") or 0)
    page_size = max(0, min(page_size, 60))
    min_price = _safe_float(request.query_params.get("min_price"))
    max_price = _safe_float(request.query_params.get("max_price"))
    min_rating = _safe_float(request.query_params.get("min_rating"))
    tags = _query_tags(request)
    user_id = get_user_id_from_request(request)
    itinerary_map = _itinerary_lookup(user_id)

    available_spots = repository.list_spots()
    filtered_spots = repository.list_spots(
        query=query,
        city=city,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        duration=duration,
        tags=tags,
        sort=sort,
    )
    total = len(filtered_spots)
    if page_size:
        start = (page - 1) * page_size
        end = start + page_size
        visible_spots = filtered_spots[start:end]
    else:
        visible_spots = filtered_spots[:limit] if limit else filtered_spots

    available_tags = sorted({tag for spot in available_spots for tag in spot.tags})
    items = [
        _serialize_spot(
            spot,
            in_itinerary=spot.spot_key in itinerary_map,
            recommendation_reason=DEFAULT_RECOMMENDATION_REASON,
        )
        for spot in visible_spots
    ]

    return Response(
        {
            "items": items,
            "filters": {
                "cities": list_available_cities(available_spots),
                "tags": available_tags,
            },
            "total": total,
            "source": "knowledge_base_fallback",
            "page": page,
            "page_size": page_size or (len(visible_spots) if limit else total),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def discovery_spot_detail(request, spot_key: str):
    repository = get_spot_repository()
    spot = repository.get_spot(spot_key)
    if not spot:
        return Response({"error": "spot not found"}, status=status.HTTP_404_NOT_FOUND)

    user_id = get_user_id_from_request(request)
    itinerary_map = _itinerary_lookup(user_id)
    if user_id:
        _log_signal(user_id, spot.spot_key, "view", {"path": "detail"})

    similar_spots = [
        _serialize_spot(
            item,
            in_itinerary=item.spot_key in itinerary_map,
            recommendation_reason="与你加入行程的景点风格相近" if item.city == spot.city else DEFAULT_RECOMMENDATION_REASON,
        )
        for item in repository.related_spots(spot, limit=4)
    ]

    payload = _serialize_spot(
        spot,
        in_itinerary=spot.spot_key in itinerary_map,
        recommendation_reason=DEFAULT_RECOMMENDATION_REASON,
    )
    payload["similar_spots"] = similar_spots
    return Response(payload, status=status.HTTP_200_OK)


@api_view(["GET"])
def discovery_recommendations(request):
    repository = get_spot_repository()
    limit = int(request.query_params.get("limit") or 8)
    limit = max(1, min(limit, 24))
    query = str(request.query_params.get("q") or "").strip()
    city = str(request.query_params.get("city") or "").strip()
    duration = str(request.query_params.get("duration") or "").strip()
    min_price = _safe_float(request.query_params.get("min_price"))
    max_price = _safe_float(request.query_params.get("max_price"))
    min_rating = _safe_float(request.query_params.get("min_rating"))
    tags = _query_tags(request)
    user_id = get_user_id_from_request(request)

    spots = repository.list_spots(
        query=query,
        city=city,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        duration=duration,
        tags=tags,
        sort="recommended",
    )

    items = _recommendation_items(request, spots=spots, user_id=user_id, limit=limit)
    return Response(
        {
            "items": items,
            "mode": "personalized_hybrid" if user_id else "generic",
            "source": "knowledge_base_fallback",
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
def discovery_classification(request):
    limit = int(request.query_params.get("limit") or 50)
    city = str(request.query_params.get("city") or "").strip()
    category = str(request.query_params.get("category") or "").strip()
    return Response(classification_payload(limit=limit, city=city, category=category), status=status.HTTP_200_OK)


@api_view(["GET"])
def discovery_semantic_recommendations(request):
    limit = int(request.query_params.get("limit") or 12)
    query = str(request.query_params.get("q") or request.query_params.get("preference") or "").strip()
    city = str(request.query_params.get("city") or "").strip()
    category = str(request.query_params.get("category") or "").strip()
    return Response(
        semantic_recommendations(query=query, city=city, category=category, limit=limit),
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def itinerary_optimize_route(request):
    city = str(request.data.get("city") or "").strip()
    if not city:
        return Response({"error": "city is required"}, status=status.HTTP_400_BAD_REQUEST)

    days = int(request.data.get("days") or 2)
    days = max(1, min(days, 7))
    spots_per_day = int(request.data.get("spots_per_day") or 4)
    spots_per_day = max(1, min(spots_per_day, 6))
    budget = _safe_float(request.data.get("budget"), 0) or 0
    preference = str(request.data.get("preference") or "").strip()

    payload = optimize_route(
        city=city,
        days=days,
        preference=preference,
        budget=budget,
        spots_per_day=spots_per_day,
    )
    return Response(payload, status=status.HTTP_200_OK)


@api_view(["GET"])
def itinerary_list(request):
    user_id = get_user_id_from_request(request)
    if not user_id:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    items = list(TravelItineraryItem.objects.filter(user_id=user_id).order_by("-created_at", "-id"))
    return Response(
        {
            "items": TravelItineraryItemSerializer(items, many=True).data,
            "summary": _summary_from_items(items),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
def itinerary_add_item(request):
    user_id = get_user_id_from_request(request)
    if not user_id:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    spot_key = str(request.data.get("spot_key") or "").strip()
    if not spot_key:
        return Response({"error": "spot_key is required"}, status=status.HTTP_400_BAD_REQUEST)

    repository = get_spot_repository()
    spot = repository.get_spot(spot_key)
    if not spot:
        return Response({"error": "spot not found"}, status=status.HTTP_404_NOT_FOUND)

    recommendation_reason = str(request.data.get("recommendation_reason") or DEFAULT_RECOMMENDATION_REASON).strip()
    snapshot = _spot_snapshot(spot, recommendation_reason)

    item, created = TravelItineraryItem.objects.update_or_create(
        user_id=user_id,
        spot_key=spot.spot_key,
        defaults={
            "spot_name": spot.name,
            "city": spot.city,
            "price": float(spot.price or 0),
            "rating": float(spot.rating or 0),
            "cover_image": spot.cover_image,
            "recommendation_reason": recommendation_reason,
            "tags": list(spot.tags or []),
            "spot_snapshot": snapshot,
        },
    )

    _log_signal(
        user_id,
        spot.spot_key,
        "itinerary_add",
        {
            "created": created,
            "recommendation_reason": recommendation_reason,
        },
    )

    items = list(TravelItineraryItem.objects.filter(user_id=user_id).order_by("-created_at", "-id"))
    return Response(
        {
            "item": TravelItineraryItemSerializer(item).data,
            "summary": _summary_from_items(items),
        },
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["DELETE"])
def itinerary_delete_item(request, item_id: int):
    user_id = get_user_id_from_request(request)
    if not user_id:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        item = TravelItineraryItem.objects.get(id=item_id, user_id=user_id)
    except TravelItineraryItem.DoesNotExist:
        return Response({"error": "itinerary item not found"}, status=status.HTTP_404_NOT_FOUND)

    item.delete()
    items = list(TravelItineraryItem.objects.filter(user_id=user_id).order_by("-created_at", "-id"))
    return Response({"summary": _summary_from_items(items)}, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
def booking_intents(request):
    user_id = get_user_id_from_request(request)
    if not user_id:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == "GET":
        intents = TravelBookingIntent.objects.filter(user_id=user_id).order_by("-created_at", "-id")
        return Response({"items": TravelBookingIntentSerializer(intents, many=True).data}, status=status.HTTP_200_OK)

    raw_item_ids = request.data.get("item_ids") or []
    if isinstance(raw_item_ids, str):
        raw_item_ids = [part.strip() for part in raw_item_ids.split(",") if part.strip()]

    itinerary_qs = TravelItineraryItem.objects.filter(user_id=user_id)
    if raw_item_ids:
        itinerary_qs = itinerary_qs.filter(id__in=raw_item_ids)
    items = list(itinerary_qs.order_by("-created_at", "-id"))
    if not items:
        return Response({"error": "No itinerary items selected"}, status=status.HTTP_400_BAD_REQUEST)

    serialized_items = []
    total_cost = 0.0
    for item in items:
        serialized_items.append(
            {
                "item_id": item.id,
                "spot_key": item.spot_key,
                "spot_name": item.spot_name,
                "city": item.city,
                "price": round(float(item.price or 0), 2),
                "rating": round(float(item.rating or 0), 1),
                "cover_image": item.cover_image,
                "recommendation_reason": item.recommendation_reason,
                "tags": item.tags or [],
            }
        )
        total_cost += float(item.price or 0)

    intent = TravelBookingIntent.objects.create(
        user_id=user_id,
        trip_name=str(request.data.get("trip_name") or "").strip(),
        contact_name=str(request.data.get("contact_name") or "").strip(),
        contact_phone=str(request.data.get("contact_phone") or "").strip(),
        note=str(request.data.get("note") or "").strip(),
        status="pending",
        total_estimated_cost=round(total_cost, 2),
        items=serialized_items,
    )

    for item in items:
        _log_signal(
            user_id,
            item.spot_key,
            "booking_intent",
            {"intent_id": intent.id, "trip_name": intent.trip_name},
        )

    return Response(TravelBookingIntentSerializer(intent).data, status=status.HTTP_201_CREATED)
