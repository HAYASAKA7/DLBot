@echo off
REM DLBot Setup Script for Windows
REM Installs all required dependencies and sets up the application

setlocal enabledelayedexpansion

cls
echo.
echo ========================================
echo     DLBot - Setup Installation
echo ========================================
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: Failed to upgrade pip
)
echo.

REM Define dependencies
set DEPENDENCIES=yt-dlp PyQt5 requests

REM Check and install missing packages
echo Checking and installing required packages...
echo.

for %%P in (%DEPENDENCIES%) do (
    echo Checking %%P...
    python -m pip show %%P >nul 2>&1
    if errorlevel 1 (
        echo   %%P not found. Installing...
        python -m pip install %%P
        if errorlevel 1 (
            echo   ERROR: Failed to install %%P
            pause
            exit /b 1
        )
        echo   Successfully installed %%P
    ) else (
        echo   %%P already installed
    )
)
echo.

REM Create necessary directories
echo Creating necessary directories...
if not exist "config" mkdir config
if not exist "downloads" mkdir downloads
if not exist "logs" mkdir logs
echo Directories created.
echo.

REM Display completion message
echo.
echo ========================================
echo     Setup Completed Successfully!
echo ========================================
echo.
echo To run DLBot, use one of these commands:
echo.
echo   From Command Prompt:
echo     python main.py
echo.
echo   Or double-click:
echo     run.bat
echo.
echo.
pause
