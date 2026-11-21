@echo off
setlocal
rem Read-and-write test of the game's file formats. Only reads the game files.
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
echo === Edit check ===
%PY% tests\edit_check.py "%ROMFS%"
echo.
echo === Event flow add check ===
%PY% tests\evfl_add_check.py "%ROMFS%"
echo.
echo === Checking chest check ===
%PY% tests\chest_check.py "%ROMFS%"
echo.
echo === Ocarina fix check ===
%PY% tests\ocarina_fix_check.py "%ROMFS%"
echo.
echo === Turning items check ===
%PY% tests\ground_prog_check.py "%ROMFS%"
echo.
echo === Ground lift check ===
%PY% tests\ground_lift_check.py "%ROMFS%"
echo.
echo === Three-level chest check ===
%PY% tests\three_chest_check.py "%ROMFS%"
echo.
echo === Progressive gift check ===
%PY% tests\gift_check.py "%ROMFS%"
echo.
echo === Cutscene gift check ===
%PY% tests\saria_check.py "%ROMFS%"
echo.
echo === Pairs on rocks, bushes and scrubs check ===
%PY% tests\pairs_more_check.py "%ROMFS%"
echo.
echo === Round-trip test (Event, RSDB, Mals, GameData, Pack, System, AI, Logic, Sequence) ===
%PY% tests\roundtrip.py "%ROMFS%" Event RSDB Mals GameData Pack System AI Logic Sequence --report report.txt
echo.
echo The full report is in report.txt
pause
