ENTITY_TYPES = [
    "wine",
    "restaurant",
    "music",
    "cigar",
    "experience",
    "movie",
    "series",
]

ATTRIBUTE_KEYS_BY_TYPE = {
    "wine": [
        "premium",
        "classic",
        "body",
        "tannin",
        "acidity",
        "oak",
        "fruity",
        "floral",
        "spicy",
        "vegetative",
        "nutty",
        "caramelized",
        "woody",
        "earthy",
        "chemical",
        "pungent",
        "oxidized",
        "microbiological",
    ],
    "restaurant": [
        "premium",
        "quiet",
        "lively",
        "indulgent",
        "novelty",
        "comfort",
        "view",
        "outdoor_space",
        "smoking",
        "classic",
        "casual",
    ],
    "music": [
        "quiet",
        "lively",
        "intellectual",
        "comfort",
        "classic",
        "novelty",
        "intensity",
        "indulgent",
    ],
    "cigar": [
        "premium",
        "richness",
        "intensity",
        "classic",
        "indulgent",
        "novelty",
        "comfort",
    ],
    "experience": [
        "premium",
        "intensity",
        "quiet",
        "lively",
        "intellectual",
        "indulgent",
        "novelty",
        "comfort",
        "view",
        "classic",
        "casual",
    ],
    "movie": [
        "intense",
        "suspenseful",
        "cerebral",
        "emotional",
        "funny",
        "dark",
        "light",
        "slow_burn",
        "action",
        "comfort",
        "novelty",
        "classic",
    ],
    "series": [
        "intense",
        "suspenseful",
        "cerebral",
        "emotional",
        "funny",
        "dark",
        "light",
        "slow_burn",
        "serialized",
        "comfort",
        "novelty",
        "classic",
    ],
}

ATTRIBUTE_KEYS = list(
    dict.fromkeys(
        key
        for entity_type in ENTITY_TYPES
        for key in ATTRIBUTE_KEYS_BY_TYPE[entity_type]
    )
)

INTENTS = [
    "contextual_decision",
    "option_set_evaluation",
    "memory_recall",
    "attribute_retrieval",
    "passive_recall",
    "social_context",
    "negative_filtering",
    "hybrid_query",
    "fuzzy_recall",
    "exploration",
]

SIGNAL_TYPES = [
    "rating",
    "tried",
    "watched",
    "listened",
    "wanted_to_try",
    "wanted_to_watch",
    "wanted_to_listen",
    "recommended_by",
    "disliked",
    "avoid",
    "not_my_style",
    "bad_fit",
    "rejected_option",
]


def attribute_keys_for_type(entity_type: str | None) -> list[str]:
    return ATTRIBUTE_KEYS_BY_TYPE.get(entity_type or "", ATTRIBUTE_KEYS)


def invalid_attribute_keys(
    entity_type: str,
    attributes: dict[str, object] | None,
) -> list[str]:
    allowed = set(attribute_keys_for_type(entity_type))
    return sorted(key for key in (attributes or {}) if key not in allowed)
