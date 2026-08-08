# Лут

`lootBundle` описывает набор возможных наград.

Одна и та же структура используется в разных игровых ситуациях, например:

* как награда за концовку квеста;
* как награда за победу в экспедиции и освобождение карты.

Конкретный источник получения определяется местом, в котором используется `lootBundle`:

* квест — `QUEST_REWARD`;
* экспедиция — `EXPEDITION_REWARD`.

Ограничения на способы получения самих сущностей описаны в разделе [«Источники получения»](README.md#acquisition-sources).

## Структура

`lootBundle` может содержать следующие пулы:

```text
buildingLoot
mapLoot
diamondLoot
gardenItemLoot
plantLoot
furnitureLoot
recipeLoot
locationLoot
```

Каждый пул разыгрывается независимо от остальных.

Например:

```json
{
  "lootBundle": {
    "furnitureLoot": {
      "templateIds": [
        "red-sofa",
        "green-armchair",
        "old-table"
      ],
      "amount": 2,
      "dropChance": 0.25
    },
    "plantLoot": {
      "amount": 1,
      "dropChance": 0.5
    },
    "diamondLoot": {
      "amount": 20
    }
  }
}
```

Этот пример означает:

* с вероятностью 25% будут выбраны два разных предмета мебели из трёх перечисленных;
* независимо от этого с вероятностью 50% будет выбрано одно допустимое растение;
* независимо от предыдущих результатов будут гарантированно выданы 20 алмазов.

## Независимые пулы

Каждый присутствующий пул проверяет свой `dropChance` отдельно.

Например:

```json
{
  "buildingLoot": {
    "amount": 1,
    "dropChance": 0.5
  },
  "recipeLoot": {
    "amount": 1,
    "dropChance": 0.5
  }
}
```

Возможны четыре результата:

* выпало и здание, и рецепт;
* выпало только здание;
* выпал только рецепт;
* не выпало ничего.

Вероятность одного пула не влияет на вероятность другого.

## Обычный пул

Все пулы, кроме `diamondLoot`, используют одну структуру:

```json
{
  "templateIds": [
    "red-sofa",
    "green-armchair",
    "old-table"
  ],
  "amount": 2,
  "dropChance": 0.5
}
```

Поля:

* `templateIds` — множество шаблонов, из которых можно выбирать;
* `amount` — количество разных шаблонов, которые нужно выбрать;
* `dropChance` — вероятность выпадения пула.

## `templateIds`

`templateIds` ограничивает множество возможных наград.

```json
{
  "templateIds": [
    "red-sofa",
    "green-armchair",
    "old-table"
  ]
}
```

При наличии непустого списка выбирать можно только из перечисленных шаблонов.

Количество фактически выбранных шаблонов определяется полем `amount`.

### Выбор без повторений

Один и тот же шаблон не выбирается дважды внутри одного пула.

Например:

```json
{
  "templateIds": [
    "red-sofa",
    "green-armchair",
    "old-table"
  ],
  "amount": 2
}
```

означает выбор двух разных шаблонов из трёх.

Возможны, например:

```text
red-sofa + green-armchair
red-sofa + old-table
green-armchair + old-table
```

Результат:

```text
red-sofa + red-sofa
```

невозможен.

Если:

```json
{
  "templateIds": [
    "red-sofa",
    "green-armchair",
    "old-table"
  ],
  "amount": 3
}
```

будут выбраны все три шаблона.

### `templateIds: null`

Если `templateIds` отсутствует или равно `null`, выбирать можно из всех шаблонов соответствующей категории, которые разрешено получать текущим способом.

Например, в квесте:

```json
{
  "plantLoot": {
    "templateIds": null,
    "amount": 2
  }
}
```

означает выбор двух разных растений среди всех растений, доступных через `QUEST_REWARD`.

Для награды за экспедицию такой же пул выбирал бы растения, доступные через `EXPEDITION_REWARD`.

### Пустой список

Пустой список запрещён:

```json
{
  "templateIds": []
}
```

Если награда не нужна, следует убрать весь соответствующий пул.

## `amount`

Для обычного пула `amount` означает количество **разных шаблонов**, которые нужно выбрать.

Например:

```json
{
  "templateIds": [
    "recipe-a",
    "recipe-b",
    "recipe-c"
  ],
  "amount": 2
}
```

означает: выбрать два разных рецепта из трёх и выдать по одному экземпляру каждого выбранного рецепта.

`amount` должен быть положительным целым числом.

Если `amount` отсутствует или равно `null`, выбирается один шаблон.

`amount` не может превышать количество доступных кандидатов.

Поэтому такой пул ошибочен:

```json
{
  "templateIds": [
    "recipe-a",
    "recipe-b"
  ],
  "amount": 3
}
```

Если `templateIds` равно `null`, учитывается количество всех шаблонов категории, разрешённых для текущего источника получения.

Например, если через `QUEST_REWARD` разрешено получать только два рецепта, значение:

```json
{
  "recipeLoot": {
    "amount": 3
  }
}
```

также является ошибкой.

## `dropChance`

`dropChance` задаёт вероятность выпадения всего пула.

Значение находится в диапазоне от `0` до `1`.

```json
{
  "dropChance": 0.5
}
```

означает вероятность 50%.

```json
{
  "dropChance": 0.1
}
```

означает вероятность 10%.

Если `dropChance` отсутствует или равно `null`, пул выпадает гарантированно.

```json
{
  "recipeLoot": {
    "amount": 1
  }
}
```

означает гарантированную выдачу одного рецепта.

`dropChance` не является относительным весом и не определяет количество попыток.

В текущей модели отсутствуют дополнительные понятия вроде `rolls` или `withReplacement`.

## Алмазы

`diamondLoot` отличается от остальных пулов, поскольку для алмазов не существует `templateId`.

```json
{
  "diamondLoot": {
    "amount": 20,
    "dropChance": 0.5
  }
}
```

Поля:

* `amount` — количество алмазов;
* `dropChance` — вероятность их получения.

Для алмазов `amount` обязателен и должен быть положительным целым числом.

Если `dropChance` отсутствует или равно `null`, алмазы выдаются гарантированно.

Пример гарантированной награды:

```json
{
  "diamondLoot": {
    "amount": 50
  }
}
```

## Источники получения

Каждый `lootBundle` разыгрывается в контексте конкретного источника.

Квест:

```text
QUEST_REWARD
```

Экспедиция:

```text
EXPEDITION_REWARD
```

Если сущность не содержит `allowedAcquisitionSources` или поле равно `null`, ограничений нет и она может участвовать в любом таком пуле.

Например:

```json
{
  "templateId": "pumpkin-soup"
}
```

может быть выбрана и квестом, и экспедицией.

Если задан белый список:

```json
{
  "templateId": "secret-recipe",
  "allowedAcquisitionSources": [
    "QUEST_REWARD"
  ]
}
```

этот рецепт можно выдать через квест, но нельзя выдать как награду за экспедицию.

Чтобы разрешить оба способа:

```json
{
  "templateId": "secret-recipe",
  "allowedAcquisitionSources": [
    "QUEST_REWARD",
    "EXPEDITION_REWARD"
  ]
}
```

Пустой `allowedAcquisitionSources` означает, что сущность нельзя получить ни одним стандартным способом:

```json
{
  "allowedAcquisitionSources": []
}
```

Подробнее см. в разделе [«Источники получения»](README.md#acquisition-sources).

## Пример полного `lootBundle`

```json
{
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
      "amount": 20
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
}
```

Не требуется перечислять все категории. Обычно `lootBundle` должен содержать только те пулы, которые действительно нужны данной награде.

## Проверка

Для каждого `lootBundle` должны выполняться следующие правила:

* `lootBundle` содержит хотя бы один пул;
* `templateIds` либо отсутствует, либо равно `null`, либо является непустым списком;
* все указанные `templateIds` существуют в соответствующей категории;
* один `templateId` не повторяется внутри пула;
* каждый выбранный шаблон разрешено получать через текущий источник;
* `amount` обычного пула является положительным целым числом;
* `amount` не превышает количество доступных кандидатов;
* `dropChance` находится в диапазоне от `0` до `1`;
* `amount` для `diamondLoot` является положительным целым числом;
* каждый присутствующий пул разыгрывается независимо от остальных.
