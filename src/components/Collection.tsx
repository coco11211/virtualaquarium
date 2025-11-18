import { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Filter, Heart, Star } from 'lucide-react';
import type { Fish } from '../types';
import { FishCard } from './FishCard';
import { useGameStore } from '../store/gameStore';

interface CollectionProps {
  onFishClick: (fish: Fish) => void;
}

type SortOption = 'value' | 'generation' | 'age' | 'name';
type FilterOption = 'all' | 'favorites' | 'recent';

export function Collection({ onFishClick }: CollectionProps) {
  const { fish, updateFish } = useGameStore();
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('value');
  const [filterBy, setFilterBy] = useState<FilterOption>('all');
  const [showFilters, setShowFilters] = useState(false);

  const filteredFish = fish
    .filter((f) => {
      if (filterBy === 'favorites' && !f.isFavorite) return false;
      if (filterBy === 'recent' && f.age > 7) return false;
      if (search && !f.name.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'value':
          return b.value - a.value;
        case 'generation':
          return b.generation - a.generation;
        case 'age':
          return a.age - b.age;
        case 'name':
          return a.name.localeCompare(b.name);
        default:
          return 0;
      }
    });

  const handleToggleFavorite = (fishId: string, isFavorite: boolean) => {
    updateFish(fishId, { isFavorite: !isFavorite });
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search fish..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-ocean-800 border border-ocean-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-ocean-500"
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
              showFilters ? 'bg-ocean-600 text-white' : 'bg-ocean-800 text-gray-300 hover:bg-ocean-700'
            }`}
          >
            <Filter className="w-4 h-4" />
            Filters
          </button>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
            className="px-4 py-2 bg-ocean-800 border border-ocean-600 rounded-lg text-white focus:outline-none focus:border-ocean-500"
          >
            <option value="value">Sort by Value</option>
            <option value="generation">Sort by Generation</option>
            <option value="age">Sort by Age</option>
            <option value="name">Sort by Name</option>
          </select>
        </div>
      </div>

      {/* Filter Options */}
      {showFilters && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="bg-ocean-800 rounded-lg p-4 border border-ocean-600"
        >
          <div className="flex gap-2">
            <button
              onClick={() => setFilterBy('all')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                filterBy === 'all' ? 'bg-ocean-600 text-white' : 'bg-ocean-700 text-gray-300 hover:bg-ocean-600'
              }`}
            >
              All Fish ({fish.length})
            </button>
            <button
              onClick={() => setFilterBy('favorites')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                filterBy === 'favorites' ? 'bg-ocean-600 text-white' : 'bg-ocean-700 text-gray-300 hover:bg-ocean-600'
              }`}
            >
              <Heart className="w-4 h-4" />
              Favorites ({fish.filter((f) => f.isFavorite).length})
            </button>
            <button
              onClick={() => setFilterBy('recent')}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                filterBy === 'recent' ? 'bg-ocean-600 text-white' : 'bg-ocean-700 text-gray-300 hover:bg-ocean-600'
              }`}
            >
              <Star className="w-4 h-4" />
              Recent ({fish.filter((f) => f.age <= 7).length})
            </button>
          </div>
        </motion.div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-ocean-800 rounded-lg p-4 border border-ocean-600">
          <div className="text-2xl font-bold text-white">{fish.length}</div>
          <div className="text-sm text-gray-400">Total Fish</div>
        </div>
        <div className="bg-ocean-800 rounded-lg p-4 border border-ocean-600">
          <div className="text-2xl font-bold text-yellow-500">
            {fish.length > 0 ? Math.max(...fish.map((f) => f.value)) : 0}
          </div>
          <div className="text-sm text-gray-400">Highest Value</div>
        </div>
        <div className="bg-ocean-800 rounded-lg p-4 border border-ocean-600">
          <div className="text-2xl font-bold text-purple-500">
            {fish.length > 0 ? Math.max(...fish.map((f) => f.generation)) : 0}
          </div>
          <div className="text-sm text-gray-400">Max Generation</div>
        </div>
        <div className="bg-ocean-800 rounded-lg p-4 border border-ocean-600">
          <div className="text-2xl font-bold text-pink-500">
            {fish.filter((f) => f.isFavorite).length}
          </div>
          <div className="text-sm text-gray-400">Favorites</div>
        </div>
      </div>

      {/* Fish Grid */}
      {filteredFish.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredFish.map((f) => (
            <FishCard
              key={f.id}
              fish={f}
              onClick={() => onFishClick(f)}
              onFavorite={() => handleToggleFavorite(f.id, f.isFavorite)}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-400">
          <p className="text-lg">No fish found</p>
          <p className="text-sm">Try adjusting your filters</p>
        </div>
      )}
    </div>
  );
}
