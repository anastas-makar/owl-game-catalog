#!/usr/bin/env python3

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


CATEGORY_DIRS = {
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


class CatalogValidationError(Exception):
    pass


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


def validate_catalog(
    catalog: dict[str, list[dict[str, Any]]],
) -> None:
    indexes = {
        category: index_by_template_id(
            category,
            items,
        )
        for category, items in catalog.items()
    }

    validate_nested_identifiers(catalog)

    location_ids = set(indexes["locations"])
    medal_ids = set(indexes["medals"])
    supply_ids = set(indexes["supplies"])
    quest_ids = set(indexes["quests"])

    # Maps
    for map_item in catalog["maps"]:
        map_id = map_item["templateId"]
        map_source = f"Map '{map_id}'"

        require_reference(
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

        for slot in location_slots:
            if slot.get("mode") == "FIXED":
                require_reference(
                    f"{map_source}, location slot "
                    f"'{slot.get('slotId')}'",
                    slot.get(
                        "fixedLocationTemplateId"
                    ),
                    "location",
                    location_ids,
                )

    # Plants
    for plant in catalog["plants"]:
        require_reference(
            f"Plant '{plant['templateId']}'",
            plant.get("supplyTemplateId"),
            "supply",
            supply_ids,
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

        require_reference(
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
            require_reference(
                f"{recipe_source} ingredient",
                ingredient.get(
                    "supplyTemplateId"
                ),
                "supply",
                supply_ids,
            )

    # Locations -> quests
    for location in catalog["locations"]:
        location_id = location["templateId"]
        location_source = (
            f"Location '{location_id}'"
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

        for index, page in enumerate(pages):
            number = page.get("number")

            if not isinstance(number, int):
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

            for option_index, option in enumerate(
                options
            ):
                target = option.get(
                    "targetPageNumber"
                )

                if not isinstance(target, int):
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


def build_catalog(
    catalog_root: Path,
    version: str,
    schema_version: int,
    commit_sha: str,
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

    validate_catalog(catalog)

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

    args = parser.parse_args()

    try:
        result = build_catalog(
            catalog_root=Path(
                args.catalog_dir
            ),
            version=args.version,
            schema_version=args.schema_version,
            commit_sha=args.commit_sha,
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