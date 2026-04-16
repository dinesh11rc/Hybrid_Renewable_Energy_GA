import random

POP_SIZE = 40
GENERATIONS = 100

def get_region_weights(region_type):
    """
    Returns weights for (Cost, Grid Dependency, Reliability Risk, Carbon Emission)
    """
    if region_type == "Hospital":
        return 0.5, 2.0, 10.0, 1.0  # Reliability highest
    elif region_type == "Rural Village":
        return 1.0, 8.0, 2.0, 1.0   # Grid independence highest
    elif region_type == "Apartment Complex":
        return 5.0, 1.0, 1.0, 0.5   # Cost saving highest
    elif region_type == "Police Station":
        return 0.5, 3.0, 8.0, 0.5   # Reliability + Night Backup
    elif region_type == "Smart Campus":
        return 3.0, 2.0, 1.0, 5.0   # Carbon emission and cost balance
    else: # Individual House
        return 4.0, 1.0, 0.5, 2.0   # Cost + renewable usage priority

def fitness(chromosome, grid_cost, demand, battery_cap, region_type):
    solar_use, wind_use, battery_use, grid_use = chromosome
    
    w1, w2, w3, w4 = get_region_weights(region_type)
    
    cost_score = grid_use * grid_cost
    grid_dependency_score = grid_use
    
    renewable_used = solar_use + wind_use + battery_use
    total_supply = renewable_used + grid_use
    
    # Reliability Risk penalties
    unmet_demand_penalty = abs(total_supply - demand) * 10 if total_supply < demand else 0
    # Strict penalty if battery drained below 20%
    battery_safe_reserve = battery_cap * 0.2
    battery_risk_penalty = max(0, battery_use - (battery_cap - battery_safe_reserve)) * 5
    
    reliability_score = unmet_demand_penalty + battery_risk_penalty
    carbon_score = grid_use * 0.75 # 0.75 kg CO2 per kWh grid average
    
    fitness_score = (w1 * cost_score) + (w2 * grid_dependency_score) + (w3 * reliability_score) + (w4 * carbon_score)
    fitness_score -= (0.5 * renewable_used) # Reward for renewables
    
    return fitness_score

def create_population(solar_avail, wind_avail, battery_cap, demand):
    population = []
    for _ in range(POP_SIZE):
        solar = random.uniform(0, solar_avail)
        wind = random.uniform(0, wind_avail)
        battery = random.uniform(0, battery_cap)
        grid = max(0, demand - (solar + wind + battery))
        
        total = solar + wind + battery + grid
        if total < demand:
            grid = demand - (solar + wind + battery)
            
        population.append([solar, wind, battery, grid])
    return population

def crossover(parent1, parent2):
    cut = random.randint(1, len(parent1) - 1)
    return parent1[:cut] + parent2[cut:]

def mutate(chromosome, solar_avail, wind_avail, battery_cap, demand, mutation_rate=0.2):
    if random.random() < mutation_rate:
        idx = random.randint(0, 2)
        perturbation = random.uniform(-0.15, 0.15)
        
        if idx == 0:
            chromosome[0] = max(0, min(solar_avail, chromosome[0] * (1 + perturbation)))
        elif idx == 1:
            chromosome[1] = max(0, min(wind_avail, chromosome[1] * (1 + perturbation)))
        else:
            chromosome[2] = max(0, min(battery_cap, chromosome[2] * (1 + perturbation)))
            
        chromosome[3] = max(0, demand - (chromosome[0] + chromosome[1] + chromosome[2]))
    return chromosome

def generate_recommendations(region_type, solar_use, wind_use, battery_use, grid_use, battery_cap, demand, solar_avail, wind_avail, battery_charge_percent):
    reasoning = []
    
    if solar_use > 0:
        if solar_avail >= demand * 0.5:
            reasoning.append("☀️ Solar generation high → maximizing solar energy utilization.")
        else:
            reasoning.append("☀️ Utilizing available solar energy to offset grid demand.")
            
    if wind_use > 0:
         reasoning.append("💨 Wind output available → including wind in supply mix.")
         
    battery_action = "idle"
    if battery_use > battery_cap * 0.1:
        battery_action = "discharge"
    elif battery_charge_percent < 30 and solar_avail + wind_avail > demand:
        battery_action = "charge"
        
    if region_type == "Hospital":
        reasoning.append("🏥 Hospital Mode: Reliability is top priority.")
        if battery_charge_percent < 80:
             reasoning.append("⚠️ Recommendation: Maintain battery above 80% for critical backups.")
        if grid_use > 0:
             reasoning.append("🔌 Utilizing grid to preserve local battery capacity for emergencies.")
             
    elif region_type == "Apartment Complex":
        reasoning.append("🏢 Apartment Mode: Cost optimization is prioritized.")
        if solar_avail > demand:
             reasoning.append("💡 Recommendation: Shift heavy loads to daytime to capitalize on solar peak.")
        if battery_action == "charge":
             reasoning.append("🔋 Charging battery with cheap solar to minimize peak tariff usage tonight.")
             
    elif region_type == "Rural Village":
        reasoning.append("🏡 Village Mode: Grid independence is prioritized.")
        if solar_avail > demand:
             reasoning.append("🔋 Storing excess solar to ensure reliable power during night hours.")
        if grid_use < demand * 0.2:
             reasoning.append("🌟 Successfully operating with high grid independence.")
             
    elif region_type == "Police Station":
        reasoning.append("🚓 Police Station Mode: Security systems require uninterrupted power.")
        reasoning.append("🛡️ Prioritizing night backup capability over minor cost savings.")
        
    elif region_type == "Smart Campus":
        reasoning.append("🎓 Smart Campus Mode: Balancing carbon reduction and cost.")
        if grid_use > 0:
             reasoning.append("🌱 Consider shifting non-essential HVAC loads to reduce grid carbon impact.")
             
    else: # Individual House
        reasoning.append("🏠 Individual House Mode: Cost and renewable usage prioritized.")
        if solar_use == solar_avail and grid_use > 0:
             reasoning.append("💡 Recommendation: Limit large appliance usage to reduce grid cost.")

    if battery_action == "discharge":
         reasoning.append("🔋 Discharging battery to meet demand.")
    elif battery_action == "charge":
         reasoning.append("🔋 Charging battery for future use.")
         
    if grid_use > 0 and 'grid' not in ' '.join(reasoning).lower():
        reasoning.append(f"🔌 Importing {round(grid_use, 2)} kW from grid to meet remaining demand.")
        
    return battery_action, reasoning

def genetic_algorithm_optimize(solar_avail, wind_avail, battery_cap, demand, grid_cost, region_type="Individual House", battery_charge_percent=50.0):
    population = create_population(solar_avail, wind_avail, battery_cap, demand)
    evolution_history = []
    
    for generation in range(GENERATIONS):
        fitness_scores = [fitness(ind, grid_cost, demand, battery_cap, region_type) for ind in population]
        sorted_pop = sorted(zip(population, fitness_scores), key=lambda x: x[1])
        population = [ind for ind, _ in sorted_pop]
        
        elite_count = max(2, POP_SIZE // 3)
        new_population = population[:elite_count].copy()
        
        while len(new_population) < POP_SIZE:
            parent1 = population[random.randint(0, elite_count - 1)]
            parent2 = population[random.randint(0, elite_count - 1)]
            child = crossover(parent1, parent2)
            child = mutate(child, solar_avail, wind_avail, battery_cap, demand)
            new_population.append(child)
            
        population = new_population
        best_current_fitness = min(fitness(ind, grid_cost, demand, battery_cap, region_type) for ind in population)
        evolution_history.append({"generation": generation + 1, "cost": round(best_current_fitness, 2)})
        
    population.sort(key=lambda x: fitness(x, grid_cost, demand, battery_cap, region_type))
    best_solution = population[0]
    
    solar_use, wind_use, battery_use, grid_use = best_solution
    battery_action, reasoning = generate_recommendations(
        region_type, solar_use, wind_use, battery_use, grid_use, 
        battery_cap, demand, solar_avail, wind_avail, battery_charge_percent
    )
    
    return best_solution, evolution_history, battery_action, reasoning
