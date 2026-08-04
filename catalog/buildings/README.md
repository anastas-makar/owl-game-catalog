# Здания

Каждый JSON-файл в этой директории описывает один шаблон здания вместе с его комнатами и садами.

Общие правила описаны в [`catalog/README.md`](../README.md).

## Главное

- Один файл — одно здание.
- Имя файла совпадает с `templateId`.
- Комнаты и сады являются вложенными частями здания.
- Здание импортируется целиком, даже если изменена только одна комната.
- Стабильный `templateId` комнаты или сада позволяет отличить редактирование от удаления и создания нового элемента.

## Минимальный пример

Названия полей должны соответствовать актуальным `CatalogBuildingImport`, `CatalogRoomImport` и `CatalogGardenImport`.

```json
{
  "templateId": "stone-fortress",
  "name": "Каменный замок",
  "type": "FORTRESS",
  "cost": 5000,
  "sourceImageUrl": "https://example.org/stone-fortress.png",
  "rooms": [
    {
      "templateId": "main-hall",
      "name": "Главный зал",
      "roomNumber": 1,
      "sourceImageUrl": "https://example.org/main-hall.png"
    },
    {
      "templateId": "kitchen",
      "name": "Кухня",
      "roomNumber": 2
    }
  ],
  "gardens": [
    {
      "templateId": "main-garden",
      "name": "Сад",
      "gardenNumber": 1,
      "gardenType": "GARDEN"
    }
  ]
}
```

Если реальные enum или обязательные поля отличаются, ориентируйтесь на текущие import DTO и существующие файлы категории.

## Идентификаторы

Корневой `templateId` уникален среди зданий. Идентификаторы комнат и садов уникальны внутри здания.

При обычном изменении кухни сохраняйте её идентификатор:

```json
{
  "templateId": "kitchen",
  "name": "Большая кухня"
}
```

Замена `kitchen` на `dining-room` будет означать удаление старой комнаты и добавление новой.

## Порядковые номера

`roomNumber` и `gardenNumber` отвечают за порядок, а не за идентичность. Не используйте номер вместо стабильного идентификатора.

## Изображения

Изображение может быть у здания и у его вложенных частей.

В рабочем pull request:

```json
{
  "sourceImageUrl": "https://example.org/kitchen.png"
}
```

После переноса в S3:

```json
{
  "imageKey": "buildings/stone-fortress/kitchen.webp"
}
```

## Источники получения

Если здание можно получать любым способом, поле ограничения не нужно. Для квестового здания:

```json
{
  "allowedAcquisitionSources": [
    "QUEST_REWARD"
  ]
}
```

## Проверка перед pull request

- имя файла совпадает с `templateId`;
- у всех комнат и садов есть стабильные `templateId`;
- идентификаторы не повторяются внутри здания;
- enum `type` и `gardenType` существуют в backend;
- временные ссылки публично доступны;
- UUID игровых зданий и комнат отсутствуют.
