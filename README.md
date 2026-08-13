# Owl Game Catalog

Этот репозиторий содержит исходные данные игрового каталога Owl Game.

Каталог хранится в виде отдельных JSON-файлов. Сборочный скрипт проверяет их и объединяет в единый `catalog-release.json`, который затем импортируется backend.

## Для автора игрового контента

1. Создайте ветку от `develop`.

2. Добавьте или измените JSON-файлы внутри `catalog/`.

3. Не добавляйте изображения непосредственно в Git-репозиторий.

4. Если изображения ещё нет в основном хранилище, укажите временный публичный `sourceImageUrl`.

5. Запустите локальную проверку каталога.

   Для проверки требуется Python.

   В Windows из корня репозитория выполните:

   ```bat
   .\scripts\validate-catalog.bat
   ```

   В Linux выполните:

   ```bash
   sh ./scripts/validate-catalog.sh
   ```

   Если `validate-catalog.sh` имеет право на выполнение, его также можно запустить напрямую:

   ```bash
   ./scripts/validate-catalog.sh
   ```

   Если проверка прошла успешно, в конце будет выведено:

   ```text
   Catalog validation OK
   ```

6. Откройте pull request в `develop`.

Начните с [общей инструкции для авторов каталога](catalog/README.md), а затем прочитайте `README.md` в нужной директории:

* [животные](catalog/animals/README.md);
* [здания](catalog/buildings/README.md);
* [враги](catalog/enemies/README.md);
* [мебель](catalog/furniture/README.md);
* [предметы для сада](catalog/garden-items/README.md);
* [локации](catalog/locations/README.md);
* [карты](catalog/maps/README.md);
* [медали](catalog/medals/README.md);
* [растения](catalog/plants/README.md);
* [квесты](catalog/quests/README.md);
* [рецепты](catalog/recipes/README.md);
* [припасы](catalog/supplies/README.md).

## Для сопровождающего репозитория

Правила проверки, переноса изображений в S3, слияния в `main` и публикации релиза описаны в [CONTRIBUTING.md](CONTRIBUTING.md).

## Что не следует коммитить

В репозиторий не следует добавлять:

* изображения и другие тяжёлые бинарные файлы;
* собранный вручную `catalog-release.json`;
* MongoDB-поля `id` и `releaseId`;
* UUID конкретных игровых объектов пользователей;
* секреты, ключи доступа и адреса внутренних сервисов.
