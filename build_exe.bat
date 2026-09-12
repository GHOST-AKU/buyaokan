@echo off
setlocal

set PYTHON_EXE=C:\ProgramData\Anaconda3\python.exe
set APP_NAME=InputDeviceTester
set PROJECT_DIR=%~dp0
set SCRIPT_PATH=%PROJECT_DIR%input_device_tester.py
set DIST_DIR=%PROJECT_DIR%release
set BUILD_DIR=%PROJECT_DIR%build
set SPEC_DIR=%PROJECT_DIR%

if exist "%PYTHON_EXE%" (
    set PYTHON_CMD=%PYTHON_EXE%
) else (
    set PYTHON_CMD=python
)

if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%SPEC_DIR%\%APP_NAME%.spec" del /q "%SPEC_DIR%\%APP_NAME%.spec"

"%PYTHON_CMD%" -m PyInstaller --noconfirm --clean --onefile --windowed --name %APP_NAME% --distpath "%DIST_DIR%" --workpath "%BUILD_DIR%" --specpath "%SPEC_DIR%" "%SCRIPT_PATH%"

if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

echo.
echo Build finished:
echo %DIST_DIR%\%APP_NAME%.exe
