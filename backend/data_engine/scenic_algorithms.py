from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from math import exp, log, radians, sin, cos, asin, sqrt
from pathlib import Path
import hashlib
import random
import re
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd


SCENIC_XLSX_SIZE = 479040
CATEGORY_RULES: dict[str, tuple[str, ...]] = {
    "natural_landscape": (
        "山", "湖", "峡谷", "森林", "草原", "湿地", "瀑布", "海", "湾", "岛",
        "峰", "河", "溪", "洞", "温泉", "风景", "自然",
    ),
    "history_culture": (
        "古城", "古镇", "遗址", "故居", "纪念", "历史", "文化", "陵", "城墙",
        "老街", "园林", "王府", "名人", "革命",
    ),
    "museum_exhibition": (
        "博物馆", "科技馆", "展览", "美术馆", "艺术馆", "纪念馆", "陈列馆",
        "规划馆", "天文馆",
    ),
    "theme_parent_child": (
        "乐园", "动物园", "海洋", "水世界", "游乐", "迪士尼", "方特", "欢乐谷",
        "亲子", "马戏", "表演", "熊猫", "动物", "海洋馆", "海昌",
    ),
    "religious_sites": (
        "寺", "庙", "佛", "道观", "教堂", "清真", "宫", "塔", "禅", "祠",
    ),
    "urban_landmark": (
        "广场", "大厦", "中心", "步行街", "夜景", "地标", "街区", "码头",
        "观光", "城市", "塔", "桥",
    ),
}
CATEGORY_LABELS = {
    "natural_landscape": "自然风光",
    "history_culture": "历史文化",
    "museum_exhibition": "博物展馆",
    "theme_parent_child": "主题亲子",
    "religious_sites": "宗教古迹",
    "urban_landmark": "城市地标",
}


@dataclass(slots=True)
class ScenicRecord:
    spot_key: str
    city: str
    name: str
    rating: float
    price: float
    sales: float
    region: str
    longitude: float | None
    latitude: float | None
    description: str
    is_free: bool
    opening_hours: str
    visit_duration: str
    booking_required: str
    address: str
    image_url: str
    text: str


@dataclass(slots=True)
class ScenicModel:
    records: list[ScenicRecord]
    vocabulary: list[str]
    idf: dict[str, float]
    tfidf_vectors: dict[str, dict[str, float]]
    keywords: dict[str, list[str]]
    weak_labels: dict[str, str]
    class_priors: dict[str, float]
    feature_log_probs: dict[str, dict[str, float]]
    category_predictions: dict[str, dict[str, Any]]
    semantic_vectors: dict[str, np.ndarray]


def _find_scenic_xlsx() -> Path:
    root = Path(__file__).resolve().parents[2]
    preferred = root / "旅游景点_含开放信息_配图.xlsx"
    if preferred.exists():
        return preferred
    for path in root.glob("*.xlsx"):
        try:
            if path.stat().st_size == SCENIC_XLSX_SIZE:
                return path
        except OSError:
            continue
    raise FileNotFoundError("scenic xlsx file not found")


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_float(value: Any, default: float = 0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_bool(value: Any) -> bool:
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "是", "免费"}


def _parse_coord(value: Any) -> tuple[float | None, float | None]:
    parts = [part.strip() for part in str(value or "").split(",")]
    if len(parts) != 2:
        return None, None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None, None


def _parse_hours(value: Any, default: float = 3) -> float:
    text = str(value or "")
    numbers = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", text)]
    if not numbers:
        return default
    if "天" in text:
        return sum(numbers[:2]) / min(len(numbers), 2) * 8
    if len(numbers) >= 2:
        return sum(numbers[:2]) / 2
    return numbers[0]


def _tokenize(text: str) -> list[str]:
    text = re.sub(r"https?://\S+", " ", str(text).lower())
    tokens = re.findall(r"[\u4e00-\u9fff]{2,}|[a-z0-9]{2,}", text)
    expanded: list[str] = []
    for token in tokens:
        expanded.append(token)
        if re.fullmatch(r"[\u4e00-\u9fff]{4,}", token):
            expanded.extend(token[i : i + 2] for i in range(len(token) - 1))
            expanded.extend(token[i : i + 3] for i in range(len(token) - 2))
    stopwords = {"景区", "景点", "旅游", "地址", "小时", "开放", "时间", "建议", "预订"}
    return [token for token in expanded if token not in stopwords]


def _load_records() -> list[ScenicRecord]:
    dataframe = pd.read_excel(_find_scenic_xlsx()).fillna("")
    cols = list(dataframe.columns)
    city, name, _star, rating, price, sales, region, coord, intro, free, opening, duration, reserve, address, image = cols[:15]
    records: list[ScenicRecord] = []
    for index, row in dataframe.iterrows():
        spot_name = _safe_text(row.get(name))
        spot_city = _safe_text(row.get(city))
        if not spot_name:
            continue
        longitude, latitude = _parse_coord(row.get(coord))
        text = " ".join(
            [
                spot_name,
                _safe_text(row.get(intro)),
                spot_city,
                _safe_text(row.get(region)),
                _safe_text(row.get(address)),
                _safe_text(row.get(duration)),
                _safe_text(row.get(reserve)),
            ]
        )
        key_city = re.sub(r"\W+", "", spot_city.lower())[:24]
        key_name = re.sub(r"\W+", "", spot_name.lower())[:48]
        records.append(
            ScenicRecord(
                spot_key=f"xlsx-{key_city}-{key_name}" if key_name else f"xlsx-{index + 1}",
                city=spot_city,
                name=spot_name,
                rating=_safe_float(row.get(rating)),
                price=_safe_float(row.get(price)),
                sales=_safe_float(row.get(sales)),
                region=_safe_text(row.get(region)),
                longitude=longitude,
                latitude=latitude,
                description=_safe_text(row.get(intro)),
                is_free=_parse_bool(row.get(free)),
                opening_hours=_safe_text(row.get(opening)),
                visit_duration=_safe_text(row.get(duration)),
                booking_required=_safe_text(row.get(reserve)),
                address=_safe_text(row.get(address)),
                image_url=_safe_text(row.get(image)),
                text=text,
            )
        )
    return records


def _build_tfidf(records: Sequence[ScenicRecord]) -> tuple[list[str], dict[str, float], dict[str, dict[str, float]], dict[str, list[str]]]:
    tokenized = {record.spot_key: _tokenize(record.text) for record in records}
    document_frequency: Counter[str] = Counter()
    for tokens in tokenized.values():
        document_frequency.update(set(tokens))

    total = max(1, len(records))
    vocabulary = sorted(token for token, count in document_frequency.items() if count >= 2)
    idf = {token: log((1 + total) / (1 + document_frequency[token])) + 1 for token in vocabulary}
    tfidf_vectors: dict[str, dict[str, float]] = {}
    keywords: dict[str, list[str]] = {}
    vocabulary_set = set(vocabulary)

    for key, tokens in tokenized.items():
        counts = Counter(token for token in tokens if token in vocabulary_set)
        denominator = max(1, sum(counts.values()))
        vector = {token: (count / denominator) * idf[token] for token, count in counts.items()}
        tfidf_vectors[key] = vector
        keywords[key] = [token for token, _ in sorted(vector.items(), key=lambda item: item[1], reverse=True)[:20]]
    return vocabulary, idf, tfidf_vectors, keywords


def _weak_label(record: ScenicRecord, keywords: Sequence[str]) -> str:
    bag = " ".join([record.name, record.description, record.address, record.region, *keywords])
    scores = {
        category: sum(1 for keyword in rule_keywords if keyword in bag)
        for category, rule_keywords in CATEGORY_RULES.items()
    }
    priority = {
        "theme_parent_child": 6,
        "museum_exhibition": 5,
        "religious_sites": 4,
        "history_culture": 3,
        "urban_landmark": 2,
        "natural_landscape": 1,
    }
    best_category, best_score = max(scores.items(), key=lambda item: (item[1], priority.get(item[0], 0)))
    if best_score > 0:
        return best_category
    if record.is_free or record.price <= 20:
        return "urban_landmark"
    return "natural_landscape"


def _train_naive_bayes(records: Sequence[ScenicRecord], keywords: dict[str, list[str]], weak_labels: dict[str, str]) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    class_counts = Counter(weak_labels.values())
    total_docs = max(1, len(records))
    class_priors = {category: log(count / total_docs) for category, count in class_counts.items()}

    feature_counts: dict[str, Counter[str]] = defaultdict(Counter)
    class_token_totals: Counter[str] = Counter()
    vocabulary = sorted({token for tokens in keywords.values() for token in tokens})
    vocab_size = max(1, len(vocabulary))

    for record in records:
        category = weak_labels[record.spot_key]
        for token in keywords.get(record.spot_key, []):
            feature_counts[category][token] += 1
            class_token_totals[category] += 1

    feature_log_probs: dict[str, dict[str, float]] = {}
    for category in class_counts:
        denominator = class_token_totals[category] + vocab_size
        feature_log_probs[category] = {
            token: log((feature_counts[category][token] + 1) / denominator)
            for token in vocabulary
        }
        feature_log_probs[category]["__unknown__"] = log(1 / denominator)
    return class_priors, feature_log_probs


def _predict_category(tokens: Sequence[str], class_priors: dict[str, float], feature_log_probs: dict[str, dict[str, float]]) -> dict[str, Any]:
    scores: dict[str, float] = {}
    for category, prior in class_priors.items():
        score = prior
        probs = feature_log_probs[category]
        fallback = probs.get("__unknown__", -20)
        for token in tokens:
            score += probs.get(token, fallback)
        scores[category] = score

    max_score = max(scores.values()) if scores else 0
    exp_scores = {category: exp(score - max_score) for category, score in scores.items()}
    total = sum(exp_scores.values()) or 1
    probabilities = {category: value / total for category, value in exp_scores.items()}
    category = max(probabilities.items(), key=lambda item: item[1])[0]
    return {
        "category": category,
        "category_label": CATEGORY_LABELS.get(category, category),
        "confidence": round(probabilities[category], 4),
        "probabilities": {
            CATEGORY_LABELS.get(key, key): round(value, 4)
            for key, value in sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
        },
    }


def _semantic_vector(text: str, dimensions: int = 256) -> np.ndarray:
    vector = np.zeros(dimensions, dtype=np.float32)
    for token in _tokenize(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "little") % dimensions
        sign = 1 if digest[4] % 2 == 0 else -1
        vector[index] += sign
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector


@lru_cache(maxsize=1)
def get_scenic_model() -> ScenicModel:
    records = _load_records()
    vocabulary, idf, tfidf_vectors, keywords = _build_tfidf(records)
    weak_labels = {record.spot_key: _weak_label(record, keywords[record.spot_key]) for record in records}
    class_priors, feature_log_probs = _train_naive_bayes(records, keywords, weak_labels)
    category_predictions = {
        record.spot_key: _predict_category(keywords[record.spot_key], class_priors, feature_log_probs)
        for record in records
    }
    semantic_vectors = {
        record.spot_key: _semantic_vector(" ".join([record.text, " ".join(keywords[record.spot_key])]))
        for record in records
    }
    return ScenicModel(
        records=records,
        vocabulary=vocabulary,
        idf=idf,
        tfidf_vectors=tfidf_vectors,
        keywords=keywords,
        weak_labels=weak_labels,
        class_priors=class_priors,
        feature_log_probs=feature_log_probs,
        category_predictions=category_predictions,
        semantic_vectors=semantic_vectors,
    )


def classification_payload(limit: int = 50, city: str = "", category: str = "") -> dict[str, Any]:
    model = get_scenic_model()
    rows = []
    for record in model.records:
        prediction = model.category_predictions[record.spot_key]
        if city and record.city != city:
            continue
        if category and prediction["category"] != category and prediction["category_label"] != category:
            continue
        rows.append(
            {
                "spot_key": record.spot_key,
                "name": record.name,
                "city": record.city,
                "category": prediction["category"],
                "category_label": prediction["category_label"],
                "category_confidence": prediction["confidence"],
                "keywords": model.keywords[record.spot_key],
            }
        )

    category_counts = Counter(item["category_label"] for item in rows)
    return {
        "items": rows[: max(1, min(limit, 200))],
        "total": len(rows),
        "categories": [
            {"category_label": label, "count": count}
            for label, count in sorted(category_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "algorithm": {
            "feature_extractor": "TF-IDF top 20 keywords",
            "classifier": "Multinomial Naive Bayes with weak-label bootstrap",
            "records": len(model.records),
            "vocabulary_size": len(model.vocabulary),
        },
    }


def semantic_recommendations(
    query: str = "",
    city: str = "",
    category: str = "",
    limit: int = 12,
) -> dict[str, Any]:
    model = get_scenic_model()
    query_vector = _semantic_vector(query) if query else None
    rows: list[tuple[float, ScenicRecord]] = []
    max_sales = max((record.sales for record in model.records), default=1) or 1

    for record in model.records:
        prediction = model.category_predictions[record.spot_key]
        if city and record.city != city:
            continue
        if category and prediction["category"] != category and prediction["category_label"] != category:
            continue

        semantic_score = 0.0
        if query_vector is not None:
            semantic_score = float(np.dot(query_vector, model.semantic_vectors[record.spot_key]))
        quality_score = min(record.rating, 5) / 5 if record.rating else 0.35
        popularity_score = log(1 + max(0, record.sales)) / log(1 + max_sales)
        price_score = 0.12 if record.is_free else 0.08 if record.price <= 80 else 0.03
        score = semantic_score * 0.55 + quality_score * 0.22 + popularity_score * 0.18 + price_score
        rows.append((score, record))

    rows.sort(key=lambda item: (-item[0], -item[1].rating, item[1].price, item[1].name))
    items = []
    for score, record in rows[: max(1, min(limit, 50))]:
        prediction = model.category_predictions[record.spot_key]
        items.append(
            {
                "spot_key": record.spot_key,
                "name": record.name,
                "city": record.city,
                "rating": round(record.rating, 1),
                "price": round(record.price, 2),
                "sales": int(record.sales),
                "category": prediction["category"],
                "category_label": prediction["category_label"],
                "keywords": model.keywords[record.spot_key],
                "semantic_score": round(score, 4),
                "description": record.description,
                "cover_image": record.image_url,
                "visit_duration": record.visit_duration,
                "address": record.address,
            }
        )
    return {
        "items": items,
        "mode": "semantic_vector_hybrid",
        "algorithm": "hashed semantic vector + Naive Bayes category + quality/popularity weighting",
    }


def _distance_km(a: ScenicRecord, b: ScenicRecord) -> float:
    if a.longitude is None or a.latitude is None or b.longitude is None or b.latitude is None:
        return 9999
    lon1, lat1, lon2, lat2 = map(radians, [a.longitude, a.latitude, b.longitude, b.latitude])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    value = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(value))


def _route_score(route: Sequence[ScenicRecord], budget: float) -> float:
    if not route:
        return -1e9
    distance = sum(_distance_km(route[i], route[i + 1]) for i in range(len(route) - 1))
    cost = sum(record.price for record in route)
    quality = sum((record.rating or 3.5) + log(1 + max(0, record.sales)) / 3 for record in route)
    budget_penalty = max(0, cost - budget) * 0.04 if budget else 0
    return quality - distance * 0.08 - budget_penalty


def _ant_colony_order(records: list[ScenicRecord], budget: float, iterations: int = 60, ants: int = 24) -> list[ScenicRecord]:
    if len(records) <= 2:
        return records

    pheromone: dict[tuple[int, int], float] = defaultdict(lambda: 1.0)
    best_route = records[:]
    best_score = _route_score(best_route, budget)
    rng = random.Random(42)

    for _ in range(iterations):
        candidates: list[tuple[float, list[ScenicRecord]]] = []
        for _ant in range(ants):
            remaining = list(range(len(records)))
            current = remaining.pop(rng.randrange(len(remaining)))
            order = [current]
            while remaining:
                weights = []
                for nxt in remaining:
                    distance = max(0.2, _distance_km(records[current], records[nxt]))
                    attractiveness = ((records[nxt].rating or 3.5) + 1) / distance
                    weights.append((pheromone[(current, nxt)] ** 1.1) * (attractiveness ** 2.0))
                total = sum(weights) or 1
                pick = rng.random() * total
                cumulative = 0.0
                chosen_position = 0
                for idx, weight in enumerate(weights):
                    cumulative += weight
                    if cumulative >= pick:
                        chosen_position = idx
                        break
                current = remaining.pop(chosen_position)
                order.append(current)
            route = [records[index] for index in order]
            score = _route_score(route, budget)
            candidates.append((score, route))
            if score > best_score:
                best_score = score
                best_route = route

        for edge in list(pheromone):
            pheromone[edge] *= 0.82
        for score, route in sorted(candidates, key=lambda item: item[0], reverse=True)[:6]:
            deposit = max(0.01, score / 100)
            indexes = [records.index(item) for item in route]
            for left, right in zip(indexes, indexes[1:]):
                pheromone[(left, right)] += deposit
    return best_route


def optimize_route(
    *,
    city: str,
    days: int,
    preference: str = "",
    budget: float = 0,
    spots_per_day: int = 4,
) -> dict[str, Any]:
    model = get_scenic_model()
    recommendation = semantic_recommendations(query=preference, city=city, limit=max(days * spots_per_day * 2, 12))
    selected_keys = [item["spot_key"] for item in recommendation["items"]]
    by_key = {record.spot_key: record for record in model.records}
    selected = [by_key[key] for key in selected_keys if key in by_key and by_key[key].longitude is not None and by_key[key].latitude is not None]
    selected = selected[: max(1, days) * max(1, spots_per_day)]
    ordered = _ant_colony_order(selected, budget)

    day_count = max(1, min(days, 7))
    daily_budget = budget / day_count if budget else 0
    chunk_size = max(1, spots_per_day)
    day_routes = []
    for day_index in range(day_count):
        start = day_index * chunk_size
        end = start + chunk_size
        day_records = ordered[start:end]
        distance = sum(_distance_km(day_records[i], day_records[i + 1]) for i in range(len(day_records) - 1))
        cost = sum(record.price for record in day_records)
        hours = sum(_parse_hours(record.visit_duration) for record in day_records)
        day_routes.append(
            {
                "day": day_index + 1,
                "distance_km": round(distance, 2),
                "estimated_hours": round(hours, 1),
                "estimated_cost": round(cost, 2),
                "budget_status": "over_budget" if daily_budget and cost > daily_budget else "ok",
                "spots": [
                    {
                        "spot_key": record.spot_key,
                        "name": record.name,
                        "city": record.city,
                        "category_label": model.category_predictions[record.spot_key]["category_label"],
                        "price": round(record.price, 2),
                        "rating": round(record.rating, 1),
                        "visit_duration": record.visit_duration,
                        "longitude": record.longitude,
                        "latitude": record.latitude,
                        "address": record.address,
                        "cover_image": record.image_url,
                    }
                    for record in day_records
                ],
            }
        )

    return {
        "city": city,
        "days": day_count,
        "preference": preference,
        "budget": round(budget, 2),
        "routes": day_routes,
        "summary": {
            "spots_count": sum(len(route["spots"]) for route in day_routes),
            "total_distance_km": round(sum(route["distance_km"] for route in day_routes), 2),
            "total_cost": round(sum(route["estimated_cost"] for route in day_routes), 2),
            "total_hours": round(sum(route["estimated_hours"] for route in day_routes), 1),
        },
        "algorithm": {
            "recommendation": "semantic vector hybrid recommendation",
            "classification": "TF-IDF + Multinomial Naive Bayes",
            "route_optimizer": "Ant Colony Optimization",
            "iterations": 60,
            "ants": 24,
        },
    }
