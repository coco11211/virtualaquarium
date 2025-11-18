# Quick Start Guide - Virtual Aquarium

## For Windows 11 Users

### Option 1: Run from Source (Recommended for Development)

1. **Install Node.js** (if not already installed)
   - Download from: https://nodejs.org/
   - Choose the LTS version (18.x or higher)
   - Run the installer and follow the prompts

2. **Open Terminal/PowerShell**
   - Press `Win + X` and select "Windows PowerShell" or "Terminal"
   - Navigate to the project folder:
     ```powershell
     cd path\to\virtualaquarium
     ```

3. **Install Dependencies**
   ```powershell
   npm install
   ```
   This may take a few minutes.

4. **Run the Application**
   ```powershell
   npm run electron:dev
   ```
   The app will open automatically!

### Option 2: Build and Install (For End Users)

1. **Build the Windows Installer**
   ```powershell
   npm install
   npm run electron:build:win
   ```
   This will create an installer in the `release` folder.

2. **Install the App**
   - Navigate to the `release` folder
   - Double-click the `.exe` installer
   - Follow the installation wizard
   - Launch "Virtual Aquarium" from your Start Menu

## Troubleshooting

### If you get "npm command not found"
- Node.js is not installed or not in PATH
- Install Node.js from https://nodejs.org/

### If the build fails
- Make sure you have at least 2GB of free disk space
- Try running `npm install` again
- Check that you're using Node.js 18 or higher: `node --version`

### If Electron doesn't start
- Check that port 5173 is not in use
- Try closing other applications
- Restart your computer and try again

## First Time Playing

1. **Start**: You begin with 3 starter fish and 1000 currency
2. **Explore**: Click on the navigation tabs to explore different sections
3. **Buy Fish**: Visit the Marketplace to purchase more fish
4. **Breed**: Click the "Breed" button to create offspring
5. **Collect**: Try to collect all colors and fin types!

## Controls

- **Click** on fish in the aquarium to view details
- **Breed** button in header to open breeding lab
- **Search** and **Filter** in Collection view
- **Refresh Stock** in Marketplace for new fish

## Tips

- Breed high-value fish for better offspring
- Check trait probabilities before breeding
- Unlock achievements by reaching milestones
- Save is automatic - your progress is always preserved!

Enjoy your aquarium! 🐟
