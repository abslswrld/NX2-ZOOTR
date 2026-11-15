@echo off
setlocal
rem Read-and-write test of the game's file formats. Only reads the game files.
set "ROMFS=C:\Users\4bsol\Games\Longshot\nightly-130-0caf0618\romfs"
if not "%~1"=="" set "ROMFS=%~1"
cd /d "%~dp0"
where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
echo Game files: %ROMFS%
echo.
echo === Edit check ===
%PY% tests\edit_check.py "%ROMFS%"
echo.
echo === Round-trip test (Event, RSDB, Mals, GameData, Pack, System) ===
%PY% tests\roundtrip.py "%ROMFS%" Event RSDB Mals GameData Pack System --report report.txt
echo.
echo The full report is in report.txt
pause
