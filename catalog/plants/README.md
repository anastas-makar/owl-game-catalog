# Растения

Каждый файл описывает один шаблон растения.

Общие правила находятся в [`catalog/README.md`](../README.md).

## Связь с припасом

Если растение при сборе даёт припас, `supplyTemplateId` должен ссылаться на существующий припас.

```json
{
  "templateId": "pumpkin-plant",
  "name": "Тыква",
  "supplyTemplateId": "pumpkin",
  "sourceImageUrl": "https://example.org/pumpkin-plant.png"
}
```

Добавьте параметры роста и другие обязательные поля текущего `CatalogPlantImport`, ориентируясь на существующие растения.

## Случайный выбор в квесте

```json
{
  "plantLoot": {
    "templateIds": [
      "pumpkin-plant"
    ],
    "amount": 1,
    "dropChance": 0.5
  }
}
```

Если `templateIds` отсутствует, backend может выбирать любое растение, доступное через `QUEST_REWARD`.

## Ограничение получения

Только квестовое растение:

```json
{
  "allowedAcquisitionSources": [
    "QUEST_REWARD"
  ]
}
```

## Проверка

- `supplyTemplateId` существует;
- параметры роста соответствуют текущей механике;
- enum-значения существуют;
- изображение не добавлено бинарным файлом.
