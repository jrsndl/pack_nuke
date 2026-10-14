@echo off
rem ---------------------------------------------------------------------------
rem  Build Pack Nuke executables with PyInstaller (via uv, no venv needed).
rem
rem    dist\PackNuke\PackNuke.exe       GUI (windowed, onedir: fast start-up)
rem    dist\PackNuke\PackNukeCLI.exe    command line (console, single file)
rem    dist\PackNuke\pack_nuke.py       farm / local packing entry (run by Nuke)
rem    dist\PackNuke\packnuke\          Python code used by pack_nuke.py in Nuke
rem    dist\PackNuke\settings.json      default settings (when no preset is loaded)
rem
rem  settings.ini, presets and pack_nuke_gui.log live next to the exe.
rem  Usage:  build_exe.bat            build (runs the tests first)
rem          build_exe.bat notest     build without running the tests
rem ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0"

set "NAME=PackNuke"
set "PYVER=3.11"
set "ROOT=%~dp0"
set "DIST=%ROOT%dist\%NAME%"
set "WORK=%ROOT%build"

where uv >nul 2>nul
if errorlevel 1 (
    echo ERROR: uv was not found on PATH. Install it from https://docs.astral.sh/uv/
    exit /b 1
)

if /i not "%~1"=="notest" (
    echo.
    echo === Running tests
    uv run --no-project --python %PYVER% python -m unittest discover -s tests -q
    if errorlevel 1 goto :fail
)

echo.
echo === Cleaning
if exist "%WORK%" rmdir /s /q "%WORK%"
if exist "%DIST%" rmdir /s /q "%DIST%"

echo.
echo === Building GUI: %NAME%.exe
uv run --no-project --python %PYVER% --with pyinstaller --with PySide6-Essentials --with pillow ^
    pyinstaller --noconfirm --clean --log-level WARN ^
    --windowed --name %NAME% ^
    --icon "%ROOT%images\folder.png" ^
    --contents-directory _internal ^
    --distpath "%ROOT%dist" --workpath "%WORK%\gui" --specpath "%WORK%" ^
    --paths "%ROOT%." ^
    --hidden-import ui_images_rc ^
    --add-data "%ROOT%packnuke\gui\style.qss;packnuke\gui" ^
    "%ROOT%pack_nuke_gui.py"
if errorlevel 1 goto :fail

echo.
echo === Building command line: %NAME%CLI.exe
uv run --no-project --python %PYVER% --with pyinstaller ^
    pyinstaller --noconfirm --clean --log-level WARN ^
    --onefile --console --name %NAME%CLI ^
    --distpath "%DIST%" --workpath "%WORK%\cli" --specpath "%WORK%" ^
    --paths "%ROOT%." ^
    --exclude-module PySide6 ^
    "%ROOT%pack_nuke_cli.py"
if errorlevel 1 goto :fail

echo.
echo === Copying farm files and defaults
copy /y "%ROOT%pack_nuke.py" "%DIST%\" >nul || goto :fail
copy /y "%ROOT%settings.json" "%DIST%\" >nul || goto :fail
copy /y "%ROOT%README.md" "%DIST%\" >nul
rem the packnuke code Nuke imports for packing (the GUI part is inside the exe)
robocopy "%ROOT%packnuke" "%DIST%\packnuke" /E /XD __pycache__ gui /XF *.pyc /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto :fail
rem an empty settings.ini so the exe does not pick up anything from the dev checkout
if not exist "%DIST%\settings.ini" (
    > "%DIST%\settings.ini" echo [General]
    >> "%DIST%\settings.ini" echo presets_folder=
)

echo.
echo === Done: %DIST%
dir /b "%DIST%"
echo.
echo Deploy the whole folder. For the farm, point settings deadline_python to
echo   ^<deployed folder^>\pack_nuke.py
endlocal
exit /b 0

:fail
echo.
echo *** BUILD FAILED ***
endlocal
exit /b 1
