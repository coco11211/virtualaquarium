import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, Award, Dna, Fish } from 'lucide-react';
import { useGameStore } from '../store/gameStore';
import type { BodyColor, FinType, Pattern } from '../types';

const COLORS = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'];

export function Statistics() {
  const { fish, achievements, totalBreedings, startDate } = useGameStore();

  // Calculate color distribution
  const colorDistribution = fish.reduce((acc, f) => {
    acc[f.phenotype.bodyColor] = (acc[f.phenotype.bodyColor] || 0) + 1;
    return acc;
  }, {} as Record<BodyColor, number>);

  const colorData = Object.entries(colorDistribution).map(([color, count]) => ({
    name: color,
    value: count,
  }));

  // Calculate fin distribution
  const finDistribution = fish.reduce((acc, f) => {
    acc[f.phenotype.finType] = (acc[f.phenotype.finType] || 0) + 1;
    return acc;
  }, {} as Record<FinType, number>);

  const finData = Object.entries(finDistribution).map(([type, count]) => ({
    name: type,
    count,
  }));

  // Calculate pattern distribution
  const patternDistribution = fish.reduce((acc, f) => {
    acc[f.phenotype.pattern] = (acc[f.phenotype.pattern] || 0) + 1;
    return acc;
  }, {} as Record<Pattern, number>);

  const patternData = Object.entries(patternDistribution).map(([type, count]) => ({
    name: type,
    count,
  }));

  // Generation distribution
  const generationDistribution = fish.reduce((acc, f) => {
    const gen = `Gen ${f.generation}`;
    acc[gen] = (acc[gen] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const generationData = Object.entries(generationDistribution)
    .map(([gen, count]) => ({
      name: gen,
      count,
    }))
    .sort((a, b) => {
      const aNum = parseInt(a.name.split(' ')[1]);
      const bNum = parseInt(b.name.split(' ')[1]);
      return aNum - bNum;
    });

  const totalValue = fish.reduce((sum, f) => sum + f.value, 0);
  const averageValue = fish.length > 0 ? Math.round(totalValue / fish.length) : 0;
  const unlockedAchievements = achievements.filter((a) => a.unlockedAt);
  const daysPlaying = Math.floor((Date.now() - startDate) / (1000 * 60 * 60 * 24));

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-blue-500/20 to-blue-600/20 rounded-xl p-4 border border-blue-500/30"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-blue-500/30 rounded-lg">
              <Fish className="w-5 h-5 text-blue-400" />
            </div>
            <div className="text-sm text-blue-300">Total Fish</div>
          </div>
          <div className="text-3xl font-bold text-white">{fish.length}</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-purple-500/20 to-purple-600/20 rounded-xl p-4 border border-purple-500/30"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-purple-500/30 rounded-lg">
              <Dna className="w-5 h-5 text-purple-400" />
            </div>
            <div className="text-sm text-purple-300">Breedings</div>
          </div>
          <div className="text-3xl font-bold text-white">{totalBreedings}</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-br from-yellow-500/20 to-yellow-600/20 rounded-xl p-4 border border-yellow-500/30"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-yellow-500/30 rounded-lg">
              <TrendingUp className="w-5 h-5 text-yellow-400" />
            </div>
            <div className="text-sm text-yellow-300">Avg Value</div>
          </div>
          <div className="text-3xl font-bold text-white">{averageValue}</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-gradient-to-br from-green-500/20 to-green-600/20 rounded-xl p-4 border border-green-500/30"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-green-500/30 rounded-lg">
              <Award className="w-5 h-5 text-green-400" />
            </div>
            <div className="text-sm text-green-300">Achievements</div>
          </div>
          <div className="text-3xl font-bold text-white">
            {unlockedAchievements.length}/{achievements.length}
          </div>
        </motion.div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Body Colors */}
        <div className="bg-ocean-800 rounded-xl p-6 border border-ocean-600">
          <h3 className="text-lg font-bold text-white mb-4">Body Color Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={colorData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {colorData.map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Generation Distribution */}
        <div className="bg-ocean-800 rounded-xl p-6 border border-ocean-600">
          <h3 className="text-lg font-bold text-white mb-4">Generation Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={generationData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="count" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Fin Types */}
        <div className="bg-ocean-800 rounded-xl p-6 border border-ocean-600">
          <h3 className="text-lg font-bold text-white mb-4">Fin Type Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={finData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="count" fill="#8B5CF6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Patterns */}
        <div className="bg-ocean-800 rounded-xl p-6 border border-ocean-600">
          <h3 className="text-lg font-bold text-white mb-4">Pattern Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={patternData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="count" fill="#EC4899" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Achievements */}
      <div className="bg-ocean-800 rounded-xl p-6 border border-ocean-600">
        <h3 className="text-lg font-bold text-white mb-4">Achievements</h3>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
          {achievements.map((achievement) => (
            <motion.div
              key={achievement.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className={`p-4 rounded-lg border-2 transition-all ${
                achievement.unlockedAt
                  ? 'bg-gradient-to-br from-yellow-500/20 to-orange-500/20 border-yellow-500/50'
                  : 'bg-ocean-700/50 border-ocean-600 opacity-50'
              }`}
            >
              <div className="text-3xl mb-2">{achievement.icon}</div>
              <div className="font-bold text-white text-sm">{achievement.name}</div>
              <div className="text-xs text-gray-400 mt-1">{achievement.description}</div>
              {achievement.unlockedAt && (
                <div className="text-xs text-green-400 mt-2">
                  ✓ Unlocked {new Date(achievement.unlockedAt).toLocaleDateString()}
                </div>
              )}
            </motion.div>
          ))}
        </div>
      </div>

      {/* Misc Stats */}
      <div className="bg-ocean-800 rounded-xl p-6 border border-ocean-600">
        <h3 className="text-lg font-bold text-white mb-4">Additional Statistics</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-gray-400">Days Playing</div>
            <div className="text-xl font-bold text-white mt-1">{daysPlaying}</div>
          </div>
          <div>
            <div className="text-gray-400">Total Value</div>
            <div className="text-xl font-bold text-yellow-500 mt-1">{totalValue}</div>
          </div>
          <div>
            <div className="text-gray-400">Rarest Fish</div>
            <div className="text-xl font-bold text-purple-500 mt-1">
              {fish.length > 0 ? Math.max(...fish.map((f) => f.value)) : 0}
            </div>
          </div>
          <div>
            <div className="text-gray-400">Max Generation</div>
            <div className="text-xl font-bold text-blue-500 mt-1">
              {fish.length > 0 ? Math.max(...fish.map((f) => f.generation)) : 0}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
