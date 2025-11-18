import { motion } from 'framer-motion';
import type { Fish, BodyColor, FinType } from '../types';

interface FishVisualProps {
  fish: Fish;
  size?: 'small' | 'medium' | 'large';
  animate?: boolean;
}

const COLOR_MAP: Record<BodyColor, string> = {
  red: '#EF4444',
  blue: '#3B82F6',
  orange: '#F97316',
  yellow: '#EAB308',
  purple: '#A855F7',
  green: '#22C55E',
  white: '#F3F4F6',
  black: '#1F2937',
  pink: '#EC4899',
  teal: '#14B8A6',
};

const SIZE_MAP = {
  small: { body: 40, fin: 15 },
  medium: { body: 60, fin: 22 },
  large: { body: 80, fin: 30 },
};

export function FishVisual({ fish, size = 'medium', animate = true }: FishVisualProps) {
  const dimensions = SIZE_MAP[size];
  const bodyColor = COLOR_MAP[fish.phenotype.bodyColor];
  const secondaryColor = fish.phenotype.secondaryColor ? COLOR_MAP[fish.phenotype.secondaryColor] : bodyColor;

  const swimAnimation = animate
    ? {
        x: [0, 5, 0, -5, 0],
        y: [0, -3, 0, 3, 0],
        rotate: [0, 2, 0, -2, 0],
      }
    : {};

  const finAnimation = animate
    ? {
        scaleX: [1, 1.1, 1, 0.9, 1],
      }
    : {};

  return (
    <motion.svg
      width={dimensions.body * 1.8}
      height={dimensions.body * 1.2}
      viewBox={`0 0 ${dimensions.body * 1.8} ${dimensions.body * 1.2}`}
      animate={swimAnimation}
      transition={{
        duration: 3,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    >
      <defs>
        {/* Gradients for patterns */}
        <linearGradient id={`gradient-${fish.id}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={bodyColor} />
          <stop offset="100%" stopColor={secondaryColor} />
        </linearGradient>

        <radialGradient id={`spotted-${fish.id}`}>
          <stop offset="0%" stopColor={bodyColor} />
          <stop offset="50%" stopColor={secondaryColor} />
          <stop offset="100%" stopColor={bodyColor} />
        </radialGradient>

        {/* Pattern definitions */}
        {fish.phenotype.pattern === 'spotted' && (
          <pattern id={`spots-${fish.id}`} x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
            <circle cx="10" cy="10" r="3" fill={secondaryColor} opacity="0.6" />
          </pattern>
        )}

        {fish.phenotype.pattern === 'striped' && (
          <pattern id={`stripes-${fish.id}`} x="0" y="0" width="10" height="20" patternUnits="userSpaceOnUse">
            <rect x="0" y="0" width="5" height="20" fill={secondaryColor} opacity="0.6" />
          </pattern>
        )}
      </defs>

      {/* Tail fin */}
      <motion.g animate={finAnimation} transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}>
        <TailFin
          finType={fish.phenotype.finType}
          color={bodyColor}
          secondaryColor={secondaryColor}
          size={dimensions.fin}
          x={10}
          y={dimensions.body * 0.6}
        />
      </motion.g>

      {/* Body */}
      <ellipse
        cx={dimensions.body}
        cy={dimensions.body * 0.6}
        rx={dimensions.body * 0.5}
        ry={dimensions.body * 0.35}
        fill={getPatternFill(fish, bodyColor)}
        stroke={secondaryColor}
        strokeWidth="1"
        opacity="0.95"
      />

      {/* Pattern overlay */}
      {fish.phenotype.pattern === 'marble' && (
        <>
          <ellipse
            cx={dimensions.body * 0.8}
            cy={dimensions.body * 0.5}
            rx={dimensions.body * 0.2}
            ry={dimensions.body * 0.15}
            fill={secondaryColor}
            opacity="0.4"
          />
          <ellipse
            cx={dimensions.body * 1.1}
            cy={dimensions.body * 0.7}
            rx={dimensions.body * 0.15}
            ry={dimensions.body * 0.12}
            fill={secondaryColor}
            opacity="0.3"
          />
        </>
      )}

      {/* Dorsal fin */}
      <motion.g animate={finAnimation} transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut', delay: 0.5 }}>
        <DorsalFin
          finType={fish.phenotype.finType}
          color={bodyColor}
          secondaryColor={secondaryColor}
          size={dimensions.fin}
          x={dimensions.body}
          y={dimensions.body * 0.3}
        />
      </motion.g>

      {/* Eye */}
      <circle cx={dimensions.body * 1.3} cy={dimensions.body * 0.55} r={dimensions.body * 0.08} fill="white" />
      <circle cx={dimensions.body * 1.32} cy={dimensions.body * 0.56} r={dimensions.body * 0.04} fill="black" />

      {/* Pectoral fin */}
      <motion.ellipse
        cx={dimensions.body * 0.9}
        cy={dimensions.body * 0.75}
        rx={dimensions.fin * 0.6}
        ry={dimensions.fin * 0.4}
        fill={bodyColor}
        opacity="0.6"
        animate={animate ? { rotate: [0, 15, 0] } : {}}
        transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
        style={{ transformOrigin: `${dimensions.body * 0.9}px ${dimensions.body * 0.75}px` }}
      />
    </motion.svg>
  );
}

function getPatternFill(fish: Fish, bodyColor: string): string {
  switch (fish.phenotype.pattern) {
    case 'gradient':
    case 'koi':
      return `url(#gradient-${fish.id})`;
    case 'spotted':
      return `url(#spots-${fish.id})`;
    case 'striped':
      return `url(#stripes-${fish.id})`;
    default:
      return bodyColor;
  }
}

function TailFin({
  finType,
  color,
  secondaryColor,
  size,
  x,
  y,
}: {
  finType: FinType;
  color: string;
  secondaryColor: string;
  size: number;
  x: number;
  y: number;
}) {
  switch (finType) {
    case 'veil':
      return (
        <path
          d={`M ${x} ${y} Q ${x - size * 0.5} ${y - size * 1.5} ${x - size} ${y} Q ${x - size * 0.5} ${y + size * 1.5} ${x} ${y}`}
          fill={color}
          stroke={secondaryColor}
          strokeWidth="1"
          opacity="0.8"
        />
      );
    case 'double':
      return (
        <g>
          <path
            d={`M ${x} ${y - size * 0.3} Q ${x - size * 0.8} ${y - size * 0.8} ${x - size * 0.7} ${y - size * 0.1}`}
            fill={color}
            opacity="0.8"
          />
          <path
            d={`M ${x} ${y + size * 0.3} Q ${x - size * 0.8} ${y + size * 0.8} ${x - size * 0.7} ${y + size * 0.1}`}
            fill={color}
            opacity="0.8"
          />
        </g>
      );
    case 'split':
      return (
        <path
          d={`M ${x} ${y} L ${x - size} ${y - size * 0.8} L ${x - size * 0.6} ${y} L ${x - size} ${y + size * 0.8} Z`}
          fill={color}
          stroke={secondaryColor}
          strokeWidth="1"
          opacity="0.8"
        />
      );
    case 'crown':
      return (
        <g>
          {[...Array(5)].map((_, i) => (
            <path
              key={i}
              d={`M ${x} ${y} L ${x - size * 0.8} ${y - size * 0.6 + i * size * 0.3} L ${x - size * 0.5} ${y - size * 0.3 + i * size * 0.3}`}
              fill={color}
              opacity="0.8"
            />
          ))}
        </g>
      );
    case 'long':
      return (
        <path
          d={`M ${x} ${y} Q ${x - size * 1.2} ${y - size * 0.3} ${x - size * 1.3} ${y} Q ${x - size * 1.2} ${y + size * 0.3} ${x} ${y}`}
          fill={color}
          stroke={secondaryColor}
          strokeWidth="1"
          opacity="0.8"
        />
      );
    default: // normal
      return (
        <path
          d={`M ${x} ${y} Q ${x - size * 0.8} ${y - size * 0.5} ${x - size} ${y} Q ${x - size * 0.8} ${y + size * 0.5} ${x} ${y}`}
          fill={color}
          opacity="0.8"
        />
      );
  }
}

function DorsalFin({
  finType,
  color,
  secondaryColor,
  size,
  x,
  y,
}: {
  finType: FinType;
  color: string;
  secondaryColor: string;
  size: number;
  x: number;
  y: number;
}) {
  if (finType === 'crown') {
    return (
      <g>
        {[...Array(4)].map((_, i) => (
          <path
            key={i}
            d={`M ${x - size + i * size * 0.5} ${y} L ${x - size + i * size * 0.5} ${y - size * 0.8} L ${x - size * 0.8 + i * size * 0.5} ${y - size * 0.4}`}
            fill={color}
            opacity="0.7"
          />
        ))}
      </g>
    );
  }

  const height = finType === 'veil' || finType === 'long' ? size * 1.2 : size * 0.8;

  return (
    <path
      d={`M ${x - size * 0.5} ${y} Q ${x - size * 0.2} ${y - height} ${x + size * 0.3} ${y - height * 0.8} L ${x + size * 0.5} ${y}`}
      fill={color}
      stroke={secondaryColor}
      strokeWidth="0.5"
      opacity="0.7"
    />
  );
}
