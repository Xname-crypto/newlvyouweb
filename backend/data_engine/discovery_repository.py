from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import re
from typing import Iterable, Sequence

from django.db.utils import OperationalError, ProgrammingError

from .models import KnowledgeBase
from .scenic_data import find_scenic_xlsx


TAG_RULES = {
    "探险": ["探险", "徒步", "攀登", "峡谷", "漂流", "穿越", "登山"],
    "摄影": ["摄影", "拍照", "机位", "观景", "日落", "夜景", "出片", "光影"],
    "自然": ["自然", "山", "湖", "森林", "海", "沙滩", "公园", "湿地", "瀑布", "草原"],
    "城市": ["城市", "地标", "街区", "古镇", "商圈", "夜游", "漫步", "都市"],
    "人文": ["博物馆", "纪念馆", "历史", "古迹", "文化", "建筑", "寺", "庙", "展馆"],
    "亲子": ["亲子", "乐园", "动物园", "海洋馆", "科技馆", "儿童", "家庭"],
}

@dataclass(slots=True)
class SpotRecord:
    spot_key: str
    source_type: str
    source_id: str
    name: str
    city: str
    rating: float
    price: float
    description: str
    cover_image: str
    tags: list[str]
    opening_hours: str
    visit_duration: str
    booking_required: str
    address: str
    raw_metadata: dict


@dataclass(slots=True)
class SpotExtraInfo:
    opening_hours: str
    visit_duration: str
    booking_required: str
    address: str
    cover_image: str


def _safe_float(value: object, default: float = 0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_text(value: object) -> str:
    return str(value or "").strip()


def _extract_line_value(text: str, label: str) -> str:
    match = re.search(rf"{re.escape(label)}[:：]\s*(.+)", text)
    return match.group(1).strip() if match else ""


def _extract_description(text: str) -> str:
    description = _extract_line_value(text, "简介")
    if description:
        return description

    compact = [line.strip() for line in text.splitlines() if line.strip()]
    if not compact:
        return ""

    if compact[0].startswith("景点名称"):
        compact = compact[1:]
    return " ".join(compact)[:220]


def _extract_cover(metadata: dict) -> str:
    direct_fields = [
        metadata.get("cover_image"),
        metadata.get("cover"),
        metadata.get("image"),
        metadata.get("image_url"),
    ]
    for value in direct_fields:
        if isinstance(value, str) and value.strip():
            return value.strip()

    images = metadata.get("images")
    if isinstance(images, list):
        for item in images:
            if isinstance(item, str) and item.strip():
                return item.strip()
    if isinstance(images, str) and images.strip():
        first = re.split(r"[,|]", images)[0].strip()
        if first:
            return first
    return ""


def _build_spot_key(city: str, name: str, source_id: str) -> str:
    city_key = _normalize_lookup_text(city)[:24]
    name_key = _normalize_lookup_text(name)[:48]
    if city_key or name_key:
        return f"xlsx-{city_key}-{name_key}".strip("-")
    return f"xlsx-{source_id}"


def _normalize_lookup_text(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    return re.sub(r"[\s·•,，/\\()（）【】\[\]\-—_]+", "", text)


def _extra_info_score(info: SpotExtraInfo) -> int:
    return sum(
        1
        for value in (
            info.opening_hours,
            info.visit_duration,
            info.booking_required,
            info.address,
            info.cover_image,
        )
        if str(value or "").strip()
    )


@lru_cache(maxsize=1)
def _load_spot_extra_info() -> tuple[dict[tuple[str, str], SpotExtraInfo], dict[str, SpotExtraInfo]]:
    by_city_and_name: dict[tuple[str, str], SpotExtraInfo] = {}
    by_name: dict[str, SpotExtraInfo] = {}

    try:
        import pandas as pd

        path = find_scenic_xlsx()
        dataframe = pd.read_excel(path).fillna("")
    except (Exception, FileNotFoundError):
        return by_city_and_name, by_name

    for _, row in dataframe.iterrows():
        name = str(row.get("名称") or "").strip()
        city = str(row.get("城市") or "").strip()
        if not name:
            continue

        info = SpotExtraInfo(
            opening_hours=str(row.get("开放时间") or "").strip(),
            visit_duration=str(row.get("游玩时间") or "").strip(),
            booking_required=str(row.get("是否需要预定") or "").strip(),
            address=str(row.get("具体地址") or "").strip(),
            cover_image=str(row.get("图片URL") or "").strip(),
        )

        name_key = _normalize_lookup_text(name)
        city_key = _normalize_lookup_text(city)
        if not name_key:
            continue

        pair_key = (name_key, city_key)
        current_pair = by_city_and_name.get(pair_key)
        if current_pair is None or _extra_info_score(info) > _extra_info_score(current_pair):
            by_city_and_name[pair_key] = info

        current_name = by_name.get(name_key)
        if current_name is None or _extra_info_score(info) > _extra_info_score(current_name):
            by_name[name_key] = info

    return by_city_and_name, by_name


@lru_cache(maxsize=1)
def _load_xlsx_spots() -> list[SpotRecord]:
    try:
        import pandas as pd

        path = find_scenic_xlsx()
        dataframe = pd.read_excel(path).fillna("")
    except (Exception, FileNotFoundError):
        return []

    spots: list[SpotRecord] = []
    for index, row in dataframe.iterrows():
        name = _safe_text(row.get("名称"))
        city = _safe_text(row.get("城市"))
        if not name:
            continue

        description = _safe_text(row.get("简介"))
        cover_image = _safe_text(row.get("图片URL"))
        metadata = {
            "name": name,
            "city": city,
            "star_rating": _safe_text(row.get("星级")),
            "rating": _safe_float(row.get("评分"), 0),
            "price": _safe_float(row.get("价格"), 0),
            "sales_volume": _safe_text(row.get("销量")),
            "region": _safe_text(row.get("省/市/区")),
            "coordinates": _safe_text(row.get("坐标")),
            "description": description,
            "is_free": _safe_text(row.get("是否免费")),
            "opening_hours": _safe_text(row.get("开放时间")),
            "visit_duration": _safe_text(row.get("游玩时间")),
            "booking_required": _safe_text(row.get("是否需要预定")),
            "address": _safe_text(row.get("具体地址")),
            "cover_image": cover_image,
        }
        tags = _infer_tags(name, description, city, metadata)

        spots.append(
            SpotRecord(
                spot_key=_build_spot_key(city, name, str(index + 1)),
                source_type="xlsx",
                source_id=str(index + 1),
                name=name,
                city=city,
                rating=_safe_float(row.get("评分"), 0),
                price=_safe_float(row.get("价格"), 0),
                description=description,
                cover_image=cover_image,
                tags=tags,
                opening_hours=_safe_text(row.get("开放时间")),
                visit_duration=_safe_text(row.get("游玩时间")),
                booking_required=_safe_text(row.get("是否需要预定")),
                address=_safe_text(row.get("具体地址")),
                raw_metadata=metadata,
            )
        )

    return spots


def _match_spot_extra_info(name: str, city: str) -> SpotExtraInfo | None:
    by_city_and_name, by_name = _load_spot_extra_info()
    name_key = _normalize_lookup_text(name)
    city_key = _normalize_lookup_text(city)
    if not name_key:
        return None

    exact_match = by_city_and_name.get((name_key, city_key))
    if exact_match:
        return exact_match
    return by_name.get(name_key)


def _infer_tags(name: str, description: str, city: str, metadata: dict) -> list[str]:
    raw_tags = metadata.get("tags")
    if isinstance(raw_tags, list):
        normalized = [str(tag).strip() for tag in raw_tags if str(tag).strip()]
        if normalized:
            return normalized[:5]

    bag = "\n".join([name, description, city, str(metadata.get("keywords") or "")]).lower()
    tags: list[str] = []
    for tag, keywords in TAG_RULES.items():
        if any(keyword.lower() in bag for keyword in keywords):
            tags.append(tag)

    if not tags:
        tags = ["城市"] if city else ["自然"]
    return tags[:5]


def _parse_duration_hours(value: str) -> tuple[float, float] | None:
    text = str(value or "").strip()
    if not text:
        return None

    if "半天" in text:
        return (4, 6)

    numbers = [float(number) for number in re.findall(r"\d+(?:\.\d+)?", text)]
    if not numbers:
        return None

    if "天" in text:
        if len(numbers) >= 2:
            return (numbers[0] * 24, numbers[1] * 24)
        return (numbers[0] * 24, numbers[0] * 24)

    if "小时" in text or "时" in text:
        if len(numbers) >= 2:
            return (numbers[0], numbers[1])
        return (numbers[0], numbers[0])

    return None


def _match_duration_filter(visit_duration: str, duration_key: str) -> bool:
    if not duration_key:
        return True

    parsed = _parse_duration_hours(visit_duration)
    if parsed is None:
        return False

    min_hours, max_hours = parsed
    if duration_key == "up_to_1_hour":
        return max_hours <= 1
    if duration_key == "one_to_four_hours":
        return min_hours <= 4 and max_hours >= 1
    if duration_key == "four_hours_to_one_day":
        return min_hours <= 24 and max_hours >= 4
    if duration_key == "one_to_three_days":
        return min_hours <= 72 and max_hours >= 24
    if duration_key == "three_days_or_more":
        return max_hours >= 72
    return True


def _serialize_kb_spot(item: KnowledgeBase) -> SpotRecord | None:
    metadata = item.metadata if isinstance(item.metadata, dict) else {}
    if str(metadata.get("category") or "").strip() != "景点数据":
        return None

    content = str(item.content or "").strip()
    name = str(metadata.get("name") or f"景点 {item.id}").strip()
    city = str(metadata.get("city") or _extract_line_value(content, "位置") or "未知城市").strip()
    rating = _safe_float(metadata.get("rating"), _safe_float(_extract_line_value(content, "评分"), 0))
    price = _safe_float(metadata.get("price"), _safe_float(_extract_line_value(content, "价格"), 0))
    description = str(metadata.get("description") or "").strip() or _extract_description(content)
    cover_image = _extract_cover(metadata)
    tags = _infer_tags(name, description, city, metadata)
    extra_info = _match_spot_extra_info(name, city)

    if extra_info and extra_info.cover_image and not cover_image:
        cover_image = extra_info.cover_image

    return SpotRecord(
        spot_key=f"kb-{item.id}",
        source_type="knowledge_base",
        source_id=str(item.id),
        name=name,
        city=city,
        rating=rating,
        price=price,
        description=description,
        cover_image=cover_image,
        tags=tags,
        opening_hours=extra_info.opening_hours if extra_info else "",
        visit_duration=extra_info.visit_duration if extra_info else "",
        booking_required=extra_info.booking_required if extra_info else "",
        address=extra_info.address if extra_info else str(metadata.get("address") or "").strip(),
        raw_metadata=metadata,
    )


class BaseSpotRepository:
    def list_spots(
        self,
        *,
        query: str = "",
        city: str = "",
        min_price: float | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
        duration: str = "",
        tags: Sequence[str] | None = None,
        sort: str = "recommended",
    ) -> list[SpotRecord]:
        raise NotImplementedError

    def get_spot(self, spot_key: str) -> SpotRecord | None:
        raise NotImplementedError

    def related_spots(self, spot: SpotRecord, limit: int = 4) -> list[SpotRecord]:
        raise NotImplementedError


class KnowledgeBaseSpotRepository(BaseSpotRepository):
    def _all_spots(self) -> list[SpotRecord]:
        xlsx_spots = _load_xlsx_spots()
        if xlsx_spots:
            return xlsx_spots

        rows: list[SpotRecord] = []
        try:
            queryset = KnowledgeBase.objects.filter(kind="document").order_by("id")
            for item in queryset.iterator():
                spot = _serialize_kb_spot(item)
                if spot:
                    rows.append(spot)
        except (OperationalError, ProgrammingError):
            return rows
        return rows

    def list_spots(
        self,
        *,
        query: str = "",
        city: str = "",
        min_price: float | None = None,
        max_price: float | None = None,
        min_rating: float | None = None,
        duration: str = "",
        tags: Sequence[str] | None = None,
        sort: str = "recommended",
    ) -> list[SpotRecord]:
        tag_set = {str(tag).strip() for tag in (tags or []) if str(tag).strip()}
        query_lower = query.strip().lower()
        city = city.strip()
        filtered: list[SpotRecord] = []

        for spot in self._all_spots():
            if city and spot.city != city:
                continue
            if min_price is not None and spot.price < min_price:
                continue
            if max_price is not None and spot.price > max_price:
                continue
            if min_rating is not None and spot.rating < min_rating:
                continue
            if duration and not _match_duration_filter(spot.visit_duration, duration):
                continue
            if tag_set and not tag_set.intersection(spot.tags):
                continue
            if query_lower:
                haystack = f"{spot.name}\n{spot.description}\n{spot.city}\n{' '.join(spot.tags)}".lower()
                if query_lower not in haystack:
                    continue
            filtered.append(spot)

        if sort == "price_asc":
            filtered.sort(key=lambda item: (item.price <= 0, item.price, -item.rating, item.name))
        elif sort == "rating_desc":
            filtered.sort(key=lambda item: (-item.rating, item.price, item.name))
        else:
            filtered.sort(key=lambda item: (-item.rating, item.price <= 0, item.price, item.name))
        return filtered

    def get_spot(self, spot_key: str) -> SpotRecord | None:
        for spot in self._all_spots():
            if spot.spot_key == spot_key:
                return spot
        return None

    def related_spots(self, spot: SpotRecord, limit: int = 4) -> list[SpotRecord]:
        scored: list[tuple[int, SpotRecord]] = []
        base_tags = set(spot.tags)
        for item in self._all_spots():
            if item.spot_key == spot.spot_key:
                continue
            score = 0
            if item.city == spot.city:
                score += 6
            score += len(base_tags.intersection(item.tags)) * 4
            if item.price and spot.price and abs(item.price - spot.price) <= 40:
                score += 2
            if item.rating >= 4.5:
                score += 1
            scored.append((score, item))

        scored.sort(key=lambda pair: (-pair[0], -pair[1].rating, pair[1].price, pair[1].name))
        return [item for _, item in scored[:limit]]


def get_spot_repository() -> BaseSpotRepository:
    return KnowledgeBaseSpotRepository()


def list_available_cities(spots: Iterable[SpotRecord]) -> list[str]:
    cities = sorted({spot.city for spot in spots if spot.city})
    return cities
