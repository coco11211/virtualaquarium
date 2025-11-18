# Windows 11 Setup Guide

## Complete Installation Instructions

This guide will help you set up and run Virtual Aquarium on your Windows 11 PC.

## Prerequisites

### 1. Install Node.js

1. Download Node.js from: https://nodejs.org/
2. Choose the **LTS version** (Long Term Support) - version 18.x or higher
3. Run the installer:
   - Check "Automatically install necessary tools" if prompted
   - Accept all defaults
4. Verify installation:
   ```powershell
   node --version
   npm --version
   ```

## Installation Methods

### Method 1: Development Mode (Fastest - Recommended)

This runs the app directly in development mode with hot-reload.

1. **Open PowerShell or Terminal**
   - Press `Win + X`
   - Select "Windows PowerShell" or "Terminal"

2. **Navigate to project folder**
   ```powershell
   cd path\to\virtualaquarium
   ```

3. **Install dependencies**
   ```powershell
   npm install
   npm install @rollup/rollup-linux-x64-gnu
   ```

4. **Run the web version**
   ```powershell
   npm run dev
   ```

   The app will open in your default web browser at http://localhost:5173

5. **To run as Electron desktop app** (optional)
   ```powershell
   npm install --save-dev electron concurrently wait-on electron-builder
   npm run electron:dev
   ```

### Method 2: Build Standalone Executable

Build a Windows installer for distribution.

1. **Install all dependencies including Electron**
   ```powershell
   npm install
   npm install --save-dev electron concurrently wait-on electron-builder
   ```

2. **Build the Windows installer**
   ```powershell
   npm run electron:build:win
   ```

3. **Find the installer**
   - Look in the `release` folder
   - Run the `.exe` installer
   - Install to your preferred location
   - Launch from Start Menu

### Method 3: Web Version Only (Lightest)

If you just want to run it in the browser without Electron:

1. **Install core dependencies**
   ```powershell
   npm install --no-optional
   npm install @rollup/rollup-linux-x64-gnu
   ```

2. **Build the production version**
   ```powershell
   npm run build
   ```

3. **Preview the build**
   ```powershell
   npm run preview
   ```

4. **Deploy the `dist` folder**
   - The `dist` folder contains the complete web app
   - Can be served by any static web server
   - Or open `dist/index.html` directly in browser

## Troubleshooting

### "npm is not recognized"
- Node.js is not installed or not in PATH
- Reinstall Node.js and make sure to check "Add to PATH"
- Restart your terminal/PowerShell

### "Cannot find module" errors
```powershell
# Clean install
rm -rf node_modules package-lock.json
npm install
npm install @rollup/rollup-linux-x64-gnu
```

### Electron download fails (403 error)
- This is a network/firewall issue
- Use the web version instead (Method 3)
- Or install Electron later when you have better network access

### Port 5173 already in use
```powershell
# Kill the process using the port or use a different port
npm run dev -- --port 3000
```

### Build errors
1. Make sure you have at least 2GB free disk space
2. Check Node.js version: `node --version` (should be 18+)
3. Try cleaning and reinstalling:
   ```powershell
   rm -rf node_modules package-lock.json dist
   npm install
   ```

### TypeScript errors during build
The codebase has been tested and builds successfully. If you encounter TypeScript errors:
```powershell
npm run build -- --force
```

## Performance Tips

1. **Close unused applications** - The app runs best with available RAM
2. **Use a modern browser** - Chrome, Edge, or Firefox for best performance
3. **Hardware acceleration** - Enable GPU acceleration in browser settings

## Running the App

### Browser Version
- Navigate to http://localhost:5173 (or the port shown in terminal)
- Works in Chrome, Edge, Firefox, Safari

### Desktop Version
- Electron app will open automatically
- Native desktop experience
- Runs independently of browser

## File Locations

### Development Mode
- Source code: `src/`
- Compiled output: `dist/`
- Game saves: Browser localStorage

### Installed App
- Installation: `C:\Program Files\Virtual Aquarium\` (or chosen location)
- Game saves: Browser localStorage (persists across sessions)

## Updating the App

To update to a new version:

1. Download new source code
2. Navigate to folder in PowerShell
3. Run:
   ```powershell
   npm install
   npm run build
   ```

## Uninstalling

### Web Version
Simply delete the folder

### Installed Version
- Windows Settings → Apps → Virtual Aquarium → Uninstall
- Or use the uninstaller in the installation folder

## Getting Help

### Common Issues
1. **Fish not moving** - Refresh the page, animations may have paused
2. **Can't breed** - Need to select both mother and father fish
3. **Lost progress** - Check localStorage wasn't cleared by browser
4. **Graphics issues** - Try a different browser or update graphics drivers

### Reset Game
Click Settings (gear icon) → Reset Game

## Features Overview

- ✨ Breed fish with genetic inheritance
- 🎨 Beautiful UI with smooth animations
- 📊 Comprehensive statistics and charts
- 🏪 Marketplace to buy new fish
- 🏆 Achievement system
- 💾 Automatic save system
- 🌈 10 body colors, 6 fin types, 6 patterns

## System Requirements

### Minimum
- Windows 11
- 4GB RAM
- Modern web browser (Chrome, Edge, Firefox)
- Node.js 18+

### Recommended
- 8GB+ RAM
- Dedicated graphics card
- Latest browser version
- Fast SSD storage

## Next Steps

After installation:
1. Read QUICKSTART.md for gameplay instructions
2. Read README.md for detailed features
3. Start breeding fish!

Enjoy your Virtual Aquarium! 🐟✨
