@echo off
python -m py_compile scripts\build_catalog.py
if errorlevel 1 exit /b 1

python scripts\build_catalog.py ^
  --catalog-dir catalog ^
  --output build\catalog-release.json ^
  --version local ^
  --commit-sha local ^
  --require-image-keys

if errorlevel 1 exit /b 1

echo.
echo Catalog strict validation OK
