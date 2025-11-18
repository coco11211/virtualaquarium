# Virtual Aquarium - Fish Breeding Simulator

A beautiful, feature-rich fish breeding simulation game with realistic Mendelian genetics, built with Electron, React, and TypeScript.

## Features

### 🐟 Genetics System
- **Mendelian Inheritance**: Realistic genetic inheritance with dominant and recessive alleles
- **Multiple Traits**: Body color, fin type, pattern, size, and behavior
- **Secondary Colors**: Complex pattern inheritance
- **Trait Probabilities**: Calculate breeding outcomes before breeding

### 🎨 Beautiful UI/UX
- Modern, polished interface with Figma-level design
- Smooth animations and transitions using Framer Motion
- Interactive aquarium view with swimming fish
- Real-time statistics and charts

### 🔬 Breeding Lab
- Select breeding pairs from your collection
- View trait probability calculations
- Generate multiple offspring per breeding
- Track family lineages and ancestry

### 📊 Statistics Dashboard
- Comprehensive charts and graphs
- Color, fin, pattern, and generation distributions
- Achievement tracking system
- Historical breeding statistics

### 🏪 Fish Marketplace
- Purchase unique fish with various traits
- Dynamic pricing based on rarity
- Refreshable stock
- Currency system

### 💾 Save System
- Automatic save to localStorage
- Persistent game state across sessions
- Export/import functionality

### 🏆 Achievements
- 10+ achievements to unlock
- Track rare fish discoveries
- Generation milestones
- Collection completionist goals

## Installation & Running

### Prerequisites
- Node.js 18+ installed
- npm or yarn package manager

### Development Mode

1. Install dependencies:
```bash
npm install
```

2. Run in development mode:
```bash
npm run electron:dev
```

This will start both the Vite dev server and Electron.

### Build for Windows

Build the Windows executable:
```bash
npm run electron:build:win
```

The installer will be created in the `release` directory.

### Running the Built App

After building, you can find the installer in:
```
release/Virtual Aquarium Setup X.X.X.exe
```

Run the installer to install the app on your Windows 11 PC.

## How to Play

### Getting Started
1. Launch the application
2. You'll start with 3 starter fish and 1000 currency
3. Visit the Marketplace to purchase more fish

### Breeding Fish
1. Click the "Breed" button in the header
2. Select a mother fish (♀)
3. Select a father fish (♂)
4. Optionally view trait probabilities
5. Click "Breed" to create offspring
6. Choose which offspring to keep

### Understanding Genetics
- Each fish has genes for 5 traits: color, fins, pattern, size, and behavior
- Each gene has 2 alleles: dominant (D) or recessive (R)
- Offspring inherit one allele from each parent
- Dominant alleles express over recessive alleles
- Create rare combinations through selective breeding

### Trait Dominance Hierarchy

**Body Colors** (highest to lowest dominance):
- Black > Red > Orange > Yellow > Pink > Purple > Blue > Teal > Green > White

**Fin Types**:
- Crown > Veil > Double > Split > Long > Normal

**Patterns**:
- Koi > Marble > Gradient > Striped > Spotted > Solid

**Sizes**:
- Large > Medium > Small

**Behaviors**:
- Aggressive > Playful > Active > Peaceful > Shy

### Tips for Success
- Breed high-value fish to create even more valuable offspring
- Collect all colors and fin types to unlock achievements
- Watch the aquarium view to see your fish swim!
- Track family lineages to understand inheritance patterns
- Rare traits (like secondary colors) significantly increase fish value

## Project Structure

```
virtualaquarium/
├── electron/           # Electron main process
│   └── main.js
├── src/
│   ├── components/     # React components
│   │   ├── Aquarium.tsx
│   │   ├── BreedingLab.tsx
│   │   ├── Collection.tsx
│   │   ├── FishCard.tsx
│   │   ├── FishDetails.tsx
│   │   ├── FishVisual.tsx
│   │   ├── Marketplace.tsx
│   │   └── Statistics.tsx
│   ├── engine/         # Game logic
│   │   └── genetics.ts
│   ├── store/          # State management
│   │   └── gameStore.ts
│   ├── types/          # TypeScript types
│   │   └── index.ts
│   ├── App.tsx         # Main app component
│   ├── main.tsx        # React entry point
│   └── index.css       # Global styles
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Technologies Used

- **Electron**: Desktop application framework
- **React 18**: UI framework
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool
- **Tailwind CSS**: Utility-first CSS framework
- **Framer Motion**: Animation library
- **Zustand**: State management
- **Recharts**: Data visualization
- **Lucide React**: Icon library

## Genetics Implementation

The genetics engine implements a simplified Mendelian inheritance model:

1. **Gene Structure**: Each trait has 2 alleles (dominant/recessive)
2. **Inheritance**: Offspring randomly inherit one allele from each parent
3. **Expression**: Phenotype is determined by allele combination and trait hierarchy
4. **Mutations**: Small chance of new secondary colors appearing

## Performance

- Smooth 60 FPS animations
- Optimized re-renders with React
- Efficient state management
- Handles 100+ fish without performance issues

## Future Enhancements

Potential features for future versions:
- Online marketplace and trading
- Seasonal events with limited-edition fish
- Tank decorations and customization
- More complex genetic traits
- Fish competitions and shows
- Breeding goals and challenges

## License

MIT License - Feel free to modify and distribute

## Credits

Developed with love for fish breeding enthusiasts and genetics learners!

---

Enjoy breeding beautiful fish! 🐟✨
