@echo off
REM ============================================
REM Environment Setup Script for Windows
REM ============================================
REM Quickly sets up .env file for your environment
REM
REM Usage: setup_env.bat

setlocal enabledelayedexpansion

echo.
echo ================================
echo AgroHub Environment Setup
echo ================================
echo.

REM Check if .env already exists
if exist ".env" (
    echo WARNING: .env file already exists!
    set /p overwrite="Do you want to overwrite it? (y/n): "
    if /i not "!overwrite!"=="y" (
        echo Setup cancelled.
        exit /b 1
    )
)

REM Ask which environment
echo.
echo Which environment are you setting up?
echo 1) Development (local, with console emails)
echo 2) Docker (production-ready, for Docker/staging/production)
echo 3) Custom (.env.example - manually edit)
echo.
set /p env_choice="Select environment (1-3): "

if "%env_choice%"=="1" (
    set ENV_FILE=.env.development
    set ENV_NAME=Development
) else if "%env_choice%"=="2" (
    set ENV_FILE=.env.docker.example
    set ENV_NAME=Docker
) else if "%env_choice%"=="3" (
    set ENV_FILE=.env.example
    set ENV_NAME=Custom
) else (
    echo Invalid choice.
    exit /b 1
)

echo.
echo Setting up %ENV_NAME% environment

REM Copy environment file
if not exist "%ENV_FILE%" (
    echo Error: %ENV_FILE% not found!
    exit /b 1
)

copy "%ENV_FILE%" ".env" >nul
echo [OK] Copied %ENV_FILE% to .env

REM For production/staging, offer to generate SECRET_KEY
if not "%env_choice%"=="1" (
    echo.
    set /p gen_key="Do you want to generate a new SECRET_KEY? (y/n): "
    if /i "!gen_key!"=="y" (
        for /f "delims=" %%i in ('python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"') do set SECRET_KEY=%%i
        
        REM Replace SECRET_KEY in .env using PowerShell
        powershell -Command "(Get-Content .env) -replace 'SECRET_KEY=.*', 'SECRET_KEY=!SECRET_KEY!' | Set-Content .env"
        
        echo [OK] Generated and set SECRET_KEY
    )
)

REM Show next steps
echo.
echo ================================
echo Environment setup complete!
echo ================================
echo.
echo Next steps:
echo.

if "%env_choice%"=="1" (
    echo 1. Review .env file:
    echo    notepad .env
    echo.
    echo 2. Start database and Redis:
    echo    docker-compose up -d db redis
    echo.
    echo 3. Run migrations:
    echo    python manage.py migrate
    echo.
    echo 4. Create admin user (optional^):
    echo    python manage.py createsuperuser
    echo.
    echo 5. Start development server:
    echo    python manage.py runserver
    echo.
    echo 6. Visit http://localhost:8000
) else if "%env_choice%"=="2" (
    echo 1. Edit .env with your credentials:
    echo    notepad .env
    echo.
    echo 2. Update these fields:
    echo    - SECRET_KEY
    echo    - ALLOWED_HOSTS
    echo    - DB_PASSWORD
    echo    - Database connection
    echo    - Email configuration
    echo.
    echo 3. Start Docker:
    echo    docker-compose up --build -d
) else if "%env_choice%"=="3" (
    echo 1. Edit .env.example with your values:
    echo    notepad .env
    echo.
    echo 2. Configure based on your needs
    echo    See ENVIRONMENT_SETUP.md for documentation
    echo.
    echo 3. Run migrations and deploy
)

echo.
echo Documentation:
echo   - Read ENV_SETUP.md for detailed guide
echo   - Read ENV_QUICK_REFERENCE.md for comparison
echo   - Check .env.example for all variables
echo.

