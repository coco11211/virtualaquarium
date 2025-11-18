import type {
  Gene,
  Genes,
  Phenotype,
  Fish,
  BreedingPair,
  BreedingResult,
  TraitProbabilities,
  BodyColor,
  FinType,
  Pattern,
  Size,
  Behavior,
} from '../types';

// Trait dominance mapping
const BODY_COLOR_DOMINANCE: Record<BodyColor, number> = {
  red: 9,
  orange: 8,
  yellow: 7,
  pink: 6,
  purple: 5,
  blue: 4,
  teal: 3,
  green: 2,
  white: 1,
  black: 10,
};

const FIN_TYPE_DOMINANCE: Record<FinType, number> = {
  crown: 6,
  veil: 5,
  double: 4,
  split: 3,
  long: 2,
  normal: 1,
};

const PATTERN_DOMINANCE: Record<Pattern, number> = {
  koi: 6,
  marble: 5,
  gradient: 4,
  striped: 3,
  spotted: 2,
  solid: 1,
};

const SIZE_DOMINANCE: Record<Size, number> = {
  large: 3,
  medium: 2,
  small: 1,
};

const BEHAVIOR_DOMINANCE: Record<Behavior, number> = {
  aggressive: 5,
  playful: 4,
  active: 3,
  peaceful: 2,
  shy: 1,
};

// All possible values for each trait
const ALL_BODY_COLORS: BodyColor[] = ['red', 'blue', 'orange', 'yellow', 'purple', 'green', 'white', 'black', 'pink', 'teal'];
const ALL_FIN_TYPES: FinType[] = ['normal', 'long', 'split', 'double', 'veil', 'crown'];
const ALL_PATTERNS: Pattern[] = ['solid', 'spotted', 'striped', 'marble', 'gradient', 'koi'];
const ALL_SIZES: Size[] = ['small', 'medium', 'large'];
const ALL_BEHAVIORS: Behavior[] = ['peaceful', 'active', 'shy', 'aggressive', 'playful'];

// Create a random gene
function createRandomGene(): Gene {
  return {
    allele1: Math.random() > 0.5 ? 'dominant' : 'recessive',
    allele2: Math.random() > 0.5 ? 'dominant' : 'recessive',
  };
}

// Inherit one allele from each parent
function inheritGene(parent1Gene: Gene, parent2Gene: Gene): Gene {
  const allele1 = Math.random() > 0.5 ? parent1Gene.allele1 : parent1Gene.allele2;
  const allele2 = Math.random() > 0.5 ? parent2Gene.allele1 : parent2Gene.allele2;
  return { allele1, allele2 };
}

// Express phenotype from genotype
function expressBodyColor(gene: Gene, traitValue1: BodyColor, traitValue2: BodyColor): BodyColor {
  if (gene.allele1 === gene.allele2) {
    // Homozygous - express the more dominant trait based on dominance hierarchy
    return BODY_COLOR_DOMINANCE[traitValue1] > BODY_COLOR_DOMINANCE[traitValue2] ? traitValue1 : traitValue2;
  } else {
    // Heterozygous - dominant allele wins
    if (gene.allele1 === 'dominant') {
      return traitValue1;
    } else {
      return traitValue2;
    }
  }
}

function expressFinType(gene: Gene, traitValue1: FinType, traitValue2: FinType): FinType {
  if (gene.allele1 === gene.allele2) {
    return FIN_TYPE_DOMINANCE[traitValue1] > FIN_TYPE_DOMINANCE[traitValue2] ? traitValue1 : traitValue2;
  } else {
    return gene.allele1 === 'dominant' ? traitValue1 : traitValue2;
  }
}

function expressPattern(gene: Gene, traitValue1: Pattern, traitValue2: Pattern): Pattern {
  if (gene.allele1 === gene.allele2) {
    return PATTERN_DOMINANCE[traitValue1] > PATTERN_DOMINANCE[traitValue2] ? traitValue1 : traitValue2;
  } else {
    return gene.allele1 === 'dominant' ? traitValue1 : traitValue2;
  }
}

function expressSize(gene: Gene, traitValue1: Size, traitValue2: Size): Size {
  if (gene.allele1 === gene.allele2) {
    return SIZE_DOMINANCE[traitValue1] > SIZE_DOMINANCE[traitValue2] ? traitValue1 : traitValue2;
  } else {
    return gene.allele1 === 'dominant' ? traitValue1 : traitValue2;
  }
}

function expressBehavior(gene: Gene, traitValue1: Behavior, traitValue2: Behavior): Behavior {
  if (gene.allele1 === gene.allele2) {
    return BEHAVIOR_DOMINANCE[traitValue1] > BEHAVIOR_DOMINANCE[traitValue2] ? traitValue1 : traitValue2;
  } else {
    return gene.allele1 === 'dominant' ? traitValue1 : traitValue2;
  }
}

// Calculate phenotype from genes with parent phenotypes as reference
export function calculatePhenotype(genes: Genes, parent1?: Phenotype, parent2?: Phenotype): Phenotype {
  // For new fish without parents, generate random phenotypes
  if (!parent1 || !parent2) {
    return {
      bodyColor: ALL_BODY_COLORS[Math.floor(Math.random() * ALL_BODY_COLORS.length)],
      finType: ALL_FIN_TYPES[Math.floor(Math.random() * ALL_FIN_TYPES.length)],
      pattern: ALL_PATTERNS[Math.floor(Math.random() * ALL_PATTERNS.length)],
      size: ALL_SIZES[Math.floor(Math.random() * ALL_SIZES.length)],
      behavior: ALL_BEHAVIORS[Math.floor(Math.random() * ALL_BEHAVIORS.length)],
      secondaryColor: Math.random() > 0.5 ? ALL_BODY_COLORS[Math.floor(Math.random() * ALL_BODY_COLORS.length)] : undefined,
    };
  }

  // Express traits based on genes and parent phenotypes
  const bodyColor = expressBodyColor(genes.bodyColor, parent1.bodyColor, parent2.bodyColor);
  const finType = expressFinType(genes.finType, parent1.finType, parent2.finType);
  const pattern = expressPattern(genes.pattern, parent1.pattern, parent2.pattern);
  const size = expressSize(genes.size, parent1.size, parent2.size);
  const behavior = expressBehavior(genes.behavior, parent1.behavior, parent2.behavior);

  // Secondary color inheritance
  let secondaryColor: BodyColor | undefined;
  if (genes.secondaryColor && (parent1.secondaryColor || parent2.secondaryColor)) {
    const sec1 = parent1.secondaryColor || parent1.bodyColor;
    const sec2 = parent2.secondaryColor || parent2.bodyColor;
    secondaryColor = expressBodyColor(genes.secondaryColor, sec1, sec2);
  } else if (Math.random() > 0.7) {
    // Small chance of mutation
    secondaryColor = ALL_BODY_COLORS[Math.floor(Math.random() * ALL_BODY_COLORS.length)];
  }

  return {
    bodyColor,
    finType,
    pattern,
    size,
    behavior,
    secondaryColor,
  };
}

// Calculate trait probabilities for breeding pair
export function calculateBreedingProbabilities(pair: BreedingPair): TraitProbabilities {
  const { mother, father } = pair;

  // This is a simplified calculation - a full Punnett square would be more accurate
  const bodyColorProbs: Record<BodyColor, number> = {} as any;
  const finTypeProbs: Record<FinType, number> = {} as any;
  const patternProbs: Record<Pattern, number> = {} as any;
  const sizeProbs: Record<Size, number> = {} as any;
  const behaviorProbs: Record<Behavior, number> = {} as any;

  // Calculate probabilities based on parent phenotypes
  // In a real implementation, this would analyze all possible gamete combinations
  ALL_BODY_COLORS.forEach(color => {
    bodyColorProbs[color] = 0;
    if (color === mother.phenotype.bodyColor) bodyColorProbs[color] += 0.4;
    if (color === father.phenotype.bodyColor) bodyColorProbs[color] += 0.4;
    if (mother.phenotype.secondaryColor === color || father.phenotype.secondaryColor === color) {
      bodyColorProbs[color] += 0.1;
    }
  });

  ALL_FIN_TYPES.forEach(fin => {
    finTypeProbs[fin] = 0;
    if (fin === mother.phenotype.finType) finTypeProbs[fin] += 0.45;
    if (fin === father.phenotype.finType) finTypeProbs[fin] += 0.45;
  });

  ALL_PATTERNS.forEach(pat => {
    patternProbs[pat] = 0;
    if (pat === mother.phenotype.pattern) patternProbs[pat] += 0.45;
    if (pat === father.phenotype.pattern) patternProbs[pat] += 0.45;
  });

  ALL_SIZES.forEach(s => {
    sizeProbs[s] = 0;
    if (s === mother.phenotype.size) sizeProbs[s] += 0.45;
    if (s === father.phenotype.size) sizeProbs[s] += 0.45;
  });

  ALL_BEHAVIORS.forEach(b => {
    behaviorProbs[b] = 0;
    if (b === mother.phenotype.behavior) behaviorProbs[b] += 0.45;
    if (b === father.phenotype.behavior) behaviorProbs[b] += 0.45;
  });

  // Normalize probabilities
  const normalize = (probs: Record<string, number>) => {
    const total = Object.values(probs).reduce((a, b) => a + b, 0);
    Object.keys(probs).forEach(key => {
      probs[key] = total > 0 ? probs[key] / total : 0;
    });
  };

  normalize(bodyColorProbs);
  normalize(finTypeProbs);
  normalize(patternProbs);
  normalize(sizeProbs);
  normalize(behaviorProbs);

  return {
    bodyColor: bodyColorProbs,
    finType: finTypeProbs,
    pattern: patternProbs,
    size: sizeProbs,
    behavior: behaviorProbs,
  };
}

// Breed two fish
export function breedFish(pair: BreedingPair, numberOfOffspring: number = 3): BreedingResult {
  const { mother, father } = pair;
  const offspring: Fish[] = [];

  for (let i = 0; i < numberOfOffspring; i++) {
    // Inherit genes from parents
    const genes: Genes = {
      bodyColor: inheritGene(mother.genes.bodyColor, father.genes.bodyColor),
      finType: inheritGene(mother.genes.finType, father.genes.finType),
      pattern: inheritGene(mother.genes.pattern, father.genes.pattern),
      size: inheritGene(mother.genes.size, father.genes.size),
      behavior: inheritGene(mother.genes.behavior, father.genes.behavior),
    };

    // Inherit secondary color if either parent has one
    if (mother.genes.secondaryColor || father.genes.secondaryColor) {
      genes.secondaryColor = inheritGene(
        mother.genes.secondaryColor || mother.genes.bodyColor,
        father.genes.secondaryColor || father.genes.bodyColor
      );
    }

    // Small chance of mutation (new secondary color)
    if (Math.random() > 0.85 && !genes.secondaryColor) {
      genes.secondaryColor = createRandomGene();
    }

    const phenotype = calculatePhenotype(genes, mother.phenotype, father.phenotype);

    const baby: Fish = {
      id: `fish_${Date.now()}_${i}_${Math.random().toString(36).substr(2, 9)}`,
      name: `Baby ${i + 1}`,
      genes,
      phenotype,
      generation: Math.max(mother.generation, father.generation) + 1,
      parents: {
        mother: mother.id,
        father: father.id,
      },
      birthDate: Date.now(),
      age: 0,
      value: calculateFishValue(phenotype, Math.max(mother.generation, father.generation) + 1),
      achievements: [],
      isFavorite: false,
    };

    offspring.push(baby);
  }

  const probabilities = calculateBreedingProbabilities(pair);

  return {
    offspring,
    probabilities,
  };
}

// Generate a starter fish with random traits
export function generateStarterFish(name: string = 'Starter Fish'): Fish {
  const genes: Genes = {
    bodyColor: createRandomGene(),
    finType: createRandomGene(),
    pattern: createRandomGene(),
    size: createRandomGene(),
    behavior: createRandomGene(),
  };

  if (Math.random() > 0.6) {
    genes.secondaryColor = createRandomGene();
  }

  const phenotype = calculatePhenotype(genes);

  return {
    id: `fish_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    name,
    genes,
    phenotype,
    generation: 0,
    birthDate: Date.now(),
    age: 0,
    value: calculateFishValue(phenotype, 0),
    achievements: [],
    isFavorite: false,
  };
}

// Calculate fish value based on rarity
export function calculateFishValue(phenotype: Phenotype, generation: number): number {
  let value = 100;

  // Rarer colors are more valuable
  const colorRarity = {
    black: 5, purple: 4, pink: 4, teal: 3, white: 3,
    blue: 2, green: 2, red: 1, orange: 1, yellow: 1,
  };
  value += (colorRarity[phenotype.bodyColor] || 1) * 50;

  // Fancy fins are valuable
  const finRarity = { crown: 5, veil: 4, double: 3, split: 2, long: 1, normal: 0 };
  value += (finRarity[phenotype.finType] || 0) * 40;

  // Complex patterns are valuable
  const patternRarity = { koi: 5, marble: 4, gradient: 3, striped: 2, spotted: 1, solid: 0 };
  value += (patternRarity[phenotype.pattern] || 0) * 35;

  // Size bonus
  if (phenotype.size === 'large') value += 30;

  // Secondary color bonus
  if (phenotype.secondaryColor) value += 100;

  // Generation bonus
  value += generation * 20;

  return Math.round(value);
}
