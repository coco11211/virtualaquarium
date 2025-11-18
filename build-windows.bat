@echo off
echo ========================================
echo Virtual Aquarium - Build Script
echo ========================================
echo.

echo Checking for Node.js...
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo Node.js found!
node --version
echo.

echo Installing dependencies...
call npm install
call npm install @rollup/rollup-linux-x64-gnu
echo.

echo Building production version...
call npm run build
echo.

if %ERRORLEVEL% EQU 0 (
    echo ========================================
    echo Build successful!
    echo ========================================
    echo.
    echo The built files are in the 'dist' folder
    echo To preview: npm run preview
    echo.
) else (
    echo ========================================
    echo Build failed!
    echo ========================================
    echo Please check the error messages above
    echo.
)

pause
