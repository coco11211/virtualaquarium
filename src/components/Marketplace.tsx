import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ShoppingCart, Sparkles, RefreshCw, TrendingUp } from 'lucide-react';
import type { Fish } from '../types';
import { generateStarterFish } from '../engine/genetics';
import { FishCard } from './FishCard';
import { useGameStore } from '../store/gameStore';

export function Marketplace() {
  const { addFish, spendCurrency, currency } = useGameStore();
  const [availableFish, setAvailableFish] = useState<(Fish & { price: number })[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const generateMarketFish = () => {
    const fish: (Fish & { price: number })[] = [];
    for (let i = 0; i < 6; i++) {
      const newFish = generateStarterFish(`Market Fish ${i + 1}`);
      // Market fish cost more than their value
      const price = Math.round(newFish.value * (1.2 + Math.random() * 0.3));
      fish.push({ ...newFish, price });
    }
    return fish;
  };

  useEffect(() => {
    setAvailableFish(generateMarketFish());
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => {
      setAvailableFish(generateMarketFish());
      setRefreshing(false);
    }, 500);
  };

  const handlePurchase = (fish: Fish & { price: number }) => {
    if (spendCurrency(fish.price)) {
      const { price, ...fishData } = fish;
      addFish(fishData);
      setAvailableFish((prev) => prev.filter((f) => f.id !== fish.id));
    } else {
      alert('Not enough currency!');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-xl p-6 border border-purple-500/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-500/30 rounded-xl">
              <ShoppingCart className="w-8 h-8 text-purple-400" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Fish Marketplace</h2>
              <p className="text-sm text-gray-300">Discover and purchase unique fish</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-400">Your Currency</div>
            <div className="text-3xl font-bold text-yellow-500">{currency}</div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-2 text-gray-400">
          <Sparkles className="w-5 h-5" />
          <span>New fish appear regularly</span>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className={`px-4 py-2 bg-ocean-700 hover:bg-ocean-600 text-white rounded-lg flex items-center gap-2 transition-all ${
            refreshing ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh Stock
        </button>
      </div>

      {/* Available Fish */}
      {availableFish.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {availableFish.map((fish) => (
            <motion.div
              key={fish.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="bg-gradient-to-br from-ocean-800 to-ocean-900 rounded-xl border-2 border-ocean-600 overflow-hidden"
            >
              <div className="p-4">
                <FishCard fish={fish} compact />
              </div>

              <div className="border-t border-ocean-700 p-4 bg-ocean-800/50">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <div className="text-sm text-gray-400">Price</div>
                    <div className="text-2xl font-bold text-yellow-500">{fish.price}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-400">Value</div>
                    <div className="text-lg font-bold text-white">{fish.value}</div>
                  </div>
                </div>

                <button
                  onClick={() => handlePurchase(fish)}
                  disabled={currency < fish.price}
                  className={`w-full px-4 py-2 rounded-lg font-medium transition-all ${
                    currency < fish.price
                      ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                      : 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white transform hover:scale-105'
                  }`}
                >
                  {currency < fish.price ? 'Not Enough Currency' : 'Purchase'}
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-ocean-800 rounded-xl border border-ocean-600">
          <ShoppingCart className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg">All fish have been purchased!</p>
          <button
            onClick={handleRefresh}
            className="mt-4 px-6 py-3 bg-purple-500 hover:bg-purple-600 text-white rounded-lg font-medium transition-colors"
          >
            Refresh Stock
          </button>
        </div>
      )}

      {/* Tips */}
      <div className="bg-ocean-800 rounded-xl p-4 border border-ocean-600">
        <div className="flex items-start gap-3">
          <TrendingUp className="w-5 h-5 text-blue-400 mt-0.5" />
          <div>
            <h4 className="font-bold text-white mb-1">Marketplace Tips</h4>
            <ul className="text-sm text-gray-400 space-y-1">
              <li>• Fish prices are based on their value and rarity</li>
              <li>• Breed fish to create offspring and earn value</li>
              <li>• Check back regularly for new and unique fish</li>
              <li>• Higher generation fish are more valuable</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
