from __future__ import annotations

from difflib import SequenceMatcher
import re
from copy import deepcopy
from math import isfinite
from typing import Any


MEDIA_ENTITY_TYPES = {"movie", "series"}
MUSIC_ENTITY_TYPE = "music"
RESTAURANT_ENTITY_TYPE = "restaurant"

MEDIA_GENRES = [
    "action",
    "adventure",
    "animation",
    "biography",
    "comedy",
    "crime",
    "documentary",
    "drama",
    "family",
    "fantasy",
    "history",
    "horror",
    "music",
    "musical",
    "mystery",
    "romance",
    "sci_fi",
    "sport",
    "thriller",
    "war",
    "western",
]

MUSIC_GENRES = [
    "ambient",
    "blues",
    "classical",
    "country",
    "dance",
    "electronic",
    "experimental",
    "folk",
    "funk",
    "hip_hop",
    "jazz",
    "latin",
    "metal",
    "pop",
    "punk",
    "r_and_b",
    "reggae",
    "rock",
    "soul",
    "soundtrack",
    "world",
]

RESTAURANT_GENRES = [
    "american",
    "barbecue",
    "british",
    "chinese",
    "cocktail_bar_drinks",
    "eastern_european",
    "french",
    "greek",
    "indian",
    "italian",
    "japanese",
    "korean",
    "latin_american",
    "mediterranean",
    "mexican",
    "middle_eastern",
    "modern_european",
    "seafood",
    "south_east_asian",
    "spanish",
    "thai",
    "vegetarian_vegan",
    "vietnamese",
    "other",
]

MICHELIN_STATUSES = [
    "unknown",
    "selected",
    "bib_gourmand",
    "one_star",
    "two_stars",
    "three_stars",
    "not_listed",
]

MEDIA_GENRE_ALIASES = {
    "children": "family",
    "kids": "family",
    "science_fiction": "sci_fi",
    "sci_fi": "sci_fi",
    "sci_fy": "sci_fi",
    "superhero": "action",
    "sports": "sport",
    "film_noir": "crime",
    "noir": "crime",
    "rom_com": "comedy",
    "romcom": "comedy",
    "tv_movie": "drama",
}

MUSIC_GENRE_ALIASES = {
    "bebop": "jazz",
    "classical_music": "classical",
    "edm": "electronic",
    "electronica": "electronic",
    "hard_bop": "jazz",
    "hip_hop": "hip_hop",
    "hiphop": "hip_hop",
    "modal_jazz": "jazz",
    "rap": "hip_hop",
    "r_b": "r_and_b",
    "rhythm_and_blues": "r_and_b",
    "singer_songwriter": "folk",
    "soundtracks": "soundtrack",
    "world_music": "world",
}

RESTAURANT_GENRE_ALIASES = {
    "asian_fusion": "south_east_asian",
    "bbq": "barbecue",
    "bistro": "french",
    "british": "british",
    "cantonese": "chinese",
    "central_european": "eastern_european",
    "cocktail": "cocktail_bar_drinks",
    "cocktail_bar": "cocktail_bar_drinks",
    "cocktail_bars": "cocktail_bar_drinks",
    "cocktail_lounge": "cocktail_bar_drinks",
    "cocktails": "cocktail_bar_drinks",
    "deli": "american",
    "dim_sum": "chinese",
    "drinks": "cocktail_bar_drinks",
    "drinks_bar": "cocktail_bar_drinks",
    "eastern_european": "eastern_european",
    "european": "modern_european",
    "filipino": "south_east_asian",
    "gastropub": "british",
    "georgian": "eastern_european",
    "greek": "greek",
    "indian": "indian",
    "indonesian": "south_east_asian",
    "italia": "italian",
    "italian": "italian",
    "japanese": "japanese",
    "korean": "korean",
    "latin": "latin_american",
    "latin_american": "latin_american",
    "lebanese": "middle_eastern",
    "malaysian": "south_east_asian",
    "mediterranean": "mediterranean",
    "mexican": "mexican",
    "middle_eastern": "middle_eastern",
    "modern_european": "modern_european",
    "new_american": "american",
    "peruvian": "latin_american",
    "pizzeria": "italian",
    "portuguese": "spanish",
    "seafood": "seafood",
    "singaporean": "south_east_asian",
    "spanish": "spanish",
    "sushi": "japanese",
    "thai": "thai",
    "trattoria": "italian",
    "turkish": "middle_eastern",
    "vegan": "vegetarian_vegan",
    "vegetarian": "vegetarian_vegan",
    "vietnamese": "vietnamese",
    "wine_bar": "cocktail_bar_drinks",
}

MICHELIN_STATUS_ALIASES = {
    "recommended": "selected",
    "selected_restaurant": "selected",
    "selected_restaurants": "selected",
    "michelin_selected": "selected",
    "michelin_plate": "selected",
    "plate": "selected",
    "bib": "bib_gourmand",
    "bib_gourmand": "bib_gourmand",
    "bib_gourmands": "bib_gourmand",
    "one_michelin_star": "one_star",
    "one_star": "one_star",
    "1_star": "one_star",
    "1_stars": "one_star",
    "1_michelin_star": "one_star",
    "two_michelin_stars": "two_stars",
    "two_star": "two_stars",
    "two_stars": "two_stars",
    "2_star": "two_stars",
    "2_stars": "two_stars",
    "2_michelin_stars": "two_stars",
    "three_michelin_stars": "three_stars",
    "three_star": "three_stars",
    "three_stars": "three_stars",
    "3_star": "three_stars",
    "3_stars": "three_stars",
    "3_michelin_stars": "three_stars",
    "not_in_guide": "not_listed",
    "not_listed": "not_listed",
    "not_michelin_listed": "not_listed",
    "no_michelin_listing": "not_listed",
    "none": "not_listed",
}

MEDIA_METADATA_PATHS: tuple[tuple[str, ...], ...] = (
    ("synopsis",),
    ("main_actors",),
    ("director",),
    ("country",),
    ("language",),
    ("genre",),
    ("runtime",),
    ("seasons",),
    ("watched",),
    ("watched_at",),
    ("external_ids", "imdb_id"),
    ("external_ratings", "imdb", "rating"),
    ("external_ratings", "imdb", "votes"),
    ("external_ratings", "rotten_tomatoes", "critic_score"),
    ("ratings_source", "provider"),
    ("ratings_source", "fetched_at"),
)

MUSIC_METADATA_PATHS: tuple[tuple[str, ...], ...] = (
    ("artist",),
    ("album",),
    ("personnel",),
    ("genre",),
)

RESTAURANT_METADATA_PATHS: tuple[tuple[str, ...], ...] = (
    ("cuisine",),
    ("michelin",),
    ("google",),
)


def is_media_type(entity_type: str | None) -> bool:
    return entity_type in MEDIA_ENTITY_TYPES


def is_music_type(entity_type: str | None) -> bool:
    return entity_type == MUSIC_ENTITY_TYPE


def is_restaurant_type(entity_type: str | None) -> bool:
    return entity_type == RESTAURANT_ENTITY_TYPE


def empty_media_metadata() -> dict[str, Any]:
    return {
        "synopsis": None,
        "main_actors": [],
        "director": None,
        "country": [],
        "language": [],
        "genre": [],
        "runtime": None,
        "seasons": None,
        "watched": False,
        "watched_at": None,
        "external_ids": {"imdb_id": None},
        "external_ratings": {
            "imdb": {"rating": None, "votes": None},
            "rotten_tomatoes": {"critic_score": None},
        },
        "ratings_source": {"provider": None, "fetched_at": None},
    }


def empty_music_metadata() -> dict[str, Any]:
    return {
        "artist": None,
        "album": None,
        "personnel": [],
        "genre": [],
    }


def empty_restaurant_metadata() -> dict[str, Any]:
    return {"cuisine": {}}


def normalize_media_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    result = empty_media_metadata()
    if not isinstance(metadata, dict):
        return result

    for path in MEDIA_METADATA_PATHS:
        raw = get_path(metadata, path)
        if raw is None:
            continue
        set_path(result, path, normalize_media_value(path, raw))

    return result


def normalize_music_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    result = empty_music_metadata()
    if not isinstance(metadata, dict):
        return result

    for path in MUSIC_METADATA_PATHS:
        raw = get_path(metadata, path)
        if raw is None:
            continue
        set_path(result, path, normalize_music_value(path, raw))

    return result


def normalize_restaurant_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    result = empty_restaurant_metadata()
    if not isinstance(metadata, dict):
        return result

    raw = metadata.get("cuisine")
    if raw is not None:
        result["cuisine"] = normalize_restaurant_cuisine(raw)
    elif metadata.get("genre") is not None:
        raw = metadata.get("genre")
        result["cuisine"] = normalize_restaurant_cuisine(raw)

    raw_michelin = metadata.get("michelin")
    if raw_michelin is None and metadata.get("michelin_status") is not None:
        raw_michelin = {"status": metadata.get("michelin_status")}
    if raw_michelin is not None:
        result["michelin"] = normalize_michelin_status(raw_michelin)

    raw_google = metadata.get("google")
    if raw_google is None and (
        metadata.get("google_rating") is not None
        or metadata.get("google_rating_count") is not None
    ):
        raw_google = {
            "rating": metadata.get("google_rating"),
            "rating_count": metadata.get("google_rating_count"),
            "source_url": metadata.get("google_url"),
        }
    if raw_google is not None:
        result["google"] = normalize_google_rating_metadata(raw_google)

    return result


def set_media_field(
    metadata: dict[str, Any],
    path: tuple[str, ...],
    value: Any,
) -> dict[str, Any]:
    result = normalize_media_metadata(metadata)
    set_path(result, path, normalize_media_value(path, value))
    return result


def set_music_field(
    metadata: dict[str, Any],
    path: tuple[str, ...],
    value: Any,
) -> dict[str, Any]:
    result = normalize_music_metadata(metadata)
    set_path(result, path, normalize_music_value(path, value))
    return result


def set_restaurant_field(
    metadata: dict[str, Any],
    path: tuple[str, ...],
    value: Any,
) -> dict[str, Any]:
    result = normalize_restaurant_metadata(metadata)
    if path in {("cuisine",), ("genre",)}:
        set_path(result, ("cuisine",), normalize_restaurant_cuisine(value))
    if path == ("michelin",):
        set_path(result, ("michelin",), normalize_michelin_status(value))
    if path == ("google",):
        set_path(result, ("google",), normalize_google_rating_metadata(value))
    return result


def merge_media_metadata(
    base: dict[str, Any] | None,
    incoming: dict[str, Any] | None,
    *,
    overwrite: bool = False,
    protected_paths: set[tuple[str, ...]] | None = None,
) -> dict[str, Any]:
    result = normalize_media_metadata(base)
    source = normalize_media_metadata(incoming)
    protected_paths = protected_paths or set()

    for path in MEDIA_METADATA_PATHS:
        if path in protected_paths:
            continue
        value = get_path(source, path)
        if is_empty_metadata_value(value):
            continue
        current = get_path(result, path)
        if overwrite or is_empty_metadata_value(current):
            set_path(result, path, value)

    return result


def merge_music_metadata(
    base: dict[str, Any] | None,
    incoming: dict[str, Any] | None,
    *,
    overwrite: bool = False,
    protected_paths: set[tuple[str, ...]] | None = None,
) -> dict[str, Any]:
    result = normalize_music_metadata(base)
    source = normalize_music_metadata(incoming)
    protected_paths = protected_paths or set()

    for path in MUSIC_METADATA_PATHS:
        if path in protected_paths:
            continue
        value = get_path(source, path)
        if is_empty_metadata_value(value):
            continue
        current = get_path(result, path)
        if overwrite or is_empty_metadata_value(current):
            set_path(result, path, value)

    return result


def merge_restaurant_metadata(
    base: dict[str, Any] | None,
    incoming: dict[str, Any] | None,
    *,
    overwrite: bool = False,
    protected_paths: set[tuple[str, ...]] | None = None,
) -> dict[str, Any]:
    result = normalize_restaurant_metadata(base)
    source = normalize_restaurant_metadata(incoming)
    protected_paths = protected_paths or set()

    for path in RESTAURANT_METADATA_PATHS:
        if path in protected_paths:
            continue
        value = get_path(source, path)
        if is_empty_metadata_value(value):
            continue
        current = get_path(result, path)
        if overwrite or is_empty_metadata_value(current):
            set_path(result, path, value)

    return result


def external_rating_tiebreak(metadata: dict[str, Any] | None) -> float:
    normalized = normalize_media_metadata(metadata)
    scores = []

    imdb_rating = get_path(normalized, ("external_ratings", "imdb", "rating"))
    if imdb_rating is not None:
        scores.append(float(imdb_rating) / 10)

    rt_score = get_path(
        normalized,
        ("external_ratings", "rotten_tomatoes", "critic_score"),
    )
    if rt_score is not None:
        scores.append(float(rt_score) / 100)

    if not scores:
        return 0.0
    return round((sum(scores) / len(scores)) * 0.05, 3)


def external_rating_facts(metadata: dict[str, Any] | None) -> list[str]:
    normalized = normalize_media_metadata(metadata)
    facts = []

    imdb_rating = get_path(normalized, ("external_ratings", "imdb", "rating"))
    imdb_votes = get_path(normalized, ("external_ratings", "imdb", "votes"))
    if imdb_rating is not None:
        suffix = f", {imdb_votes:,} votes" if imdb_votes is not None else ""
        facts.append(f"IMDb {float(imdb_rating):g}/10{suffix}")

    rt_score = get_path(
        normalized,
        ("external_ratings", "rotten_tomatoes", "critic_score"),
    )
    if rt_score is not None:
        facts.append(f"Rotten Tomatoes critic {int(rt_score)}%")

    return facts


def metadata_search_text(metadata: dict[str, Any] | None) -> str:
    normalized = normalize_media_metadata(metadata)
    music = normalize_music_metadata(metadata)
    restaurant = normalize_restaurant_metadata(metadata)
    parts: list[str] = []

    for key in ["synopsis", "director", "watched_at"]:
        value = normalized.get(key)
        if value:
            parts.append(str(value))

    parts.extend(normalized["main_actors"])
    parts.extend(normalized["country"])
    parts.extend(normalized["language"])
    parts.extend(normalized["genre"])
    if normalized["runtime"]:
        parts.extend(["runtime", f"{normalized['runtime']} min"])
    if normalized["seasons"]:
        parts.extend(["seasons", str(normalized["seasons"])])

    imdb_id = normalized["external_ids"].get("imdb_id")
    if imdb_id:
        parts.extend(["imdb", imdb_id])

    if normalized["watched"]:
        parts.append("watched")

    for fact in external_rating_facts(normalized):
        parts.append(fact)

    for key in ["artist", "album"]:
        value = music.get(key)
        if value:
            parts.append(str(value))

    parts.extend(music["personnel"])
    parts.extend(music["genre"])
    parts.extend(restaurant_cuisine_search_terms(restaurant))
    parts.extend(restaurant_michelin_search_terms(restaurant))
    parts.extend(restaurant_google_search_terms(restaurant))

    return " ".join(parts)


def get_path(mapping: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = mapping
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def set_path(mapping: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    current = mapping
    for key in path[:-1]:
        nested = current.get(key)
        if not isinstance(nested, dict):
            nested = {}
            current[key] = nested
        current = nested
    current[path[-1]] = deepcopy(value)


def normalize_media_value(path: tuple[str, ...], value: Any) -> Any:
    if path == ("main_actors",):
        return normalize_string_list(value)
    if path == ("country",):
        return normalize_string_list(value)
    if path == ("language",):
        return normalize_string_list(value)
    if path == ("genre",):
        return normalize_genres(value, allowed=MEDIA_GENRES, aliases=MEDIA_GENRE_ALIASES)
    if path == ("runtime",):
        return normalize_runtime(value)
    if path == ("seasons",):
        return normalize_int(value)

    if path == ("watched",):
        return normalize_bool(value)

    if path == ("external_ratings", "imdb", "rating"):
        return normalize_float(value)

    if path in {
        ("external_ratings", "imdb", "votes"),
        ("external_ratings", "rotten_tomatoes", "critic_score"),
    }:
        return normalize_int(value)

    return normalize_string(value)


def normalize_music_value(path: tuple[str, ...], value: Any) -> Any:
    if path == ("personnel",):
        return normalize_string_list(value)
    if path == ("genre",):
        return normalize_genres(value, allowed=MUSIC_GENRES, aliases=MUSIC_GENRE_ALIASES)
    return normalize_string(value)


def normalize_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.upper() == "N/A":
        return None
    return text


def normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = re.split(r"[,;]+", value)
    elif isinstance(value, list):
        values = value
    else:
        values = [value]
    return [text for item in values if (text := normalize_string(item))]


def normalize_genres(
    value: Any,
    *,
    allowed: list[str],
    aliases: dict[str, str],
) -> list[str]:
    allowed_set = set(allowed)
    result = []
    for item in normalize_string_list(value):
        key = normalize_genre_key(item)
        canonical = aliases.get(key, key)
        if canonical not in allowed_set or canonical in result:
            continue
        result.append(canonical)
    return result


def normalize_restaurant_genres(value: Any) -> list[str]:
    result = []
    for item in normalize_string_list(value):
        canonical = restaurant_genre_match(item)
        if canonical and canonical not in result:
            result.append(canonical)
    return result


def normalize_restaurant_cuisine(value: Any) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}

    if isinstance(value, dict):
        if isinstance(value.get("cuisine"), dict) or value.get("genre") is not None:
            value = value.get("cuisine", value.get("genre"))
        if isinstance(value, dict):
            for raw_key, raw_value in value.items():
                cuisine = restaurant_genre_match(raw_key)
                if not cuisine:
                    continue
                detail = normalize_cuisine_detail(raw_value)
                if detail["value"] <= 0:
                    continue
                existing = result.get(cuisine)
                if existing is None or detail["value"] > existing["value"]:
                    result[cuisine] = detail
            return prune_other_cuisine(result)

    for cuisine in normalize_restaurant_genres(value):
        result[cuisine] = {
            "value": 1.0,
            "interval_95": {"lower": 1.0, "upper": 1.0},
        }

    return prune_other_cuisine(result)


def normalize_cuisine_detail(value: Any) -> dict[str, Any]:
    point = cuisine_point_value(value)
    if isinstance(value, dict):
        interval = value.get("interval_95")
        if interval is None and ("lower_95" in value or "upper_95" in value):
            interval = {"lower": value.get("lower_95"), "upper": value.get("upper_95")}
    else:
        interval = None
    return {
        "value": point,
        "interval_95": normalize_cuisine_interval(point, interval),
    }


def cuisine_point_value(value: Any) -> float:
    if isinstance(value, dict):
        value = value.get("value", 0)
    try:
        return clamp_cuisine01(value)
    except (TypeError, ValueError):
        return 0.0


def normalize_cuisine_interval(
    value: float,
    interval: dict[str, Any] | None,
) -> dict[str, float]:
    if not isinstance(interval, dict):
        return {"lower": value, "upper": value}
    try:
        lower = clamp_cuisine01(interval.get("lower", interval.get("lower_95", value)))
        upper = clamp_cuisine01(interval.get("upper", interval.get("upper_95", value)))
    except (TypeError, ValueError):
        return {"lower": value, "upper": value}
    if lower > upper:
        lower, upper = upper, lower
    return {"lower": min(lower, value), "upper": max(upper, value)}


def clamp_cuisine01(value: Any) -> float:
    return max(0.0, min(1.0, float(value)))


def prune_other_cuisine(cuisine: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if len(cuisine) > 1 and "other" in cuisine:
        cuisine = dict(cuisine)
        cuisine.pop("other", None)
    return cuisine


def normalize_michelin_status(value: Any) -> dict[str, Any]:
    result = {
        "status": "unknown",
        "stars": None,
        "green_star": False,
        "source_url": None,
        "source": None,
        "checked_at": None,
    }
    if isinstance(value, str):
        result["status"] = michelin_status_match(value)
        result["stars"] = michelin_stars_from_status(result["status"])
        return result
    if not isinstance(value, dict):
        return result

    status = michelin_status_match(
        value.get("status")
        or value.get("distinction")
        or value.get("award")
        or value.get("michelin_status")
    )
    stars = normalize_michelin_stars(value.get("stars", value.get("star_count")))
    if stars is None:
        stars = michelin_stars_from_status(status)
    if stars is not None and stars > 0:
        status = michelin_status_from_stars(stars)

    result["status"] = status
    result["stars"] = stars
    result["green_star"] = normalize_bool(
        value.get("green_star", value.get("michelin_green_star", False))
    )
    result["source_url"] = normalize_string(
        value.get("source_url") or value.get("url") or value.get("michelin_url")
    )
    result["source"] = normalize_string(value.get("source"))
    result["checked_at"] = normalize_string(value.get("checked_at"))
    if result["source"] is None and is_official_michelin_url(result["source_url"]):
        result["source"] = "guide.michelin.com"
    return result


def michelin_status_match(value: Any) -> str:
    key = normalize_genre_key(value)
    if not key:
        return "unknown"
    if key in MICHELIN_STATUS_ALIASES:
        return MICHELIN_STATUS_ALIASES[key]
    if key in MICHELIN_STATUSES:
        return key
    return "unknown"


def normalize_michelin_stars(value: Any) -> int | None:
    if value is None:
        return None
    try:
        stars = int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        status = michelin_status_match(value)
        return michelin_stars_from_status(status)
    return max(0, min(3, stars))


def michelin_stars_from_status(status: str) -> int | None:
    return {
        "one_star": 1,
        "two_stars": 2,
        "three_stars": 3,
        "selected": 0,
        "bib_gourmand": 0,
        "not_listed": 0,
    }.get(status)


def michelin_status_from_stars(stars: int) -> str:
    return {
        1: "one_star",
        2: "two_stars",
        3: "three_stars",
    }.get(stars, "selected")


def is_official_michelin_url(value: Any) -> bool:
    text = str(value or "").lower()
    return "guide.michelin.com" in text


def restaurant_michelin_search_terms(metadata: dict[str, Any] | None) -> list[str]:
    michelin = normalize_restaurant_metadata(metadata).get("michelin") or {}
    status = michelin.get("status")
    if not status or status == "unknown":
        return []
    terms = ["michelin", status.replace("_", " ")]
    stars = michelin.get("stars")
    if stars:
        terms.extend([f"{stars} michelin star", f"{stars} star"])
    if michelin.get("green_star"):
        terms.append("michelin green star")
    return terms


def normalize_google_rating_metadata(value: Any) -> dict[str, Any]:
    result = {
        "rating": None,
        "rating_count": None,
        "source_url": None,
        "source": None,
        "checked_at": None,
    }
    if isinstance(value, (int, float, str)):
        result["rating"] = normalize_google_rating(value)
        return result
    if not isinstance(value, dict):
        return result

    result["rating"] = normalize_google_rating(
        value.get("rating", value.get("google_rating"))
    )
    result["rating_count"] = normalize_nonnegative_int(
        value.get(
            "rating_count",
            value.get("userRatingCount", value.get("user_ratings_total")),
        )
    )
    result["source_url"] = normalize_string(
        value.get("source_url") or value.get("url") or value.get("google_url")
    )
    result["source"] = normalize_string(value.get("source"))
    result["checked_at"] = normalize_string(value.get("checked_at"))
    if result["source"] is None and is_official_google_rating_url(
        result["source_url"]
    ):
        result["source"] = "google"
    return result


def normalize_google_rating(value: Any) -> float | None:
    rating = normalize_float(value)
    if rating is None:
        return None
    return round(max(0.0, min(5.0, rating)), 1)


def normalize_nonnegative_int(value: Any) -> int | None:
    result = normalize_int(value)
    if result is None:
        return None
    return max(0, result)


def is_official_google_rating_url(value: Any) -> bool:
    text = str(value or "").lower()
    return (
        "google.com/maps" in text
        or "maps.google." in text
        or "maps.app.goo.gl" in text
    )


def restaurant_google_search_terms(metadata: dict[str, Any] | None) -> list[str]:
    google = normalize_restaurant_metadata(metadata).get("google") or {}
    rating = google.get("rating")
    if rating is None:
        return []
    terms = ["google", f"google rating {float(rating):g}"]
    rating_count = google.get("rating_count")
    if rating_count is not None:
        terms.append(f"{int(rating_count)} google ratings")
    return terms


def restaurant_cuisine_search_terms(
    metadata: dict[str, Any] | None,
    *,
    threshold: float = 0.4,
) -> list[str]:
    cuisine = normalize_restaurant_metadata(metadata).get("cuisine") or {}
    return [
        key
        for key, detail in cuisine.items()
        if cuisine_point_value(detail) >= threshold
    ]


def restaurant_genre_match(value: Any, *, threshold: float = 0.4) -> str:
    key = normalize_genre_key(value)
    if not key:
        return "other"
    if key in RESTAURANT_GENRE_ALIASES:
        return RESTAURANT_GENRE_ALIASES[key]
    if key in RESTAURANT_GENRES:
        return key

    best = max(
        RESTAURANT_GENRES,
        key=lambda genre: genre_similarity(key, genre),
    )
    confidence = genre_similarity(key, best)
    return best if confidence >= threshold else "other"


def genre_similarity(left: str, right: str) -> float:
    if left == right:
        return 1.0
    left_tokens = set(left.split("_"))
    right_tokens = set(right.split("_"))
    overlap = len(left_tokens & right_tokens)
    token_score = overlap / max(len(left_tokens), len(right_tokens))
    if token_score > 0:
        return max(token_score, SequenceMatcher(None, left, right).ratio())
    sequence_score = SequenceMatcher(None, left, right).ratio()
    if left[0] == right[0] and sequence_score >= 0.75:
        return sequence_score
    return 0.0


def normalize_genre_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")


def normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "watched"}
    return bool(value)


def normalize_float(value: Any) -> float | None:
    try:
        result = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    if not isfinite(result):
        return None
    return result


def normalize_int(value: Any) -> int | None:
    try:
        result = int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return None
    return result


def normalize_runtime(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    match = re.search(r"\d+", str(value).replace(",", ""))
    if not match:
        return None
    return int(match.group(0))


def is_empty_metadata_value(value: Any) -> bool:
    if isinstance(value, dict) and set(value).issubset(
        {"status", "stars", "green_star", "source_url", "source", "checked_at"}
    ):
        return (
            value.get("status") in {None, "", "unknown"}
            and value.get("stars") is None
            and not value.get("green_star")
            and not value.get("source_url")
            and not value.get("source")
            and not value.get("checked_at")
        )
    if isinstance(value, dict) and set(value).issubset(
        {"rating", "rating_count", "source_url", "source", "checked_at"}
    ):
        return (
            value.get("rating") is None
            and value.get("rating_count") is None
            and not value.get("source_url")
            and not value.get("source")
            and not value.get("checked_at")
        )
    return value is None or value is False or value == "" or value == [] or value == {}
