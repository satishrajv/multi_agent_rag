@echo off
echo ============================================
echo   Jenkins Local Setup for Windows
echo ============================================
echo.

:: Check if Docker is running
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

:: Navigate to jenkins directory
cd /d "%~dp0"

echo Starting Jenkins container...
docker-compose up -d

echo.
echo Waiting for Jenkins to start (this may take 1-2 minutes)...
timeout /t 30 /nobreak >nul

:: Get initial admin password
echo.
echo ============================================
echo   Jenkins Setup Information
echo ============================================
echo.
echo Jenkins URL: http://localhost:8080
echo.
echo Initial Admin Password:
echo ----------------------------------------
docker exec jenkins_local cat /var/jenkins_home/secrets/initialAdminPassword
echo ----------------------------------------
echo.
echo NEXT STEPS:
echo 1. Open http://localhost:8080 in your browser
echo 2. Copy the password shown above
echo 3. Follow the setup wizard
echo 4. Install suggested plugins
echo 5. Create your admin user
echo.
echo To view Jenkins logs:    docker logs -f jenkins_local
echo To stop Jenkins:         docker-compose down
echo To restart Jenkins:      docker-compose restart
echo.
pause
