#!/usr/bin/env python3

import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any


CATEGORY_DIRS = {
    "animals": "animals",
    "buildings": "buildings",
    "enemies": "enemies",
    "furniture": "furniture",
    "gardenItems": "garden-items",
    "locations": "locations",
    "maps": "maps",
    "medals": "medals",
    "plants": "plants",
    "quests": "quests",
    "recipes": "recipes",
    "supplies": "supplies",
}


# Вложенные объекты используют разные идентификаторы.
#
# Формат правила:
# category:
#   (
#       parent label,
#       nested field,
#       child label,
#       identifier field,
#   )
NESTED_ID_RULES = {
    "buildings": (
        (
            "Building",
            "rooms",
            "room",
            "templateId",
        ),
        (
            "Building",
            "gardens",
            "garden",
            "templateId",
        ),
    ),
    "locations": (
        (
            "Location",
            "scenes",
            "scene",
            "templateId",
        ),
    ),
    "maps": (
        (
            "Map",
            "locationSlots",
            "location slot",
            "slotId",
        ),
        (
            "Map",
            "enemySlots",
            "enemy slot",
            "slotId",
        ),
    ),
}

LOOT_POOL_CATEGORIES = {
    "buildingLoot": "buildings",
    "mapLoot": "maps",
    "gardenItemLoot": "gardenItems",
    "plantLoot": "plants",
    "furnitureLoot": "furniture",
    "recipeLoot": "recipes",
    "locationLoot": "locations",
}

ACQUISITION_SOURCE_CATEGORIES = {
    "buildings",
    "furniture",
    "gardenItems",
    "locations",
    "maps",
    "plants",
    "recipes",
}

LOCATION_TYPES = {
    "PARK",
    "MONUMENT",
    "LANDMARK",
    "PAVILION",
    "CAVE",
    "FOUNTAIN",
    "RESORT",
    "WATERFALL",
    "RUINS",
    "WATER_ANOMALY",
}

LOCATION_SLOT_MODES = {
    "FIXED",
    "RANDOM",
}

POUCH = "POUCH"
SHOP = "SHOP"
QUEST_REWARD = "QUEST_REWARD"
EXPEDITION_REWARD = "EXPEDITION_REWARD"

ACQUISITION_SOURCES = {
    POUCH,
    SHOP,
    QUEST_REWARD,
    EXPEDITION_REWARD,
}

class CatalogValidationError(Exception):
    pass

def validate_acquisition_sources(
        catalog: dict[str, list[dict[str, Any]]],
) -> None:
    for category_name, items in catalog.items():
        for item in items:
            template_id = item["templateId"]

            if (
                    "allowedAcquisitionSources" in item
                    and category_name
                    not in ACQUISITION_SOURCE_CATEGORIES
            ):
                raise CatalogValidationError(
                    f"{category_name} '{template_id}': "
                    f"allowedAcquisitionSources is not allowed "
                    f"for this category"
                )

            sources = item.get(
                "allowedAcquisitionSources"
            )

            if sources is None:
                continue

            if not isinstance(sources, list):
                raise CatalogValidationError(
                    f"{category_name} '{template_id}': "
                    f"allowedAcquisitionSources must "
                    f"be an array or null"
                )

            seen_sources: set[str] = set()

            for index, source in enumerate(sources):
                source = require_non_blank_string(
                    f"{category_name} '{template_id}'",
                    f"allowedAcquisitionSources[{index}]",
                    source,
                )

                if source not in ACQUISITION_SOURCES:
                    raise CatalogValidationError(
                        f"{category_name} "
                        f"'{template_id}': unknown "
                        f"acquisition source "
                        f"'{source}' at index {index}"
                    )

                if source in seen_sources:
                    raise CatalogValidationError(
                        f"{category_name} "
                        f"'{template_id}': duplicate "
                        f"acquisition source '{source}'"
                    )

                seen_sources.add(source)

def require_object_list(
    source: str,
    field_name: str,
    value: Any,
) -> list[dict[str, Any]]:
    """
    Возвращает массив объектов.

    Отсутствующее поле и null трактуются как пустой массив.
    Любое другое значение считается ошибкой схемы.
    """
    if value is None:
        return []

    if not isinstance(value, list):
        raise CatalogValidationError(
            f"{source}: field '{field_name}' must be an array"
        )

    result: list[dict[str, Any]] = []

    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise CatalogValidationError(
                f"{source}: field '{field_name}' item "
                f"at index {index} must be an object"
            )

        result.append(item)

    return result


def require_non_blank_string(
    source: str,
    field_name: str,
    value: Any,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CatalogValidationError(
            f"{source}: missing or invalid {field_name}"
        )

    return value

def require_coordinate(
    source: str,
    field_name: str,
    value: Any,
) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not 0 <= value <= 1
    ):
        raise CatalogValidationError(
            f"{source}: {field_name} must be "
            f"a number between 0 and 1"
        )

    return float(value)

def require_positive_integer(
    source: str,
    field_name: str,
    value: Any,
) -> int:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 1
    ):
        raise CatalogValidationError(
            f"{source}: {field_name} must be "
            f"a positive integer"
        )

    return value

def load_category(
    root: Path,
    directory_name: str,
) -> list[dict[str, Any]]:
    directory = root / directory_name

    if not directory.exists():
        return []

    result: list[dict[str, Any]] = []

    for path in sorted(directory.rglob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as file:
                value = json.load(file)
        except json.JSONDecodeError as exc:
            raise CatalogValidationError(
                f"Invalid JSON in {path}: {exc}"
            ) from exc

        if not isinstance(value, dict):
            raise CatalogValidationError(
                f"{path}: root JSON value must be an object"
            )

        require_non_blank_string(
            str(path),
            "templateId",
            value.get("templateId"),
        )

        result.append(value)

    return result


def index_by_template_id(
    category_name: str,
    items: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}

    for item in items:
        template_id = item["templateId"]

        if template_id in result:
            raise CatalogValidationError(
                f"Duplicate templateId '{template_id}' "
                f"in category '{category_name}'"
            )

        result[template_id] = item

    return result


def require_reference(
    source: str,
    reference: Any,
    target_name: str,
    target_ids: set[str],
) -> None:
    if reference is None:
        return

    reference_id = require_non_blank_string(
        source,
        f"{target_name} templateId reference",
        reference,
    )

    if reference_id not in target_ids:
        raise CatalogValidationError(
            f"{source}: references unknown {target_name} "
            f"templateId '{reference_id}'"
        )

def require_required_reference(
    source: str,
    reference: Any,
    target_name: str,
    target_ids: set[str],
) -> None:
    reference_id = require_non_blank_string(
        source,
        f"{target_name} templateId reference",
        reference,
    )

    if reference_id not in target_ids:
        raise CatalogValidationError(
            f"{source}: references unknown "
            f"{target_name} templateId "
            f"'{reference_id}'"
        )

def validate_unique_nested_ids(
    parent_source: str,
    field_name: str,
    child_label: str,
    id_field: str,
    children: list[dict[str, Any]],
) -> None:
    """
    Проверяет наличие и уникальность идентификатора
    вложенной сущности в пределах её родителя.

    Например:

    building + rooms + templateId
    map + locationSlots + slotId
    map + enemySlots + slotId
    """
    seen: set[str] = set()

    for index, child in enumerate(children):
        child_source = (
            f"{parent_source}, {child_label} at index {index}"
        )

        child_id = require_non_blank_string(
            child_source,
            id_field,
            child.get(id_field),
        )

        if child_id in seen:
            raise CatalogValidationError(
                f"{parent_source}: duplicate {child_label} "
                f"{id_field} '{child_id}' "
                f"in field '{field_name}'"
            )

        seen.add(child_id)


def validate_nested_identifiers(
    catalog: dict[str, list[dict[str, Any]]],
) -> None:
    """
    Применяет правила из NESTED_ID_RULES.

    Здесь намеренно нет общего требования templateId
    для любого объекта, находящегося внутри массива.
    """
    for category, rules in NESTED_ID_RULES.items():
        for item in catalog[category]:
            parent_id = item["templateId"]

            for (
                parent_label,
                field_name,
                child_label,
                id_field,
            ) in rules:
                parent_source = (
                    f"{parent_label} '{parent_id}'"
                )

                children = require_object_list(
                    parent_source,
                    field_name,
                    item.get(field_name),
                )

                validate_unique_nested_ids(
                    parent_source=parent_source,
                    field_name=field_name,
                    child_label=child_label,
                    id_field=id_field,
                    children=children,
                )


def validate_image_reference(
    source: str,
    value: dict[str, Any],
    require_image_key: bool,
) -> None:
    """
    Проверяет один объект, в котором найдено одно из полей:
    imageKey, sourceImageUrl или устаревшее imageUrl.

    В develop разрешено ровно одно из:
    - imageKey;
    - sourceImageUrl.

    В строгом релизном режиме разрешён только imageKey.
    """
    if "imageUrl" in value:
        raise CatalogValidationError(
            f"{source}: field 'imageUrl' is not allowed in catalog; "
            f"use 'sourceImageUrl' for a temporary contributor URL "
            f"or 'imageKey' for the final S3 object"
        )

    has_image_key_field = "imageKey" in value
    has_source_url_field = "sourceImageUrl" in value

    if has_image_key_field and has_source_url_field:
        raise CatalogValidationError(
            f"{source}: use either imageKey or "
            f"sourceImageUrl, not both"
        )

    if not has_image_key_field and not has_source_url_field:
        return

    if has_image_key_field:
        image_key = require_non_blank_string(
            source,
            "imageKey",
            value.get("imageKey"),
        )

        if "://" in image_key:
            raise CatalogValidationError(
                f"{source}: imageKey must not be a URL"
            )

        if image_key.startswith("/"):
            raise CatalogValidationError(
                f"{source}: imageKey must not start with '/'"
            )

        if "\\" in image_key:
            raise CatalogValidationError(
                f"{source}: imageKey must use '/' separators"
            )

        if ".." in PurePosixPath(image_key).parts:
            raise CatalogValidationError(
                f"{source}: imageKey must not contain '..'"
            )

        return

    source_image_url = require_non_blank_string(
        source,
        "sourceImageUrl",
        value.get("sourceImageUrl"),
    )

    if require_image_key:
        raise CatalogValidationError(
            f"{source}: sourceImageUrl is not allowed "
            f"in a release; upload the image to S3 "
            f"and replace it with imageKey"
        )

    if not source_image_url.startswith(
        ("https://", "http://")
    ):
        raise CatalogValidationError(
            f"{source}: sourceImageUrl must be "
            f"an HTTP or HTTPS URL"
        )


def validate_image_references_recursively(
    value: Any,
    source: str,
    require_image_keys: bool,
) -> None:
    """
    Рекурсивно обходит весь объект каталога.

    Поэтому отдельно перечислять buildings, rooms, gardens,
    scenes и будущие вложенные объекты не требуется:
    любое встретившееся imageKey/sourceImageUrl будет проверено.
    """
    if isinstance(value, dict):
        if (
            "imageKey" in value
            or "sourceImageUrl" in value
            or "imageUrl" in value
        ):
            validate_image_reference(
                source=source,
                value=value,
                require_image_key=require_image_keys,
            )

        for field_name, child in value.items():
            if field_name in {
                "imageKey",
                "sourceImageUrl",
                "imageUrl",
            }:
                continue

            validate_image_references_recursively(
                value=child,
                source=f"{source}.{field_name}",
                require_image_keys=require_image_keys,
            )

        return

    if isinstance(value, list):
        for index, child in enumerate(value):
            validate_image_references_recursively(
                value=child,
                source=f"{source}[{index}]",
                require_image_keys=require_image_keys,
            )


def validate_all_image_references(
    catalog: dict[str, list[dict[str, Any]]],
    require_image_keys: bool,
) -> None:
    """
    Запускает рекурсивный обход для каждой корневой
    каталожной сущности.
    """
    for category_name, items in catalog.items():
        for item in items:
            template_id = item["templateId"]

            validate_image_references_recursively(
                value=item,
                source=f"{category_name} '{template_id}'",
                require_image_keys=require_image_keys,
            )

def acquisition_source_allowed(
    item: dict[str, Any],
    source: str,
) -> bool:
    allowed_sources = item.get(
        "allowedAcquisitionSources"
    )

    # Нет белого списка — разрешён любой источник.
    if allowed_sources is None:
        return True

    if not isinstance(allowed_sources, list):
        raise CatalogValidationError(
            "allowedAcquisitionSources must be an array or null"
        )

    return source in allowed_sources

def validate_loot_bundle(
    source: str,
    bundle: Any,
    acquisition_source: str,
    indexes: dict[str, dict[str, dict[str, Any]]],
) -> None:
    if bundle is None:
        return

    if not isinstance(bundle, dict):
        raise CatalogValidationError(
            f"{source}: loot bundle must be an object"
        )

    known_pools = set(LOOT_POOL_CATEGORIES) | {
        "diamondLoot"
    }

    unknown_pools = set(bundle) - known_pools

    if unknown_pools:
        raise CatalogValidationError(
            f"{source}: unknown loot field(s): "
            f"{sorted(unknown_pools)}"
        )

    has_loot = any(
        bundle.get(pool_name) is not None
        for pool_name in known_pools
    )

    if not has_loot:
        raise CatalogValidationError(
            f"{source}: loot bundle contains no loot"
        )

    for pool_name, category_name in LOOT_POOL_CATEGORIES.items():
        pool = bundle.get(pool_name)

        if pool is None:
            continue

        if not isinstance(pool, dict):
            raise CatalogValidationError(
                f"{source}, {pool_name}: must be an object"
            )

        amount = pool.get("amount")

        if amount is not None:
            if (
                not isinstance(amount, int)
                or isinstance(amount, bool)
                or amount < 1
            ):
                raise CatalogValidationError(
                    f"{source}, {pool_name}: "
                    f"amount must be a positive integer"
                )

        # null означает один выбранный шаблон.
        effective_amount = (
            amount if amount is not None else 1
        )

        drop_chance = pool.get("dropChance")

        if drop_chance is not None:
            if (
                not isinstance(drop_chance, (int, float))
                or isinstance(drop_chance, bool)
                or not 0 <= drop_chance <= 1
            ):
                raise CatalogValidationError(
                    f"{source}, {pool_name}: "
                    f"dropChance must be between 0 and 1"
                )

        template_ids = pool.get("templateIds")

        if template_ids is None:
            # Можно выбирать из всех шаблонов категории,
            # разрешённых для данного источника.
            available = [
                template_id
                for template_id, item
                in indexes[category_name].items()
                if acquisition_source_allowed(
                    item,
                    acquisition_source,
                )
            ]

            if len(available) < effective_amount:
                raise CatalogValidationError(
                    f"{source}, {pool_name}: "
                    f"amount is {effective_amount}, but only "
                    f"{len(available)} {category_name} "
                    f"template(s) are available through "
                    f"{acquisition_source}"
                )

            continue

        if not isinstance(template_ids, list):
            raise CatalogValidationError(
                f"{source}, {pool_name}: "
                f"templateIds must be an array or null"
            )

        if not template_ids:
            raise CatalogValidationError(
                f"{source}, {pool_name}: "
                f"templateIds must not be empty"
            )

        seen_template_ids: set[str] = set()

        for index, template_id in enumerate(template_ids):
            template_id = require_non_blank_string(
                f"{source}, {pool_name}",
                f"templateIds[{index}]",
                template_id,
            )

            if template_id in seen_template_ids:
                raise CatalogValidationError(
                    f"{source}, {pool_name}: "
                    f"duplicate templateId '{template_id}'"
                )

            seen_template_ids.add(template_id)

            item = indexes[category_name].get(template_id)

            if item is None:
                raise CatalogValidationError(
                    f"{source}, {pool_name}: unknown "
                    f"{category_name} templateId "
                    f"'{template_id}'"
                )

            if not acquisition_source_allowed(
                item,
                acquisition_source,
            ):
                raise CatalogValidationError(
                    f"{source}, {pool_name}: "
                    f"'{template_id}' is not available "
                    f"through {acquisition_source}"
                )

        if len(seen_template_ids) < effective_amount:
            raise CatalogValidationError(
                f"{source}, {pool_name}: "
                f"amount is {effective_amount}, but "
                f"templateIds contains only "
                f"{len(seen_template_ids)} template(s)"
            )

    validate_diamond_loot(
        source=source,
        bundle=bundle,
    )

def validate_diamond_loot(
    source: str,
    bundle: dict[str, Any],
) -> None:
    pool = bundle.get("diamondLoot")

    if pool is None:
        return

    if not isinstance(pool, dict):
        raise CatalogValidationError(
            f"{source}, diamondLoot: must be an object"
        )

    amount = pool.get("amount")

    if (
        not isinstance(amount, int)
        or isinstance(amount, bool)
        or amount < 1
    ):
        raise CatalogValidationError(
            f"{source}, diamondLoot: "
            f"amount must be a positive integer"
        )

    drop_chance = pool.get("dropChance")

    if drop_chance is not None and (
        not isinstance(drop_chance, (int, float))
        or isinstance(drop_chance, bool)
        or not 0 <= drop_chance <= 1
    ):
        raise CatalogValidationError(
            f"{source}, diamondLoot: "
            f"dropChance must be between 0 and 1"
        )

def validate_catalog(
    catalog: dict[str, list[dict[str, Any]]],
    require_image_keys: bool,
) -> None:
    indexes = {
        category: index_by_template_id(
            category,
            items,
        )
        for category, items in catalog.items()
    }

    validate_acquisition_sources(catalog)
    validate_nested_identifiers(catalog)

    # Рекурсивно обходит все категории, включая
    # buildings, rooms, gardens и другие вложенные объекты.
    validate_all_image_references(
        catalog,
        require_image_keys=require_image_keys,
    )

    location_ids = set(indexes["locations"])
    medal_ids = set(indexes["medals"])
    supply_ids = set(indexes["supplies"])
    quest_ids = set(indexes["quests"])


    # Enemies
    enemy_tag_sets: list[set[str]] = []

    for enemy in catalog["enemies"]:
        enemy_id = enemy["templateId"]
        enemy_source = f"Enemy '{enemy_id}'"

        tags = enemy.get("tags")

        if tags is None:
            enemy_tag_sets.append(set())
            continue

        if not isinstance(tags, list):
            raise CatalogValidationError(
                f"{enemy_source}: tags must be an array or null"
            )

        tag_set: set[str] = set()

        for index, tag in enumerate(tags):
            tag = require_non_blank_string(
                enemy_source,
                f"tags[{index}]",
                tag,
            )

            if tag in tag_set:
                raise CatalogValidationError(
                    f"{enemy_source}: duplicate tag '{tag}'"
                )

            tag_set.add(tag)

        enemy_tag_sets.append(tag_set)

    # Maps
    for map_item in catalog["maps"]:
        map_id = map_item["templateId"]
        map_source = f"Map '{map_id}'"

        completion_loot_bundle = map_item.get(
            "completionLootBundle"
        )

        if completion_loot_bundle is None:
            raise CatalogValidationError(
                f"{map_source}: completionLootBundle is required"
            )

        if "type" in map_item:
            raise CatalogValidationError(
                f"{map_source}: field 'type' is not allowed; "
                f"map state belongs to player data, not catalog"
            )

        validate_loot_bundle(
            source=f"{map_source}, completion loot",
            bundle=completion_loot_bundle,
            acquisition_source=EXPEDITION_REWARD,
            indexes=indexes,
        )

        if (
            "imageKey" not in map_item
            and "sourceImageUrl" not in map_item
        ):
            raise CatalogValidationError(
                f"{map_source}: map image is required"
            )

        require_required_reference(
            map_source,
            map_item.get("completionMedalTemplateId"),
            "medal",
            medal_ids,
        )

        location_slots = require_object_list(
            map_source,
            "locationSlots",
            map_item.get("locationSlots"),
        )

        enemy_slots = require_object_list(
            map_source,
            "enemySlots",
            map_item.get("enemySlots"),
        )

        for slot in enemy_slots:
            slot_source = (
                f"{map_source}, enemy slot "
                f"'{slot.get('slotId')}'"
            )

            require_coordinate(
                slot_source,
                "x",
                slot.get("x"),
            )

            require_coordinate(
                slot_source,
                "y",
                slot.get("y"),
            )

            required_tags = slot.get("requiredTags")

            if required_tags is not None:
                if not isinstance(required_tags, list):
                    raise CatalogValidationError(
                        f"{slot_source}: "
                        f"requiredTags must be an array or null"
                    )

                required_tag_set: set[str] = set()

                for index, tag in enumerate(required_tags):
                    tag = require_non_blank_string(
                        slot_source,
                        f"requiredTags[{index}]",
                        tag,
                    )

                    if tag in required_tag_set:
                        raise CatalogValidationError(
                            f"{slot_source}: duplicate required tag "
                            f"'{tag}'"
                        )

                    required_tag_set.add(tag)

                if required_tags is None:
                    required_tag_set = set()

                matching_enemy_exists = any(
                    required_tag_set <= enemy_tags
                    for enemy_tags in enemy_tag_sets
                )

                if not matching_enemy_exists:
                    raise CatalogValidationError(
                        f"{slot_source}: no enemy matches "
                        f"the slot restrictions"
                    )

        for slot in location_slots:
            if "requiredTags" in slot:
                raise CatalogValidationError(
                    f"{slot_source}: field 'requiredTags' is not allowed"
                )

            slot_source = (
                f"{map_source}, location slot "
                f"'{slot.get('slotId')}'"
            )

            require_coordinate(
                slot_source,
                "x",
                slot.get("x"),
            )

            require_coordinate(
                slot_source,
                "y",
                slot.get("y"),
            )

            mode = require_non_blank_string(
                slot_source,
                "mode",
                slot.get("mode"),
            )

            if mode not in LOCATION_SLOT_MODES:
                raise CatalogValidationError(
                    f"{slot_source}: unknown location slot mode "
                    f"'{mode}'"
                )

            if mode == "FIXED":
                require_required_reference(
                    slot_source,
                    slot.get("fixedLocationTemplateId"),
                    "location",
                    location_ids,
                )

                if slot.get("allowedTypes") is not None:
                    raise CatalogValidationError(
                        f"{slot_source}: allowedTypes is allowed "
                        f"only for RANDOM mode"
                    )

            if mode == "RANDOM":
                if slot.get("fixedLocationTemplateId") is not None:
                    raise CatalogValidationError(
                        f"{slot_source}: fixedLocationTemplateId "
                        f"is allowed only for FIXED mode"
                    )

                matching_locations = [
                    location
                    for location in catalog["locations"]
                    if (
                            allowed_types is None
                            or location.get("type") in allowed_types
                    )
                ]

                if not matching_locations:
                    raise CatalogValidationError(
                        f"{slot_source}: no location matches "
                        f"the slot restrictions"
                    )

            allowed_types = slot.get("allowedTypes")

            if allowed_types is not None:
                slot_source = (
                    f"{map_source}, location slot "
                    f"'{slot.get('slotId')}'"
                )

                if not isinstance(allowed_types, list):
                    raise CatalogValidationError(
                        f"{slot_source}: "
                        f"allowedTypes must be an array or null"
                    )

                if not allowed_types:
                    raise CatalogValidationError(
                        f"{slot_source}: "
                        f"allowedTypes must not be empty; "
                        f"omit the field if there is no restriction"
                    )

                seen_types: set[str] = set()

                for index, location_type in enumerate(
                    allowed_types
                ):
                    location_type = require_non_blank_string(
                        slot_source,
                        f"allowedTypes[{index}]",
                        location_type,
                    )

                    if location_type not in LOCATION_TYPES:
                        raise CatalogValidationError(
                            f"{slot_source}: unknown location type "
                            f"'{location_type}'"
                        )

                    if location_type in seen_types:
                        raise CatalogValidationError(
                            f"{slot_source}: duplicate location type "
                            f"'{location_type}'"
                        )

                    seen_types.add(location_type)

    # Plants
    for plant in catalog["plants"]:
        require_required_reference(
            f"Plant '{plant['templateId']}'",
            plant.get("supplyTemplateId"),
            "supply",
            supply_ids,
        )

        plant_source = f"Plant '{plant['templateId']}'"

        require_positive_integer(
            plant_source,
            "supplyAmount",
            plant.get("supplyAmount"),
        )

        require_positive_integer(
            plant_source,
            "seedAmount",
            plant.get("seedAmount"),
        )

    # Garden items
    for item in catalog["gardenItems"]:
        require_reference(
            f"Garden item '{item['templateId']}'",
            item.get("supplyTemplateId"),
            "supply",
            supply_ids,
        )

    # Recipes
    for recipe in catalog["recipes"]:
        recipe_id = recipe["templateId"]
        recipe_source = f"Recipe '{recipe_id}'"

        require_required_reference(
            f"{recipe_source} result",
            recipe.get("resultSupplyTemplateId"),
            "supply",
            supply_ids,
        )

        ingredients = require_object_list(
            recipe_source,
            "ingredients",
            recipe.get("ingredients"),
        )

        for ingredient in ingredients:
            require_required_reference(
                f"{recipe_source} ingredient",
                ingredient.get("supplyTemplateId"),
                "supply",
                supply_ids,
            )

    # Locations -> quests
    for location in catalog["locations"]:
        location_id = location["templateId"]
        location_source = f"Location '{location_id}'"

        location_type = require_non_blank_string(
            location_source,
            "type",
            location.get("type"),
        )

        if location_type not in LOCATION_TYPES:
            raise CatalogValidationError(
                f"{location_source}: unknown location type "
                f"'{location_type}'"
            )

        if "tags" in location:
            raise CatalogValidationError(
                f"{location_source}: field 'tags' is not allowed"
            )

        scenes = require_object_list(
            location_source,
            "scenes",
            location.get("scenes"),
        )

        for scene in scenes:
            require_reference(
                f"{location_source}, scene "
                f"'{scene.get('templateId')}'",
                scene.get("questTemplateId"),
                "quest",
                quest_ids,
            )

    # Quest pages
    for quest in catalog["quests"]:
        quest_id = quest["templateId"]
        quest_source = f"Quest '{quest_id}'"

        pages = require_object_list(
            quest_source,
            "pages",
            quest.get("pages"),
        )

        page_numbers: set[int] = set()
        ending_ids: set[str] = set()

        for index, page in enumerate(pages):
            number = page.get("number")

            if (
                not isinstance(number, int)
                or isinstance(number, bool)
            ):
                raise CatalogValidationError(
                    f"{quest_source}, page at index "
                    f"{index}: missing or invalid number"
                )

            if number in page_numbers:
                raise CatalogValidationError(
                    f"{quest_source}: duplicate "
                    f"page number {number}"
                )

            page_numbers.add(number)

        start_page = quest.get(
            "startPageNumber"
        )

        if (
            not isinstance(start_page, int)
            or isinstance(start_page, bool)
        ):
            raise CatalogValidationError(
                f"{quest_source}: missing or invalid "
                f"startPageNumber"
            )

        if start_page not in page_numbers:
            raise CatalogValidationError(
                f"{quest_source}: startPageNumber "
                f"{start_page} does not exist"
            )

        for page in pages:
            page_number = page["number"]

            options = require_object_list(
                f"{quest_source}, page {page_number}",
                "options",
                page.get("options"),
            )

            loot_bundle = page.get("lootBundle")
            ending_id = page.get("endingId")
            loot_button_text = page.get("lootButtonText")

            if ending_id is not None:
                ending_id = require_non_blank_string(
                    f"{quest_source}, page {page_number}",
                    "endingId",
                    ending_id,
                )

                if ending_id in ending_ids:
                    raise CatalogValidationError(
                        f"{quest_source}: duplicate endingId "
                        f"'{ending_id}'"
                    )

                ending_ids.add(ending_id)

            if ending_id is not None and options:
                raise CatalogValidationError(
                    f"{quest_source}, page {page_number}: "
                    f"ending page must not have options"
                )

            if loot_bundle is not None:
                if not isinstance(ending_id, str) or not ending_id.strip():
                    raise CatalogValidationError(
                        f"{quest_source}, page {page_number}: "
                        f"lootBundle is allowed only on a page with endingId"
                    )

                validate_loot_bundle(
                    source=(
                        f"{quest_source}, page "
                        f"{page_number}, loot"
                    ),
                    bundle=loot_bundle,
                    acquisition_source=QUEST_REWARD,
                    indexes=indexes,
                )

            if loot_button_text is not None and loot_bundle is None:
                raise CatalogValidationError(
                    f"{quest_source}, page {page_number}: "
                    f"lootButtonText requires lootBundle"
                )

            for option_index, option in enumerate(options):
                target = option.get("targetPageNumber")

                if (
                    not isinstance(target, int)
                    or isinstance(target, bool)
                ):
                    raise CatalogValidationError(
                        f"{quest_source}, page "
                        f"{page_number}, option at index "
                        f"{option_index}: missing or invalid "
                        f"targetPageNumber"
                    )

                if target not in page_numbers:
                    raise CatalogValidationError(
                        f"{quest_source}, page "
                        f"{page_number}: target page "
                        f"{target} does not exist"
                    )

    # Animals
    for animal in catalog["animals"]:
        animal_id = animal["templateId"]
        animal_source = f"Animal '{animal_id}'"

        require_non_blank_string(
            animal_source,
            "kind",
            animal.get("kind"),
        )

        require_non_blank_string(
            animal_source,
            "initialDisplayName",
            animal.get("initialDisplayName"),
        )


def build_catalog(
    catalog_root: Path,
    version: str,
    schema_version: int,
    commit_sha: str,
    require_image_keys: bool,
) -> dict[str, Any]:
    catalog: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for (
        category_name,
        directory_name,
    ) in CATEGORY_DIRS.items():
        catalog[category_name] = load_category(
            catalog_root,
            directory_name,
        )

    validate_catalog(
        catalog,
        require_image_keys=require_image_keys,
    )

    # Хешируется только фактическое содержимое каталога.
    # Форматирование JSON и порядок полей на хеш не влияют.
    canonical_catalog = json.dumps(
        catalog,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    content_hash = hashlib.sha256(
        canonical_catalog
    ).hexdigest()

    return {
        "version": version,
        "schemaVersion": schema_version,
        "commitSha": commit_sha,
        "contentHash": content_hash,
        "catalog": catalog,
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--catalog-dir",
        default="catalog",
    )

    parser.add_argument(
        "--output",
        default="build/catalog-release.json",
    )

    parser.add_argument(
        "--version",
        required=True,
    )

    parser.add_argument(
        "--schema-version",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--commit-sha",
        required=True,
    )

    parser.add_argument(
        "--require-image-keys",
        action="store_true",
        help=(
            "Reject sourceImageUrl and require final imageKey "
            "for every image reference found in the catalog"
        ),
    )

    args = parser.parse_args()

    try:
        result = build_catalog(
            catalog_root=Path(
                args.catalog_dir
            ),
            version=args.version,
            schema_version=args.schema_version,
            commit_sha=args.commit_sha,
            require_image_keys=args.require_image_keys,
        )

        output = Path(args.output)
        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=2,
            )

        print(
            f"Catalog release built: {output}"
        )
        print(
            f"Version: {result['version']}"
        )
        print(
            f"Commit: {result['commitSha']}"
        )
        print(
            f"Content hash: "
            f"{result['contentHash']}"
        )

        for (
            category,
            values,
        ) in result["catalog"].items():
            print(
                f"  {category}: {len(values)}"
            )

        return 0

    except CatalogValidationError as exc:
        print(
            f"CATALOG VALIDATION ERROR: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())