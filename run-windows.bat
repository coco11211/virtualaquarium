@echo off
echo ========================================
echo Virtual Aquarium - Fish Breeding Simulator
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

echo Checking for dependencies...
if not exist "node_modules\" (
    echo Installing dependencies... This may take a few minutes.
    call npm install
    call npm install @rollup/rollup-linux-x64-gnu
    echo.
)

echo Starting Virtual Aquarium...
echo The app will open in your web browser at http://localhost:5173
echo Press Ctrl+C to stop the server
echo.

call npm run dev

pause
