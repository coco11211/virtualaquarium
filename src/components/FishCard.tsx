import { motion } from 'framer-motion';
import { Heart, Star, Trophy } from 'lucide-react';
import type { Fish } from '../types';
import { FishVisual } from './FishVisual';

interface FishCardProps {
  fish: Fish;
  onClick?: () => void;
  onFavorite?: () => void;
  selected?: boolean;
  compact?: boolean;
}

export function FishCard({ fish, onClick, onFavorite, selected, compact }: FishCardProps) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      whileHover={{ scale: 1.02, y: -2 }}
      onClick={onClick}
      className={`
        relative bg-gradient-to-br from-ocean-800 to-ocean-900 rounded-xl
        border-2 transition-all cursor-pointer overflow-hidden
        ${selected ? 'border-yellow-400 shadow-lg shadow-yellow-400/50' : 'border-ocean-600 hover:border-ocean-500'}
        ${compact ? 'p-3' : 'p-4'}
      `}
    >
      {/* Shimmer effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent animate-shimmer" />

      {/* Favorite button */}
      {onFavorite && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onFavorite();
          }}
          className="absolute top-2 right-2 z-10 p-1.5 rounded-full bg-ocean-700/80 hover:bg-ocean-600 transition-colors"
        >
          <Heart
            className={`w-4 h-4 ${fish.isFavorite ? 'fill-red-500 text-red-500' : 'text-gray-300'}`}
          />
        </button>
      )}

      {/* Fish Visual */}
      <div className={`${compact ? 'h-24' : 'h-32'} flex items-center justify-center mb-3`}>
        <FishVisual fish={fish} size={compact ? 'small' : 'medium'} />
      </div>

      {/* Fish Info */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-white truncate flex-1">{fish.name}</h3>
          {fish.achievements.length > 0 && (
            <Trophy className="w-4 h-4 text-yellow-500 ml-2" />
          )}
        </div>

        {!compact && (
          <>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-ocean-700/50 rounded px-2 py-1">
                <div className="text-gray-400">Color</div>
                <div className="text-white font-medium capitalize">{fish.phenotype.bodyColor}</div>
              </div>
              <div className="bg-ocean-700/50 rounded px-2 py-1">
                <div className="text-gray-400">Fins</div>
                <div className="text-white font-medium capitalize">{fish.phenotype.finType}</div>
              </div>
              <div className="bg-ocean-700/50 rounded px-2 py-1">
                <div className="text-gray-400">Pattern</div>
                <div className="text-white font-medium capitalize">{fish.phenotype.pattern}</div>
              </div>
              <div className="bg-ocean-700/50 rounded px-2 py-1">
                <div className="text-gray-400">Gen</div>
                <div className="text-white font-medium">G{fish.generation}</div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-ocean-700">
              <div className="flex items-center gap-1">
                <Star className="w-4 h-4 text-yellow-500" />
                <span className="text-sm font-bold text-yellow-500">{fish.value}</span>
              </div>
              <div className="text-xs text-gray-400">
                {fish.age} {fish.age === 1 ? 'day' : 'days'} old
              </div>
            </div>
          </>
        )}
      </div>
    </motion.div>
  );
}
