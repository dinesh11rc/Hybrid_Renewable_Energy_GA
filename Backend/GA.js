/**
 * Genetic Algorithm for Campus Hybrid Energy Optimization
 * Standalone module for testing and integration
 */

// ========== GA CONFIGURATION ==========
const GA_CONFIG = {
    DEMAND: 60,              // Total campus demand in kW
    SOLAR_AVAIL: 35,         // Available solar generation in kW
    WIND_AVAIL: 20,          // Available wind generation in kW
    BATTERY_CAP: 10,         // Battery storage capacity in kW
    GRID_COST: 6,            // Grid electricity cost in ₹/kWh
    
    POP_SIZE: 40,            // Population size (larger = more accurate, slower)
    GENERATIONS: 100,        // Number of generations to evolve
    MUTATION_RATE: 0.2,      // Probability of mutation (0-1)
    ELITE_PERCENTAGE: 0.3,   // Top % to keep each generation
    
    // Carbon emissions factor
    CARBON_GRID: 750,        // grams CO2 per kWh (grid)
    CARBON_RENEWABLE: 0      // grams CO2 per kWh (solar/wind)
};

// ========== UTILITY FUNCTIONS ==========

/**
 * Generate random number between min and max
 */
function randomBetween(min, max) {
    return Math.random() * (max - min) + min;
}

/**
 * Create a random chromosome (solution)
 * Format: [solar_use, wind_use, battery_use, grid_use]
 */
function createChromosome(config = GA_CONFIG) {
    const solar = randomBetween(0, config.SOLAR_AVAIL);
    const wind = randomBetween(0, config.WIND_AVAIL);
    const battery = randomBetween(0, config.BATTERY_CAP);
    
    // Calculate grid usage to meet demand
    const grid = Math.max(0, config.DEMAND - (solar + wind + battery));
    
    return [solar, wind, battery, grid];
}

// ========== FITNESS FUNCTION ==========

/**
 * Evaluate fitness of a solution
 * Lower score = better solution
 * Minimizes: grid cost and usage
 * Maximizes: renewable usage
 */
function fitness(chromosome, config = GA_CONFIG) {
    const [solar, wind, battery, grid] = chromosome;
    
    // Ensure non-negative values
    if (solar < 0 || wind < 0 || battery < 0 || grid < 0) {
        return Infinity;
    }
    
    // Cost component: grid electricity cost
    const cost = grid * config.GRID_COST;
    
    // Renewable component: encourage renewable usage
    const renewable = solar + wind + battery;
    
    // Penalty for unmet demand
    const totalSupply = renewable + grid;
    const demandPenalty = totalSupply < config.DEMAND ? 
        (config.DEMAND - totalSupply) * 10 : 0;
    
    // Penalty for exceeding battery capacity (discharge limit)
    const batteryPenalty = battery > config.BATTERY_CAP ? 
        (battery - config.BATTERY_CAP) * 5 : 0;
    
    // Composite fitness score
    // Lower is better: we want low cost, high renewable
    const score = cost + demandPenalty + batteryPenalty - (renewable * 0.2);
    
    return score;
}

// ========== GENETIC OPERATORS ==========

/**
 * Selection: Keep best individuals
 */
function select(population, config = GA_CONFIG) {
    const sorted = population
        .map((chromosome, index) => ({
            chromosome,
            fitness: fitness(chromosome, config),
            index
        }))
        .sort((a, b) => a.fitness - b.fitness);
    
    const eliteCount = Math.max(2, Math.floor(config.POP_SIZE * config.ELITE_PERCENTAGE));
    return sorted.slice(0, eliteCount).map(item => item.chromosome);
}

/**
 * Crossover: Blend two parent solutions
 * Single-point crossover
 */
function crossover(parent1, parent2) {
    if (parent1.length !== parent2.length) {
        throw new Error("Parents must have same length");
    }
    
    const cut = Math.floor(Math.random() * parent1.length);
    const child = [];
    
    for (let i = 0; i < parent1.length; i++) {
        if (i < cut) {
            child.push(parent1[i]);
        } else {
            child.push(parent2[i]);
        }
    }
    
    return child;
}

/**
 * Mutation: Randomly adjust chromosome values
 */
function mutate(chromosome, config = GA_CONFIG, mutationRate = null) {
    const rate = mutationRate || config.MUTATION_RATE;
    const mutated = [...chromosome];
    
    if (Math.random() < rate) {
        const mutationIdx = Math.floor(Math.random() * 3); // Mutate solar, wind, or battery
        const perturbation = randomBetween(-0.15, 0.15); // ±15% change
        
        switch (mutationIdx) {
            case 0: // Solar
                mutated[0] = Math.max(0, Math.min(config.SOLAR_AVAIL, mutated[0] * (1 + perturbation)));
                break;
            case 1: // Wind
                mutated[1] = Math.max(0, Math.min(config.WIND_AVAIL, mutated[1] * (1 + perturbation)));
                break;
            case 2: // Battery
                mutated[2] = Math.max(0, Math.min(config.BATTERY_CAP, mutated[2] * (1 + perturbation)));
                break;
        }
        
        // Recalculate grid to meet demand
        mutated[3] = Math.max(0, config.DEMAND - (mutated[0] + mutated[1] + mutated[2]));
    }
    
    return mutated;
}

// ========== MAIN GA ALGORITHM ==========

/**
 * Run the genetic algorithm optimization
 * Returns the best solution found
 */
function optimizeWithGA(config = GA_CONFIG, verboseLogging = false) {
    // Initialize population
    let population = Array.from({ length: config.POP_SIZE }, () => createChromosome(config));
    
    const bestFitnessHistory = [];
    
    // Evolution loop
    for (let generation = 0; generation < config.GENERATIONS; generation++) {
        // Selection: keep best individuals
        const selected = select(population, config);
        
        // Create new population starting with elite
        let newPopulation = selected.map(chromosome => [...chromosome]); // Clone elite
        
        // Reproduction: generate offspring through crossover and mutation
        while (newPopulation.length < config.POP_SIZE) {
            const parent1 = selected[Math.floor(Math.random() * selected.length)];
            const parent2 = selected[Math.floor(Math.random() * selected.length)];
            
            const child = crossover(parent1, parent2);
            const mutatedChild = mutate(child, config);
            
            newPopulation.push(mutatedChild);
        }
        
        population = newPopulation;
        
        // Track best fitness
        const bestFitness = Math.min(...population.map(chromosome => fitness(chromosome, config)));
        bestFitnessHistory.push(bestFitness);
        
        if (verboseLogging && generation % 10 === 0) {
            console.log(`Generation ${generation}: Best Fitness = ${bestFitness.toFixed(3)}`);
        }
    }
    
    // Find best solution
    const bestIndex = population.reduce((bestIdx, chromosome, idx) => {
        return fitness(chromosome, config) < fitness(population[bestIdx], config) ? idx : bestIdx;
    }, 0);
    
    const bestSolution = population[bestIndex];
    const bestFitnessValue = fitness(bestSolution, config);
    
    return {
        solution: bestSolution,
        fitness: bestFitnessValue,
        fitnessHistory: bestFitnessHistory,
        details: {
            solar: bestSolution[0],
            wind: bestSolution[1],
            battery: bestSolution[2],
            grid: bestSolution[3]
        }
    };
}

// ========== ANALYSIS FUNCTIONS ==========

/**
 * Calculate detailed metrics for a solution
 */
function analyzeSolution(solution, config = GA_CONFIG) {
    const [solar, wind, battery, grid] = solution;
    const renewable = solar + wind + battery;
    const totalSupply = renewable + grid;
    
    return {
        solar_kw: solar.toFixed(2),
        wind_kw: wind.toFixed(2),
        battery_kw: battery.toFixed(2),
        grid_kw: grid.toFixed(2),
        renewable_total_kw: renewable.toFixed(2),
        total_supply_kw: totalSupply.toFixed(2),
        demand_kw: config.DEMAND.toFixed(2),
        grid_percentage: (grid / config.DEMAND * 100).toFixed(1),
        renewable_percentage: (renewable / config.DEMAND * 100).toFixed(1),
        estimated_cost_rs: (grid * config.GRID_COST).toFixed(2),
        emissions_avoided_kg_co2: (renewable * (config.CARBON_GRID / 1000)).toFixed(2),
        demand_satisfied: totalSupply >= config.DEMAND ? "YES" : "NO"
    };
}

// ========== EXPORT FOR USE IN NODEJS OR BROWSER ==========

// Node.js export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        GA_CONFIG,
        optimizeWithGA,
        analyzeSolution,
        fitness,
        createChromosome,
        select,
        crossover,
        mutate
    };
}

// ========== STANDALONE EXECUTION ==========

// Run if executed directly
if (typeof require !== 'undefined' && require.main === module) {
    console.log("=== Hybrid Energy Genetic Algorithm Optimization ===\n");
    
    console.log("Configuration:");
    console.log(`  Demand: ${GA_CONFIG.DEMAND} kW`);
    console.log(`  Solar Max: ${GA_CONFIG.SOLAR_AVAIL} kW`);
    console.log(`  Wind Max: ${GA_CONFIG.WIND_AVAIL} kW`);
    console.log(`  Battery: ${GA_CONFIG.BATTERY_CAP} kW`);
    console.log(`  Grid Cost: ₹${GA_CONFIG.GRID_COST}/kWh\n`);
    
    console.log("Running GA Optimization...\n");
    
    const result = optimizeWithGA(GA_CONFIG, true);
    
    console.log("\n=== OPTIMIZATION RESULTS ===\n");
    
    const analysis = analyzeSolution(result.solution, GA_CONFIG);
    
    Object.entries(analysis).forEach(([key, value]) => {
        const displayKey = key.replace(/_/g, ' ').toUpperCase();
        console.log(`${displayKey}: ${value}`);
    });
    
    console.log(`\nFinal Fitness Score: ${result.fitness.toFixed(3)}`);
    console.log(`\nEvolution Progress (Best Fitness by Generation):`);
    console.log(`  Start: ${result.fitnessHistory[0].toFixed(3)}`);
    console.log(`  Mid:   ${result.fitnessHistory[Math.floor(result.fitnessHistory.length/2)].toFixed(3)}`);
    console.log(`  End:   ${result.fitnessHistory[result.fitnessHistory.length-1].toFixed(3)}`);
}

