import sys
sys.path.insert(0, r"file path")

from simulation.simulation_engine import SimulationEngine

# Create simulation with info_lt=1, ship_lt=1
sim = SimulationEngine()
config = {
    "duration": 10,
    "ship_lt": 1,
    "info_lt": 1,
    "order_handling": "BACKORDER"
}
sim.set_game_configuration(config)

def print_week_state(week_num, state):
    print(f"\n{'='*80}")
    print(f"WEEK {week_num}")
    print(f"{'='*80}")
    
    for role in ["retailer", "distributor", "wholesaler", "factory"]:
        tier = state['tiers'][role]
        print(f"\n{role.upper()}:")
        print(f"  Order={tier.order_last}, Demand={tier.incoming_order}, Inventory={tier.inventory}", end="")
        if tier.backlog > 0:
            print(f", Backlog={tier.backlog}", end="")
        print()
        print(f"  Incoming Shipments: [now={tier.incoming_ship_now}, t+1={tier.incoming_ship_t1}, t+2={tier.incoming_ship_t2}]")

print("="*80)
print("10-WEEK SIMULATION - ALL TIERS ORDER 20 UNITS/WEEK")
print("info_lt=1 week, ship_lt=1 week")
print("="*80)

# Week 1: Initial state
state = sim.get_state()
print_week_state(state['week'], state)

# Process all 10 weeks with everyone ordering 20
for week in range(1, 11):
    print(f"\n>>> Week {week}: Everyone orders 20 units <<<")
    orders = {"retailer": 20, "wholesaler": 20, "distributor": 20, "factory": 20}
    sim.next_week(orders)
    
    if week < 10:  # Show state after processing (except after week 10)
        state = sim.get_state()
        print_week_state(state['week'], state)

print("\n" + "="*80)
print("SIMULATION COMPLETE")
print("="*80)

# Get final state
state = sim.get_state()
print("\nFINAL INVENTORY LEVELS:")
for role in ["retailer", "distributor", "wholesaler", "factory"]:
    tier = state['tiers'][role]
    print(f"  {role.upper()}: Inventory={tier.inventory}, Backlog={tier.backlog}")

print("\nFINAL COSTS:")
total_system_cost = 0
for role in ["retailer", "distributor", "wholesaler", "factory"]:
    tier = state['tiers'][role]
    print(f"  {role.upper()}: ${tier.cumulative_cost:.2f}")
    total_system_cost += tier.cumulative_cost
print(f"\n  TOTAL SYSTEM COST: ${total_system_cost:.2f}")
print("="*80)
