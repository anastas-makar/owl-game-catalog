# Квесты

Квест состоит из страниц.

На каждой странице могут быть текст и изображение. Если квест продолжается, страница содержит варианты действий, ведущие на следующие страницы.

Квест запускается из сцены локации, которая ссылается на него через `questTemplateId`. Подробнее см. в [документации локаций](../locations/README.md).

Конечная страница не содержит вариантов продолжения и имеет стабильный `endingId`.

Концовка также может:

* изменить сцену локации через `scenePatch`;
* выдать награду через `lootBundle`.

Общие правила находятся в [`catalog/README.md`](../README.md).

## Полный пример

Ниже приведён пример квеста, в котором используются все поля модели.

```json
{
  "templateId": "first-hatches",
  "title": "Первые люки",
  "startPageNumber": 1,
  "pages": [
    {
      "number": 1,
      "name": "Закрытый люк",
      "description": "Перед вами старый железный люк. Из-под крышки тянет холодом.",
      "imageKey": "quests/first-hatches/closed-hatch.webp",
      "options": [
        {
          "description": "Открыть люк",
          "targetPageNumber": 2
        },
        {
          "description": "Не трогать люк",
          "targetPageNumber": 3
        }
      ]
    },
    {
      "number": 2,
      "name": "Подземелье",
      "description": "Под люком обнаружился старый подземный зал. В углу стоит покрытый пылью сундук.",
      "imageKey": "quests/first-hatches/underground-hall.webp",
      "options": [],
      "endingId": "hatch-opened",
      "scenePatch": {
        "description": "Старый железный люк теперь открыт. Под ним виден спуск в подземелье.",
        "imageKey": "locations/old-grotto/open-hatch.webp"
      },
      "lootButtonText": "Забрать найденное",
      "lootBundle": {
        "buildingLoot": {
          "templateIds": [
            "small-stone-house",
            "wooden-house",
            "swamp-hut"
          ],
          "amount": 2,
          "dropChance": 0.1
        },
        "mapLoot": {
          "templateIds": [
            "old-forest-map",
            "swamp-map"
          ],
          "amount": 1,
          "dropChance": 0.2
        },
        "diamondLoot": {
          "amount": 20,
          "dropChance": 1.0
        },
        "gardenItemLoot": {
          "templateIds": [
            "old-watering-can",
            "wooden-planter"
          ],
          "amount": 1,
          "dropChance": 0.3
        },
        "plantLoot": {
          "templateIds": null,
          "amount": 2,
          "dropChance": 0.5
        },
        "furnitureLoot": {
          "templateIds": [
            "red-sofa",
            "green-armchair",
            "old-table"
          ],
          "amount": 2,
          "dropChance": 0.25
        },
        "recipeLoot": {
          "templateIds": [
            "pumpkin-soup",
            "healing-potion"
          ],
          "amount": 1,
          "dropChance": 0.5
        },
        "locationLoot": {
          "templateIds": [
            "old-grotto"
          ],
          "amount": 1,
          "dropChance": 0.1
        }
      }
    },
    {
      "number": 3,
      "name": "Возвращение",
      "description": "Вы решили пока не открывать люк и вернуться к нему позже.",
      "imageKey": "quests/first-hatches/leave-hatch.webp",
      "options": [],
      "endingId": "left-the-hatch",
      "scenePatch": {
        "description": "Старый железный люк по-прежнему закрыт.",
        "imageKey": "locations/old-grotto/closed-hatch.webp"
      }
    }
  ]
}
```

В рабочей ветке вместо `imageKey` можно использовать временный `sourceImageUrl` согласно [общим правилам работы с изображениями](../README.md). Перед попаданием каталога в `main` временные ссылки заменяются на `imageKey`.

## Стартовая страница

`startPageNumber` указывает номер страницы, с которой начинается квест.

Он должен совпадать с `number` одной из страниц:

```json
{
  "startPageNumber": 1
}
```

## Номера страниц

`number`:

* обязателен для каждой страницы;
* является целым числом;
* уникален внутри квеста;
* используется в `startPageNumber` и `targetPageNumber`;
* не является UUID;
* не должен случайно изменяться при редактировании существующей страницы.

Порядок страниц в JSON не используется вместо `number`.

## Переходы

Если квест продолжается, страница содержит `options`.

Каждая опция состоит из текста действия и номера следующей страницы:

```json
{
  "description": "Продолжить",
  "targetPageNumber": 4
}
```

`targetPageNumber` должен указывать на существующую страницу того же квеста.

Пример развилки:

```json
{
  "number": 1,
  "name": "Развилка",
  "description": "Тропа разделяется надвое.",
  "options": [
    {
      "description": "Пойти налево",
      "targetPageNumber": 2
    },
    {
      "description": "Пойти направо",
      "targetPageNumber": 3
    }
  ]
}
```

## Конечные страницы и `endingId`

Конечная страница завершает квест и не содержит вариантов продолжения.

Она имеет стабильный `endingId`:

```json
{
  "number": 7,
  "name": "Спасение",
  "description": "Сова спасена.",
  "options": [],
  "endingId": "owl-rescued"
}
```

`endingId`:

* должен быть непустой строкой;
* уникален внутри квеста;
* сохраняется при редактировании существующей развязки.

Новый `endingId` означает новую развязку.

`endingId` также используется backend для различения концовок и связанных с ними действий, в частности получения награды.

## Изображения страниц

Страница может содержать собственное изображение:

```json
{
  "imageKey": "quests/first-hatches/underground-hall.webp"
}
```

В рабочей ветке автора вместо `imageKey` допускается временный `sourceImageUrl`.

Не следует одновременно указывать `imageKey` и `sourceImageUrl`.

## `scenePatch`

`scenePatch` описывает изменение сцены локации, вызванное конкретной концовкой квеста.

Например, до прохождения квеста люк может быть закрыт, а после одной из концовок — открыт.

```json
{
  "endingId": "hatch-opened",
  "scenePatch": {
    "description": "Старый люк открыт. Под ним видна лестница, ведущая вниз.",
    "imageKey": "locations/old-grotto/open-hatch.webp"
  }
}
```

`scenePatch` может изменять:

* `description` — описание сцены;
* `imageKey` — изображение сцены.

В рабочей ветке автора вместо `imageKey` может использоваться временный `sourceImageUrl`.

`scenePatch` относится к сцене локации, из которой был запущен квест, а не к самой странице квеста.

## Лут

Конечная страница с `endingId` может содержать `lootBundle`.

```json
{
  "endingId": "hatch-opened",
  "lootButtonText": "Забрать награду",
  "lootBundle": {
    "recipeLoot": {
      "templateIds": [
        "pumpkin-soup",
        "healing-potion"
      ],
      "amount": 1,
      "dropChance": 0.5
    },
    "diamondLoot": {
      "amount": 20
    }
  }
}
```

Для квестового `lootBundle` источником получения считается `QUEST_REWARD`.

Если у награды задан `allowedAcquisitionSources`, её белый список должен разрешать `QUEST_REWARD`.

Подробно структура `lootBundle`, правила `templateIds`, `amount`, `dropChance` и выбора без повторений описаны в [документации лута](../LOOT.md).

## Кнопка награды

`lootButtonText` задаёт текст кнопки, через которую игрок получает награду:

```json
{
  "lootButtonText": "Забрать награду"
}
```

`lootButtonText` используется только вместе с `lootBundle`.

Поле `lootAvailable` в каталоге отсутствует. Доступность награды является состоянием конкретного игрока и определяется backend.

## Проверка квеста

Перед pull request проверьте:

* `templateId` квеста уникален;
* `startPageNumber` указывает на существующую страницу;
* номера страниц являются целыми числами и не повторяются;
* все `targetPageNumber` указывают на существующие страницы;
* все `endingId` уникальны внутри квеста;
* конечные страницы не содержат вариантов продолжения;
* все страницы достижимы от `startPageNumber`;
* каждая неконечная страница содержит хотя бы один вариант продолжения;
* из каждой достижимой страницы существует путь хотя бы к одной конечной странице.
* `lootBundle` находится только на странице с `endingId`;
* `lootButtonText` не существует без `lootBundle`;
* содержимое `lootBundle` соответствует [правилам лута](../LOOT.md);
* награды из `lootBundle` разрешено получать через `QUEST_REWARD`;
* временные ссылки на изображения открываются без авторизации;
* перед попаданием изменений в `main` временные `sourceImageUrl` заменены на `imageKey`.
