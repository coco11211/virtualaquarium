import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import type { Fish } from '../types';
import { FishVisual } from './FishVisual';

interface AquariumProps {
  fish: Fish[];
  onFishClick?: (fish: Fish) => void;
  maxDisplay?: number;
}

interface SwimmingFish {
  fish: Fish;
  x: number;
  y: number;
  direction: number;
  speed: number;
}

export function Aquarium({ fish, onFishClick, maxDisplay = 12 }: AquariumProps) {
  const [swimmingFish, setSwimmingFish] = useState<SwimmingFish[]>([]);

  useEffect(() => {
    const displayFish = fish.slice(0, maxDisplay);
    const initial = displayFish.map((f) => ({
      fish: f,
      x: Math.random() * 80 + 10,
      y: Math.random() * 70 + 15,
      direction: Math.random() > 0.5 ? 1 : -1,
      speed: Math.random() * 0.3 + 0.2,
    }));
    setSwimmingFish(initial);
  }, [fish, maxDisplay]);

  useEffect(() => {
    if (swimmingFish.length === 0) return;

    const interval = setInterval(() => {
      setSwimmingFish((prev) =>
        prev.map((sf) => {
          let newX = sf.x + sf.speed * sf.direction;
          let newY = sf.y + (Math.random() - 0.5) * 0.5;
          let newDirection = sf.direction;

          // Bounce off walls
          if (newX <= 5 || newX >= 95) {
            newDirection = -sf.direction;
            newX = newX <= 5 ? 5 : 95;
          }

          // Keep in bounds
          newY = Math.max(10, Math.min(85, newY));

          return {
            ...sf,
            x: newX,
            y: newY,
            direction: newDirection,
          };
        })
      );
    }, 50);

    return () => clearInterval(interval);
  }, [swimmingFish.length]);

  return (
    <div className="relative w-full h-full bg-gradient-to-b from-ocean-400 via-ocean-600 to-ocean-800 rounded-2xl overflow-hidden">
      {/* Water effects */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-300/10 to-transparent pointer-events-none" />

      {/* Bubbles */}
      {[...Array(8)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-2 h-2 bg-white/30 rounded-full"
          style={{
            left: `${(i * 13 + 10) % 90}%`,
            bottom: 0,
          }}
          animate={{
            y: [0, -600],
            x: [0, Math.sin(i) * 30],
            scale: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 5 + i * 0.5,
            repeat: Infinity,
            delay: i * 0.7,
            ease: 'easeInOut',
          }}
        />
      ))}

      {/* Seaweed */}
      {[...Array(4)].map((_, i) => (
        <motion.div
          key={`seaweed-${i}`}
          className="absolute bottom-0 w-3 bg-green-600/40 rounded-t-full"
          style={{
            left: `${i * 25 + 8}%`,
            height: `${40 + Math.random() * 30}%`,
          }}
          animate={{
            scaleX: [1, 1.1, 1, 0.9, 1],
            skewX: [-2, 2, -2],
          }}
          transition={{
            duration: 3 + i * 0.5,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      ))}

      {/* Fish */}
      {swimmingFish.map(({ fish: f, x, y, direction }) => (
        <motion.div
          key={f.id}
          className="absolute cursor-pointer hover:scale-110 transition-transform"
          style={{
            left: `${x}%`,
            top: `${y}%`,
            transform: `scaleX(${direction})`,
          }}
          onClick={() => onFishClick?.(f)}
          whileHover={{ scale: 1.15 }}
        >
          <FishVisual fish={f} size="medium" animate={true} />
        </motion.div>
      ))}

      {/* Bottom sand */}
      <div className="absolute bottom-0 w-full h-16 bg-gradient-to-b from-yellow-800/30 to-yellow-900/50" />

      {/* Light rays */}
      {[...Array(3)].map((_, i) => (
        <motion.div
          key={`ray-${i}`}
          className="absolute top-0 w-20 h-full bg-gradient-to-b from-yellow-200/20 to-transparent"
          style={{
            left: `${i * 35 + 10}%`,
            transform: 'skewX(-10deg)',
          }}
          animate={{
            opacity: [0.2, 0.4, 0.2],
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            delay: i * 1.5,
          }}
        />
      ))}
    </div>
  );
}
