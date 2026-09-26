@echo off
python -m owl_catalog_tools ^
  --catalog-dir catalog ^
  --output build\catalog-release.json ^
  --version local ^
  --commit-sha local ^
  --locale ru ^
  --require-image-keys ^
  --validate-s3-images ^
  --image-base-url "https://s3.regru.cloud/owlgame/"

if errorlevel 1 exit /b 1

echo.
echo Catalog strict validation OK
