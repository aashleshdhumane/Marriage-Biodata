@echo off
REM ====== config ======
set CONTENT=my_biodata.yaml
set OUTPUT=my_biodata.png
set SIZE=1240x1754
set PY=python
REM ====================

if not exist "%CONTENT%" (
  echo ERROR: "%CONTENT%" not found. Make sure your YAML file exists.
  exit /b 1
)

%PY% generate_biodata.py --content "%CONTENT%" --output "%OUTPUT%" --size %SIZE%
if errorlevel 1 (
  echo.
  echo Failed to generate biodata. Check error messages above.
  exit /b 1
)

echo.
echo Done! Output: %OUTPUT%
pause
