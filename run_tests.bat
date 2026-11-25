@echo off
setlocal
rem Every test script, several at a time (tests\run_all.py has the list). Only reads the game files.
rem The game's romfs folder comes from, in order: the first argument, the ROMFS environment variable,
rem or romfs_path.txt next to this file (one line; not uploaded to GitHub). Otherwise it asks.
cd /d "%~dp0"
if not "%~1"=="" set "ROMFS=%~1"
if "%ROMFS%"=="" if exist romfs_path.txt set /p ROMFS=<romfs_path.txt
if "%ROMFS%"=="" set /p ROMFS=Path to the game's romfs folder:
if "%ROMFS%"=="" (echo No romfs folder given.& pause & exit /b 1)
where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
echo Game files: %ROMFS%
echo.
%PY% tests\run_all.py "%ROMFS%"
echo.
echo Each script's whole output is in test_logs\, the round-trip test's full report in report.txt
pause
