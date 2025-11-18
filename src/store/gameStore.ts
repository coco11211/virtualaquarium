import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Fish, GameState, Achievement } from '../types';
import { generateStarterFish } from '../engine/genetics';

interface GameStore extends GameState {
  // Actions
  addFish: (fish: Fish) => void;
  removeFish: (fishId: string) => void;
  updateFish: (fishId: string, updates: Partial<Fish>) => void;
  addCurrency: (amount: number) => void;
  spendCurrency: (amount: number) => boolean;
  incrementBreedings: () => void;
  unlockAchievement: (achievementId: string) => void;
  resetGame: () => void;
  ageFish: () => void;
  getFishById: (fishId: string) => Fish | undefined;
  getFishLineage: (fishId: string) => { ancestors: Fish[]; descendants: Fish[] };
}

const INITIAL_ACHIEVEMENTS: Achievement[] = [
  { id: 'first_breed', name: 'First Steps', description: 'Breed your first fish', icon: '🐣' },
  { id: 'collector_10', name: 'Collector', description: 'Own 10 fish', icon: '🏆' },
  { id: 'collector_25', name: 'Master Collector', description: 'Own 25 fish', icon: '👑' },
  { id: 'generation_5', name: 'Five Generations', description: 'Reach 5th generation', icon: '🌟' },
  { id: 'generation_10', name: 'Ancient Lineage', description: 'Reach 10th generation', icon: '✨' },
  { id: 'rare_find', name: 'Rare Find', description: 'Own a fish worth 500+', icon: '💎' },
  { id: 'legendary', name: 'Legendary', description: 'Own a fish worth 1000+', icon: '🔮' },
  { id: 'breeder_50', name: 'Expert Breeder', description: 'Complete 50 breedings', icon: '🎯' },
  { id: 'all_colors', name: 'Rainbow Collection', description: 'Own all body colors', icon: '🌈' },
  { id: 'all_fins', name: 'Fin Fanatic', description: 'Own all fin types', icon: '🎨' },
];

export const useGameStore = create<GameStore>()(
  persist(
    (set, get) => ({
      fish: [],
      achievements: INITIAL_ACHIEVEMENTS,
      currency: 1000,
      startDate: Date.now(),
      totalBreedings: 0,
      totalGeneration: 0,

      addFish: (fish) => {
        set((state) => {
          const newFish = [...state.fish, fish];
          const newState = { fish: newFish };

          // Check achievements
          if (newFish.length === 10) {
            get().unlockAchievement('collector_10');
          }
          if (newFish.length === 25) {
            get().unlockAchievement('collector_25');
          }
          if (fish.value >= 500) {
            get().unlockAchievement('rare_find');
          }
          if (fish.value >= 1000) {
            get().unlockAchievement('legendary');
          }
          if (fish.generation >= 5) {
            get().unlockAchievement('generation_5');
          }
          if (fish.generation >= 10) {
            get().unlockAchievement('generation_10');
          }

          // Check if all colors collected
          const colors = new Set(newFish.map(f => f.phenotype.bodyColor));
          if (colors.size >= 10) {
            get().unlockAchievement('all_colors');
          }

          // Check if all fins collected
          const fins = new Set(newFish.map(f => f.phenotype.finType));
          if (fins.size >= 6) {
            get().unlockAchievement('all_fins');
          }

          return newState;
        });
      },

      removeFish: (fishId) => {
        set((state) => ({
          fish: state.fish.filter((f) => f.id !== fishId),
        }));
      },

      updateFish: (fishId, updates) => {
        set((state) => ({
          fish: state.fish.map((f) => (f.id === fishId ? { ...f, ...updates } : f)),
        }));
      },

      addCurrency: (amount) => {
        set((state) => ({ currency: state.currency + amount }));
      },

      spendCurrency: (amount) => {
        const state = get();
        if (state.currency >= amount) {
          set({ currency: state.currency - amount });
          return true;
        }
        return false;
      },

      incrementBreedings: () => {
        set((state) => {
          const newCount = state.totalBreedings + 1;
          if (newCount === 1) {
            get().unlockAchievement('first_breed');
          }
          if (newCount === 50) {
            get().unlockAchievement('breeder_50');
          }
          return { totalBreedings: newCount };
        });
      },

      unlockAchievement: (achievementId) => {
        set((state) => ({
          achievements: state.achievements.map((a) =>
            a.id === achievementId && !a.unlockedAt
              ? { ...a, unlockedAt: Date.now() }
              : a
          ),
        }));
      },

      resetGame: () => {
        const starters = [
          generateStarterFish('Azure'),
          generateStarterFish('Coral'),
          generateStarterFish('Sunny'),
        ];
        set({
          fish: starters,
          achievements: INITIAL_ACHIEVEMENTS,
          currency: 1000,
          startDate: Date.now(),
          totalBreedings: 0,
          totalGeneration: 0,
        });
      },

      ageFish: () => {
        set((state) => ({
          fish: state.fish.map((f) => ({
            ...f,
            age: Math.floor((Date.now() - f.birthDate) / (1000 * 60 * 60 * 24)),
          })),
        }));
      },

      getFishById: (fishId) => {
        return get().fish.find((f) => f.id === fishId);
      },

      getFishLineage: (fishId) => {
        const state = get();
        const fish = state.getFishById(fishId);
        if (!fish) return { ancestors: [], descendants: [] };

        const ancestors: Fish[] = [];
        const descendants: Fish[] = [];

        // Get ancestors
        const getAncestors = (f: Fish) => {
          if (f.parents) {
            const mother = state.getFishById(f.parents.mother);
            const father = state.getFishById(f.parents.father);
            if (mother) {
              ancestors.push(mother);
              getAncestors(mother);
            }
            if (father) {
              ancestors.push(father);
              getAncestors(father);
            }
          }
        };
        getAncestors(fish);

        // Get descendants
        state.fish.forEach((f) => {
          if (f.parents && (f.parents.mother === fishId || f.parents.father === fishId)) {
            descendants.push(f);
          }
        });

        return { ancestors, descendants };
      },
    }),
    {
      name: 'virtual-aquarium-storage',
    }
  )
);

// Initialize with starter fish if new game
if (typeof window !== 'undefined') {
  const stored = localStorage.getItem('virtual-aquarium-storage');
  if (!stored) {
    useGameStore.getState().resetGame();
  }
}
