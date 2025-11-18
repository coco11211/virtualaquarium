import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Heart, Sparkles, Info } from 'lucide-react';
import type { Fish, BreedingPair, TraitProbabilities } from '../types';
import { FishCard } from './FishCard';
import { FishVisual } from './FishVisual';
import { breedFish, calculateBreedingProbabilities } from '../engine/genetics';
import { useGameStore } from '../store/gameStore';

interface BreedingLabProps {
  onClose: () => void;
}

export function BreedingLab({ onClose }: BreedingLabProps) {
  const { fish, addFish, incrementBreedings } = useGameStore();
  const [selectedMother, setSelectedMother] = useState<Fish | null>(null);
  const [selectedFather, setSelectedFather] = useState<Fish | null>(null);
  const [breeding, setBreeding] = useState(false);
  const [offspring, setOffspring] = useState<Fish[] | null>(null);
  const [probabilities, setProbabilities] = useState<TraitProbabilities | null>(null);

  const handleBreed = () => {
    if (!selectedMother || !selectedFather) return;

    setBreeding(true);

    const pair: BreedingPair = {
      mother: selectedMother,
      father: selectedFather,
    };

    const result = breedFish(pair, 3);

    setTimeout(() => {
      setOffspring(result.offspring);
      setBreeding(false);
    }, 2000);
  };

  const handleKeepOffspring = (fish: Fish) => {
    addFish(fish);
    setOffspring((prev) => prev?.filter((f) => f.id !== fish.id) || null);

    if (!offspring || offspring.length === 1) {
      incrementBreedings();
      setSelectedMother(null);
      setSelectedFather(null);
      setOffspring(null);
      setProbabilities(null);
    }
  };

  const handleCalculateProbabilities = () => {
    if (!selectedMother || !selectedFather) return;

    const pair: BreedingPair = {
      mother: selectedMother,
      father: selectedFather,
    };

    const probs = calculateBreedingProbabilities(pair);
    setProbabilities(probs);
  };

  const canBreed = selectedMother && selectedFather && !breeding && !offspring;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="bg-gradient-to-br from-ocean-900 to-ocean-950 rounded-2xl border-2 border-ocean-600 max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="p-6 border-b border-ocean-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-pink-500/20 rounded-xl">
                <Heart className="w-6 h-6 text-pink-400" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white">Breeding Laboratory</h2>
                <p className="text-sm text-gray-400">Select two fish to create offspring</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-ocean-700 hover:bg-ocean-600 text-white rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {/* Breeding Interface */}
          {!offspring ? (
            <div className="space-y-6">
              {/* Selected Parents */}
              <div className="grid grid-cols-3 gap-4 items-center">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-300">Mother</label>
                  {selectedMother ? (
                    <div className="relative">
                      <FishCard
                        fish={selectedMother}
                        selected
                        onClick={() => setSelectedMother(null)}
                      />
                      <div className="absolute -top-2 -right-2 bg-pink-500 text-white text-xs px-2 py-1 rounded-full">
                        ♀
                      </div>
                    </div>
                  ) : (
                    <div className="h-48 border-2 border-dashed border-ocean-600 rounded-xl flex items-center justify-center text-gray-500">
                      Select a fish
                    </div>
                  )}
                </div>

                <div className="flex flex-col items-center gap-4">
                  <Heart className="w-12 h-12 text-pink-400" />
                  {canBreed && (
                    <>
                      <button
                        onClick={handleBreed}
                        className="px-6 py-3 bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600 text-white rounded-xl font-bold flex items-center gap-2 transition-all transform hover:scale-105"
                      >
                        <Sparkles className="w-5 h-5" />
                        Breed
                      </button>
                      <button
                        onClick={handleCalculateProbabilities}
                        className="px-4 py-2 bg-ocean-700 hover:bg-ocean-600 text-white rounded-lg text-sm flex items-center gap-2 transition-colors"
                      >
                        <Info className="w-4 h-4" />
                        Show Probabilities
                      </button>
                    </>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-300">Father</label>
                  {selectedFather ? (
                    <div className="relative">
                      <FishCard
                        fish={selectedFather}
                        selected
                        onClick={() => setSelectedFather(null)}
                      />
                      <div className="absolute -top-2 -right-2 bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
                        ♂
                      </div>
                    </div>
                  ) : (
                    <div className="h-48 border-2 border-dashed border-ocean-600 rounded-xl flex items-center justify-center text-gray-500">
                      Select a fish
                    </div>
                  )}
                </div>
              </div>

              {/* Breeding Animation */}
              <AnimatePresence>
                {breeding && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 bg-black/70 flex items-center justify-center z-10"
                  >
                    <div className="text-center">
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                      >
                        <Sparkles className="w-16 h-16 text-pink-400 mx-auto" />
                      </motion.div>
                      <p className="text-white text-xl mt-4">Creating offspring...</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Probabilities Display */}
              {probabilities && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-ocean-800 rounded-xl p-4 border border-ocean-600"
                >
                  <h3 className="text-lg font-bold text-white mb-3">Trait Probabilities</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <h4 className="text-gray-300 font-medium mb-2">Body Colors</h4>
                      {Object.entries(probabilities.bodyColor)
                        .filter(([_, prob]) => prob > 0.05)
                        .sort((a, b) => b[1] - a[1])
                        .map(([color, prob]) => (
                          <div key={color} className="flex justify-between items-center mb-1">
                            <span className="capitalize text-gray-400">{color}</span>
                            <span className="text-white font-medium">{(prob * 100).toFixed(1)}%</span>
                          </div>
                        ))}
                    </div>
                    <div>
                      <h4 className="text-gray-300 font-medium mb-2">Fin Types</h4>
                      {Object.entries(probabilities.finType)
                        .filter(([_, prob]) => prob > 0.05)
                        .sort((a, b) => b[1] - a[1])
                        .map(([fin, prob]) => (
                          <div key={fin} className="flex justify-between items-center mb-1">
                            <span className="capitalize text-gray-400">{fin}</span>
                            <span className="text-white font-medium">{(prob * 100).toFixed(1)}%</span>
                          </div>
                        ))}
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Available Fish */}
              <div>
                <h3 className="text-lg font-bold text-white mb-3">Available Fish</h3>
                <div className="grid grid-cols-4 gap-4">
                  {fish.map((f) => (
                    <FishCard
                      key={f.id}
                      fish={f}
                      onClick={() => {
                        if (!selectedMother) {
                          setSelectedMother(f);
                        } else if (!selectedFather && f.id !== selectedMother.id) {
                          setSelectedFather(f);
                        }
                      }}
                      selected={f.id === selectedMother?.id || f.id === selectedFather?.id}
                      compact
                    />
                  ))}
                </div>
              </div>
            </div>
          ) : (
            /* Offspring Display */
            <div className="space-y-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center"
              >
                <h3 className="text-2xl font-bold text-white mb-2">🎉 Breeding Successful!</h3>
                <p className="text-gray-400">Select the offspring you want to keep</p>
              </motion.div>

              <div className="grid grid-cols-3 gap-4">
                {offspring.map((baby, index) => (
                  <motion.div
                    key={baby.id}
                    initial={{ opacity: 0, scale: 0.8, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    transition={{ delay: index * 0.2 }}
                    className="bg-gradient-to-br from-ocean-800 to-ocean-900 rounded-xl p-4 border-2 border-pink-500/50"
                  >
                    <div className="h-32 flex items-center justify-center mb-3">
                      <FishVisual fish={baby} size="medium" />
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Color:</span>
                        <span className="text-white capitalize">{baby.phenotype.bodyColor}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Fins:</span>
                        <span className="text-white capitalize">{baby.phenotype.finType}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Pattern:</span>
                        <span className="text-white capitalize">{baby.phenotype.pattern}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Value:</span>
                        <span className="text-yellow-500 font-bold">{baby.value}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleKeepOffspring(baby)}
                      className="mt-4 w-full px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-lg font-medium transition-all transform hover:scale-105"
                    >
                      Keep Fish
                    </button>
                  </motion.div>
                ))}
              </div>

              <div className="text-center">
                <button
                  onClick={() => {
                    offspring.forEach((baby) => addFish(baby));
                    incrementBreedings();
                    setSelectedMother(null);
                    setSelectedFather(null);
                    setOffspring(null);
                  }}
                  className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-xl font-bold transition-all"
                >
                  Keep All Fish
                </button>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
