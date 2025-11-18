import { motion } from 'framer-motion';
import { X, Heart, Star, Users, TrendingUp, Trash2 } from 'lucide-react';
import type { Fish } from '../types';
import { FishVisual } from './FishVisual';
import { useGameStore } from '../store/gameStore';

interface FishDetailsProps {
  fish: Fish;
  onClose: () => void;
}

export function FishDetails({ fish, onClose }: FishDetailsProps) {
  const { updateFish, removeFish, getFishLineage, getFishById } = useGameStore();

  const handleToggleFavorite = () => {
    updateFish(fish.id, { isFavorite: !fish.isFavorite });
  };

  const handleRename = () => {
    const newName = prompt('Enter new name:', fish.name);
    if (newName && newName.trim()) {
      updateFish(fish.id, { name: newName.trim() });
    }
  };

  const handleRemove = () => {
    if (confirm(`Are you sure you want to release ${fish.name}?`)) {
      removeFish(fish.id);
      onClose();
    }
  };

  const lineage = getFishLineage(fish.id);
  const mother = fish.parents ? getFishById(fish.parents.mother) : null;
  const father = fish.parents ? getFishById(fish.parents.father) : null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="bg-gradient-to-br from-ocean-900 to-ocean-950 rounded-2xl border-2 border-ocean-600 max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="p-6 border-b border-ocean-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-24 h-24 flex items-center justify-center">
                <FishVisual fish={fish} size="large" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white">{fish.name}</h2>
                <p className="text-sm text-gray-400">Generation {fish.generation}</p>
                <div className="flex items-center gap-2 mt-2">
                  <button
                    onClick={handleToggleFavorite}
                    className="p-1.5 rounded-lg bg-ocean-700 hover:bg-ocean-600 transition-colors"
                  >
                    <Heart
                      className={`w-4 h-4 ${fish.isFavorite ? 'fill-red-500 text-red-500' : 'text-gray-300'}`}
                    />
                  </button>
                  <button
                    onClick={handleRename}
                    className="px-3 py-1.5 text-sm bg-ocean-700 hover:bg-ocean-600 text-white rounded-lg transition-colors"
                  >
                    Rename
                  </button>
                </div>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-ocean-700 rounded-lg transition-colors"
            >
              <X className="w-6 h-6 text-gray-400" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-ocean-800 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Star className="w-5 h-5 text-yellow-500" />
                <span className="text-gray-400 text-sm">Value</span>
              </div>
              <div className="text-2xl font-bold text-yellow-500">{fish.value}</div>
            </div>
            <div className="bg-ocean-800 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-5 h-5 text-green-500" />
                <span className="text-gray-400 text-sm">Age</span>
              </div>
              <div className="text-2xl font-bold text-white">
                {fish.age} {fish.age === 1 ? 'day' : 'days'}
              </div>
            </div>
          </div>

          {/* Phenotype */}
          <div className="bg-ocean-800 rounded-xl p-4">
            <h3 className="text-lg font-bold text-white mb-3">Appearance</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-sm text-gray-400">Body Color</div>
                <div className="text-white font-medium capitalize">{fish.phenotype.bodyColor}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">Fin Type</div>
                <div className="text-white font-medium capitalize">{fish.phenotype.finType}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">Pattern</div>
                <div className="text-white font-medium capitalize">{fish.phenotype.pattern}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">Size</div>
                <div className="text-white font-medium capitalize">{fish.phenotype.size}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">Behavior</div>
                <div className="text-white font-medium capitalize">{fish.phenotype.behavior}</div>
              </div>
              {fish.phenotype.secondaryColor && (
                <div>
                  <div className="text-sm text-gray-400">Secondary Color</div>
                  <div className="text-white font-medium capitalize">{fish.phenotype.secondaryColor}</div>
                </div>
              )}
            </div>
          </div>

          {/* Genetics */}
          <div className="bg-ocean-800 rounded-xl p-4">
            <h3 className="text-lg font-bold text-white mb-3">Genetics</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Body Color Genes</span>
                <span className="text-white font-mono">
                  {fish.genes.bodyColor.allele1.substring(0, 1).toUpperCase()}
                  {fish.genes.bodyColor.allele2.substring(0, 1).toUpperCase()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Fin Type Genes</span>
                <span className="text-white font-mono">
                  {fish.genes.finType.allele1.substring(0, 1).toUpperCase()}
                  {fish.genes.finType.allele2.substring(0, 1).toUpperCase()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Pattern Genes</span>
                <span className="text-white font-mono">
                  {fish.genes.pattern.allele1.substring(0, 1).toUpperCase()}
                  {fish.genes.pattern.allele2.substring(0, 1).toUpperCase()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Size Genes</span>
                <span className="text-white font-mono">
                  {fish.genes.size.allele1.substring(0, 1).toUpperCase()}
                  {fish.genes.size.allele2.substring(0, 1).toUpperCase()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Behavior Genes</span>
                <span className="text-white font-mono">
                  {fish.genes.behavior.allele1.substring(0, 1).toUpperCase()}
                  {fish.genes.behavior.allele2.substring(0, 1).toUpperCase()}
                </span>
              </div>
            </div>
          </div>

          {/* Family */}
          {(mother || father || lineage.descendants.length > 0) && (
            <div className="bg-ocean-800 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <Users className="w-5 h-5 text-blue-400" />
                <h3 className="text-lg font-bold text-white">Family</h3>
              </div>

              {(mother || father) && (
                <div className="mb-3">
                  <div className="text-sm text-gray-400 mb-2">Parents</div>
                  <div className="grid grid-cols-2 gap-2">
                    {mother && (
                      <div className="bg-ocean-700 rounded-lg p-2">
                        <div className="text-xs text-pink-400">Mother</div>
                        <div className="text-white text-sm">{mother.name}</div>
                      </div>
                    )}
                    {father && (
                      <div className="bg-ocean-700 rounded-lg p-2">
                        <div className="text-xs text-blue-400">Father</div>
                        <div className="text-white text-sm">{father.name}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {lineage.descendants.length > 0 && (
                <div>
                  <div className="text-sm text-gray-400 mb-2">
                    Offspring ({lineage.descendants.length})
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {lineage.descendants.slice(0, 5).map((desc) => (
                      <div key={desc.id} className="bg-ocean-700 rounded-lg px-3 py-1 text-sm text-white">
                        {desc.name}
                      </div>
                    ))}
                    {lineage.descendants.length > 5 && (
                      <div className="bg-ocean-700 rounded-lg px-3 py-1 text-sm text-gray-400">
                        +{lineage.descendants.length - 5} more
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-ocean-700">
          <button
            onClick={handleRemove}
            className="w-full px-4 py-3 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
          >
            <Trash2 className="w-5 h-5" />
            Release Fish
          </button>
        </div>
      </motion.div>
    </div>
  );
}
