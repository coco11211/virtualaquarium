import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Fish,
  Heart,
  TrendingUp,
  ShoppingCart,
  BarChart3,
  Droplets,
  Settings,
} from 'lucide-react';
import type { Fish as FishType } from './types';
import { Aquarium } from './components/Aquarium';
import { Collection } from './components/Collection';
import { BreedingLab } from './components/BreedingLab';
import { FishDetails } from './components/FishDetails';
import { Statistics } from './components/Statistics';
import { Marketplace } from './components/Marketplace';
import { useGameStore } from './store/gameStore';

type View = 'aquarium' | 'collection' | 'statistics' | 'marketplace';

function App() {
  const [currentView, setCurrentView] = useState<View>('aquarium');
  const [showBreeding, setShowBreeding] = useState(false);
  const [selectedFish, setSelectedFish] = useState<FishType | null>(null);
  const [showSettings, setShowSettings] = useState(false);

  const { fish, currency, ageFish, resetGame } = useGameStore();

  // Age fish every second (for demo purposes - in production would be slower)
  useEffect(() => {
    const interval = setInterval(() => {
      ageFish();
    }, 60000); // Every minute

    return () => clearInterval(interval);
  }, [ageFish]);

  const navigation = [
    { id: 'aquarium' as View, label: 'Aquarium', icon: Droplets },
    { id: 'collection' as View, label: 'Collection', icon: Fish },
    { id: 'statistics' as View, label: 'Statistics', icon: BarChart3 },
    { id: 'marketplace' as View, label: 'Market', icon: ShoppingCart },
  ];

  const handleResetGame = () => {
    if (confirm('Are you sure you want to reset your game? This cannot be undone.')) {
      resetGame();
      setShowSettings(false);
      setCurrentView('aquarium');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-ocean-950 via-ocean-900 to-ocean-950 text-white">
      {/* Header */}
      <header className="bg-ocean-900/80 backdrop-blur-sm border-b border-ocean-700 sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl">
                <Fish className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  Virtual Aquarium
                </h1>
                <p className="text-xs text-gray-400">Fish Breeding Simulator</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="bg-ocean-800 px-4 py-2 rounded-lg border border-ocean-600">
                <div className="flex items-center gap-2">
                  <Fish className="w-4 h-4 text-blue-400" />
                  <span className="text-sm font-medium">{fish.length} Fish</span>
                </div>
              </div>

              <div className="bg-gradient-to-r from-yellow-500/20 to-orange-500/20 px-4 py-2 rounded-lg border border-yellow-500/30">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-yellow-500" />
                  <span className="text-sm font-bold text-yellow-500">{currency}</span>
                </div>
              </div>

              <button
                onClick={() => setShowBreeding(true)}
                className="px-4 py-2 bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600 rounded-lg font-medium flex items-center gap-2 transition-all transform hover:scale-105"
              >
                <Heart className="w-4 h-4" />
                Breed
              </button>

              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 hover:bg-ocean-700 rounded-lg transition-colors"
              >
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Settings Dropdown */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-20 right-4 bg-ocean-800 rounded-lg border border-ocean-600 p-4 z-50 min-w-[200px]"
          >
            <div className="space-y-2">
              <button
                onClick={handleResetGame}
                className="w-full px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-sm transition-colors"
              >
                Reset Game
              </button>
              <div className="pt-2 border-t border-ocean-700 text-xs text-gray-500">
                Version 1.0.0
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Navigation */}
      <nav className="bg-ocean-900/50 border-b border-ocean-700">
        <div className="container mx-auto px-4">
          <div className="flex gap-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = currentView === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentView(item.id)}
                  className={`px-6 py-3 flex items-center gap-2 border-b-2 transition-all ${
                    isActive
                      ? 'border-blue-500 text-blue-400 bg-ocean-800/50'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:bg-ocean-800/30'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="font-medium">{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentView}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
          >
            {currentView === 'aquarium' && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-blue-500/20 to-cyan-500/20 rounded-xl p-6 border border-blue-500/30">
                  <h2 className="text-2xl font-bold mb-2">Welcome to Your Aquarium</h2>
                  <p className="text-gray-300">
                    Watch your fish swim peacefully. Click on them to view details or breed them to create
                    new offspring with unique traits!
                  </p>
                </div>

                <div className="bg-ocean-900 rounded-2xl border-2 border-ocean-700 overflow-hidden">
                  <div style={{ height: '600px' }}>
                    <Aquarium
                      fish={fish}
                      onFishClick={setSelectedFish}
                      maxDisplay={12}
                    />
                  </div>
                </div>

                {fish.length === 0 && (
                  <div className="text-center bg-ocean-800 rounded-xl p-8 border border-ocean-600">
                    <Fish className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-xl font-bold mb-2">Your aquarium is empty</h3>
                    <p className="text-gray-400 mb-4">
                      Visit the marketplace to purchase your first fish!
                    </p>
                    <button
                      onClick={() => setCurrentView('marketplace')}
                      className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-lg font-medium transition-all"
                    >
                      Go to Marketplace
                    </button>
                  </div>
                )}
              </div>
            )}

            {currentView === 'collection' && <Collection onFishClick={setSelectedFish} />}
            {currentView === 'statistics' && <Statistics />}
            {currentView === 'marketplace' && <Marketplace />}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Modals */}
      <AnimatePresence>
        {showBreeding && <BreedingLab onClose={() => setShowBreeding(false)} />}
        {selectedFish && <FishDetails fish={selectedFish} onClose={() => setSelectedFish(null)} />}
      </AnimatePresence>

      {/* Footer */}
      <footer className="mt-12 py-6 border-t border-ocean-700 bg-ocean-900/50">
        <div className="container mx-auto px-4 text-center text-sm text-gray-500">
          <p>Virtual Aquarium - Fish Breeding Simulator with Genetic Inheritance</p>
          <p className="mt-1">Create unique fish through selective breeding and discover rare traits!</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
