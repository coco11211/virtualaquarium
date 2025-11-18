// Genetic alleles for traits
export type Allele = 'dominant' | 'recessive';

export interface Gene {
  allele1: Allele;
  allele2: Allele;
}

export type BodyColor = 'red' | 'blue' | 'orange' | 'yellow' | 'purple' | 'green' | 'white' | 'black' | 'pink' | 'teal';
export type FinType = 'normal' | 'long' | 'split' | 'double' | 'veil' | 'crown';
export type Pattern = 'solid' | 'spotted' | 'striped' | 'marble' | 'gradient' | 'koi';
export type Size = 'small' | 'medium' | 'large';
export type Behavior = 'peaceful' | 'active' | 'shy' | 'aggressive' | 'playful';

export interface Genes {
  bodyColor: Gene;
  finType: Gene;
  pattern: Gene;
  size: Gene;
  behavior: Gene;
  // Secondary colors for patterns
  secondaryColor?: Gene;
}

export interface Phenotype {
  bodyColor: BodyColor;
  finType: FinType;
  pattern: Pattern;
  size: Size;
  behavior: Behavior;
  secondaryColor?: BodyColor;
}

export interface Fish {
  id: string;
  name: string;
  genes: Genes;
  phenotype: Phenotype;
  generation: number;
  parents?: {
    mother: string;
    father: string;
  };
  birthDate: number;
  age: number; // in days
  value: number; // rarity/market value
  achievements: string[];
  isFavorite: boolean;
}

export interface BreedingPair {
  mother: Fish;
  father: Fish;
}

export interface BreedingResult {
  offspring: Fish[];
  probabilities: TraitProbabilities;
}

export interface TraitProbabilities {
  bodyColor: Record<BodyColor, number>;
  finType: Record<FinType, number>;
  pattern: Record<Pattern, number>;
  size: Record<Size, number>;
  behavior: Record<Behavior, number>;
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  unlockedAt?: number;
}

export interface GameState {
  fish: Fish[];
  achievements: Achievement[];
  currency: number;
  startDate: number;
  totalBreedings: number;
  totalGeneration: number;
}
