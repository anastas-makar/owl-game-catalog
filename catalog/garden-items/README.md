# Предметы для сада

Каждый файл описывает один корневой шаблон предмета, используемого в садовой механике.

Общие правила находятся в [`catalog/README.md`](../README.md).

## Связь с припасом

Если предмет создаёт, хранит или представляет припас, поле `supplyTemplateId` должно ссылаться на существующий файл из [`../supplies/`](../supplies/).

```json
{
  "templateId": "pumpkin-bed",
  "name": "Грядка с тыквой",
  "supplyTemplateId": "pumpkin",
  "sourceImageUrl": "https://example.org/pumpkin-bed.png"
}
```

Добавьте остальные обязательные поля текущего `CatalogGardenItemImport`, ориентируясь на существующие предметы.

## Ограничение получения

Если предмет доступен только как квестовая награда:

```json
{
  "allowedAcquisitionSources": [
    "QUEST_REWARD"
  ]
}
```

## Проверка

- `templateId` уникален;
- `supplyTemplateId` существует в `supplies`;
- поля соответствуют import DTO;
- enum-значения существуют;
- изображение передано ссылкой, а не файлом.
