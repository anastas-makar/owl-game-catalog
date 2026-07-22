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


class CatalogValidationError(Exception):
    pass


def load_category(root: Path, directory_name: str) -> list[dict[str, Any]]:
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

        template_id = value.get("templateId")

        if not isinstance(template_id, str) or not template_id.strip():
            raise CatalogValidationError(
                f"{path}: missing or invalid templateId"
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
    reference: str | None,
    target_name: str,
    target_ids: set[str],
) -> None:
    if reference is None:
        return

    if reference not in target_ids:
        raise CatalogValidationError(
            f"{source}: references unknown {target_name} "
            f"templateId '{reference}'"
        )


def validate_catalog(catalog: dict[str, list[dict[str, Any]]]) -> None:
    indexes = {
        category: index_by_template_id(category, items)
        for category, items in catalog.items()
    }

    location_ids = set(indexes["locations"])
    medal_ids = set(indexes["medals"])
    supply_ids = set(indexes["supplies"])
    quest_ids = set(indexes["quests"])

    # Maps
    for map_item in catalog["maps"]:
        map_id = map_item["templateId"]

        require_reference(
            f"Map '{map_id}'",
            map_item.get("completionMedalTemplateId"),
            "medal",
            medal_ids,
        )

        for slot in map_item.get("locationSlots", []):
            if slot.get("mode") == "FIXED":
                require_reference(
                    f"Map '{map_id}', location slot "
                    f"'{slot.get('slotId')}'",
                    slot.get("fixedLocationTemplateId"),
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

        require_reference(
            f"Recipe '{recipe_id}' result",
            recipe.get("resultSupplyTemplateId"),
            "supply",
            supply_ids,
        )

        for ingredient in recipe.get("ingredients", []):
            require_reference(
                f"Recipe '{recipe_id}' ingredient",
                ingredient.get("supplyTemplateId"),
                "supply",
                supply_ids,
            )

    # Locations -> quests
    for location in catalog["locations"]:
        location_id = location["templateId"]

        for scene in location.get("scenes", []):
            require_reference(
                f"Location '{location_id}', scene "
                f"'{scene.get('templateId')}'",
                scene.get("questTemplateId"),
                "quest",
                quest_ids,
            )

    # Basic nested uniqueness checks.
    for building in catalog["buildings"]:
        building_id = building["templateId"]

        for field in ("rooms", "gardens"):
            seen: set[str] = set()

            for child in building.get(field, []):
                child_id = child.get("templateId")

                if not child_id:
                    raise CatalogValidationError(
                        f"Building '{building_id}': "
                        f"{field} item has no templateId"
                    )

                if child_id in seen:
                    raise CatalogValidationError(
                        f"Building '{building_id}': duplicate "
                        f"{field} templateId '{child_id}'"
                    )

                seen.add(child_id)

    # Quest page checks.
    for quest in catalog["quests"]:
        quest_id = quest["templateId"]
        pages = quest.get("pages", [])

        page_numbers = {
            page.get("number")
            for page in pages
        }

        if len(page_numbers) != len(pages):
            raise CatalogValidationError(
                f"Quest '{quest_id}': duplicate page numbers"
            )

        start_page = quest.get("startPageNumber")

        if start_page not in page_numbers:
            raise CatalogValidationError(
                f"Quest '{quest_id}': startPageNumber "
                f"{start_page} does not exist"
            )

        for page in pages:
            for option in page.get("options", []):
                target = option.get("targetPageNumber")

                if target not in page_numbers:
                    raise CatalogValidationError(
                        f"Quest '{quest_id}', page "
                        f"{page.get('number')}: target page "
                        f"{target} does not exist"
                    )


def build_catalog(
    catalog_root: Path,
    version: str,
    schema_version: int,
    commit_sha: str,
) -> dict[str, Any]:

    catalog: dict[str, list[dict[str, Any]]] = {}

    for category_name, directory_name in CATEGORY_DIRS.items():
        catalog[category_name] = load_category(
            catalog_root,
            directory_name,
        )

    validate_catalog(catalog)

    # Hash only the actual catalog content.
    # Formatting and field order do not affect the hash.
    canonical_catalog = json.dumps(
        catalog,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    content_hash = hashlib.sha256(canonical_catalog).hexdigest()

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
            catalog_root=Path(args.catalog_dir),
            version=args.version,
            schema_version=args.schema_version,
            commit_sha=args.commit_sha,
        )

        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", encoding="utf-8") as file:
            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=2,
            )

        print(f"Catalog release built: {output}")
        print(f"Version: {result['version']}")
        print(f"Commit: {result['commitSha']}")
        print(f"Content hash: {result['contentHash']}")

        for category, values in result["catalog"].items():
            print(f"  {category}: {len(values)}")

        return 0

    except CatalogValidationError as exc:
        print(
            f"CATALOG VALIDATION ERROR: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())