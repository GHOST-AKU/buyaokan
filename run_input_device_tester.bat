@echo off
setlocal
set PYTHON_EXE=C:\ProgramData\Anaconda3\python.exe

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" "%~dp0input_device_tester.py"
) else (
    python "%~dp0input_device_tester.py"
)
