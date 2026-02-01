# simulation/simulation_engine.py
from __future__ import annotations

from dataclasses import dataclass
from collections import deque
import math
import random
from typing import Dict, Deque

from simulation.logger import Logger


# Roles used everywhere
ROLES = ["retailer", "distributor", "wholesaler", "factory"]


@dataclass
class TierUIState:
    # Start-of-week (what the player should see BEFORE ordering)
    inventory: int = 0
    backlog: int = 0

    # This week's incoming order (retailer: customer demand)
    incoming_order: int = 0

    # Shipment that arrived at start of THIS week (already credited in inventory above)
    incoming_ship_now: int = 0

    # Future arrivals (3-slot pipeline)
    incoming_ship_t1: int = 0  # arrives next week (t+1)
    incoming_ship_t2: int = 0  # arrives in 2 weeks (t+2)

    # Last week result snapshot
    ship_out_last: int = 0
    order_last: int = 0
    inv_end_last: int = 0
    bl_end_last: int = 0
    holding_cost_last: float = 0.0
    backlog_cost_last: float = 0.0
    production_cost_last: float = 0.0
    total_cost_last: float = 0.0

    # Cumulative totals
    holding_cost_total: float = 0.0
    backlog_cost_total: float = 0.0
    production_cost_total: float = 0.0
    cumulative_cost: float = 0.0


@dataclass
class TierRuntime:
    name: str
    inventory: int
    backlog: int

    # Pipelines hold FUTURE events (after week-start has been applied)
    # shipments[0] => arrives next week (t+1) - simplified: only 1 future slot
    # orders[0]    => arrives next week (t+1)
    incoming_shipments: Deque[int]
    incoming_orders: Deque[int]

    # last processed week snapshot
    last_ship_out: int = 0
    last_order: int = 0
    last_inv_end: int = 0
    last_bl_end: int = 0
    last_holding_cost: float = 0.0
    last_backlog_cost: float = 0.0
    last_production_cost: float = 0.0
    last_total_cost: float = 0.0

    cumulative_cost: float = 0.0
    cumulative_holding_cost: float = 0.0
    cumulative_backlog_cost: float = 0.0
    cumulative_production_cost: float = 0.0


class SimulationEngine:
    """Beer Game simulation with correct week timing.

    Week timing (classic):
    - At the **start** of each week, shipments arrive and orders become visible.
    - Players then place their orders.
    - The week is processed (shipping, scheduling, costs), then week advances.

    With info_lt=1 and ship_lt=1:
      Order placed in week 1 is visible upstream in week 2,
      shipped in week 2,
      and credited to downstream inventory at the **start of week 3**.
    """

    def __init__(self):
        self.config = None

        self.duration = 25
        self.week = 1

        self.ship_lt = 1
        self.info_lt = 1

        self.order_handling = "BACKORDER"
        self.cost_holding = 1.0
        self.cost_backorder = 5.0
        self.cost_production = 1.0

        self.control_mode: Dict[str, str] = {r: "HUMAN" for r in ROLES}
        self.ai_policies: Dict[str, str] = {}
        self.pi_params = {"alpha": 0.5, "beta": 0.3, "gamma": 0.1}
        self.target_inventory = 12

        self.scenario = "STEP"
        self.noise_amplitude = 2.0

        self.rng = random.Random(42)
        self.current_demand = 4

        self.tiers: Dict[str, TierRuntime] = {}
        self._init_tiers(initial_inventory={r: 12 for r in ROLES})

        # Week-start caches (refreshed by _begin_week())
        self._arriving_now: Dict[str, int] = {r: 0 for r in ROLES}
        self._stage_demand_now: Dict[str, int] = {r: 0 for r in ROLES}

        self.logger = Logger()

        # Prepare the very first week so UI sees the correct start-of-week state
        self.current_demand = self._generate_customer_demand(self.week)
        self._begin_week()

    # -----------------------------
    # Configuration
    # -----------------------------
    def set_game_configuration(self, config: dict):
        self.config = config

        self.duration = int(config.get("duration", 25))
        self.week = 1

        # Accept both formats:
        # - lead_times: {shipping, information}  (used by your config screen)
        # - ship_lt / info_lt (older tests/scripts)
        lead = config.get("lead_times", None)
        if isinstance(lead, dict):
            ship = lead.get("shipping", 1)
            info = lead.get("information", 1)
        else:
            ship = config.get("ship_lt", 1)
            info = config.get("info_lt", 1)

        # Enforce >= 1 to match “1 week info + 1 week ship” minimum
        self.ship_lt = max(1, int(ship))
        self.info_lt = max(1, int(info))
        self.scenario = config.get("scenario", "STEP")
        self.noise_amplitude = float(config.get("noise_amplitude", 2.0))

        self.control_mode = config.get("control_mode", {r: "HUMAN" for r in ROLES})
        self.ai_policies = config.get("ai_policies", {})
        self.pi_params = config.get("pi_params", {"alpha": 0.5, "beta": 0.3, "gamma": 0.1})
        self.target_inventory = int(config.get("target_inventory", 12))

        self.order_handling = config.get("order_handling", "BACKORDER")
        costs = config.get("costs", {})
        self.cost_holding = float(costs.get("holding", 1.0))
        self.cost_backorder = float(costs.get("backorder", 5.0))
        self.cost_production = float(costs.get("production", 1.0))

        # RNG
        seed_mode = str(config.get("random_seed_mode", "FIXED")).upper()
        seed_value = int(config.get("random_seed_value", 42))
        self.rng = random.Random() if seed_mode == "RANDOM" else random.Random(seed_value)

        init_inv = config.get("initial_inventory", {r: 12 for r in ROLES})
        self._init_tiers(initial_inventory=init_inv)

        self.logger = Logger()  # fresh log for this run
        self.current_demand = self._generate_customer_demand(self.week)
        self.logger.start_new_run(config)

        # prepare week 1 for UI
        self._begin_week()

    def _init_tiers(self, initial_inventory: Dict[str, int]):
        self.tiers = {}

        # 3-slot pipeline: [now, t+1, t+2]
        ship_len = 3
        info_len = max(int(self.info_lt) + 1, 3)

        for r in ROLES:
            # Initialize with steady-state shipments (4 units/week baseline)
            # Represents shipments already in transit before game starts
            init_ship = [0 for _ in range(ship_len)]
            if ship_len > 1:
                init_ship[1] = 4  # Initial t+1 shipment
            if ship_len > 2:
                init_ship[2] = 4  # Initial t+2 shipment
            ship_pipe = deque(init_ship, maxlen=ship_len)
            order_pipe = deque([0 for _ in range(info_len)], maxlen=info_len)

            self.tiers[r] = TierRuntime(
                name=r,
                inventory=int(initial_inventory.get(r, 12)),
                backlog=0,
                incoming_shipments=ship_pipe,
                incoming_orders=order_pipe,
            )

    # -----------------------------
    # Demand scenarios
    # -----------------------------
    def _generate_customer_demand(self, week: int) -> int:
        if self.scenario == "STEP":
            return 8 if week >= 5 else 4

        if self.scenario == "POISSON":
            lam = 6.0
            L = math.exp(-lam)
            k = 0
            p = 1.0
            while p > L:
                k += 1
                p *= self.rng.random()
            return max(0, k - 1)

        if self.scenario == "TREND_NOISE":
            base = 4.0 + 0.4 * week
            noise = self.rng.gauss(0, self.noise_amplitude)
            return max(0, int(round(base + noise)))

        return 4

    # -----------------------------
    # AI Policies
    # -----------------------------
    def _inventory_position(self, tier: TierRuntime) -> int:
        # on-hand + incoming shipments - backlog
        return tier.inventory + sum(tier.incoming_shipments) - tier.backlog

    def _ai_order(self, role: str, tier: TierRuntime) -> int:
        pol = self.ai_policies.get(role, "BASE_STOCK")
        inv_pos = self._inventory_position(tier)
        target = self.target_inventory

        if pol == "BASE_STOCK":
            return max(0, target - inv_pos)

        if pol == "PI":
            a = float(self.pi_params.get("alpha", 0.5))
            b = float(self.pi_params.get("beta", 0.3))
            raw = a * (target - inv_pos) + b * (tier.backlog)
            return max(0, int(round(raw)))

        return max(0, target - inv_pos)

    # -----------------------------
    # Week start processing
    # -----------------------------
    def _begin_week(self) -> None:
        """Apply arrivals and reveal orders for the *current* week.

        After this runs:
        - inventory is already credited with shipments arriving this week
        - _stage_demand_now contains this week's observed demand per tier
        - incoming_shipments deque holds future shipments only (t+1)
        - incoming_orders deque holds future orders only (based on info_lt)
        """

        self._arriving_now = {r: 0 for r in ROLES}
        self._stage_demand_now = {r: 0 for r in ROLES}

        # shipments arrive
        for r in ROLES:
            t = self.tiers[r]
            arrived = t.incoming_shipments.popleft() if len(t.incoming_shipments) > 0 else 0
            t.incoming_shipments.append(0)
            t.inventory += int(arrived)
            self._arriving_now[r] = int(arrived)

        # orders become visible
        for r in ROLES:
            t = self.tiers[r]
            if r == "retailer":
                self._stage_demand_now[r] = int(self.current_demand)
            else:
                dem = t.incoming_orders.popleft() if len(t.incoming_orders) > 0 else 0
                t.incoming_orders.append(0)
                self._stage_demand_now[r] = int(dem)
        
        # Pre-calculate and display future shipments based on current inventory
        # This shows what will be shipped, constrained by actual inventory available
        downstream_of = {
            "factory": "wholesaler",
            "wholesaler": "distributor", 
            "distributor": "retailer",
            "retailer": None,
        }
        
        # Clear the position that will be used for pre-scheduling (but not in Week 1)
        # In Week 1, we keep the initial steady-state shipments
        if self.week > 1:
            delay_index = max(0, self.ship_lt - 1)
            for r in ROLES:
                tier = self.tiers[r]
                if len(tier.incoming_shipments) > delay_index:
                    tier.incoming_shipments[delay_index] = 0
        
        for r in ROLES:
            if r == "retailer":
                continue  # Retailer doesn't ship to anyone
            
            tier = self.tiers[r]
            demand = int(self._stage_demand_now.get(r, 0))
            
            # Calculate what CAN be shipped: min(inventory, backlog + demand)
            need = int(tier.backlog) + demand
            can_ship = min(int(tier.inventory), need)
            
            # Schedule this shipment downstream for display
            dn = downstream_of[r]
            
            if dn is not None and can_ship > 0:
                self._schedule_shipment(dn, can_ship)

    # -----------------------------
    # Main step (process current week)
    # -----------------------------
    def next_week(self, orders: Dict[str, int]) -> bool:
        """Process the current week and advance to the next.
        
        Internally processes 7 days to complete the week.
        Returns False when the game ends (after processing the last week).
        """
        if self.week > self.duration:
            return False
        
        # start-of-week snapshots (already after receiving this week's shipments)
        inv_start = {r: int(self.tiers[r].inventory) for r in ROLES}
        bl_start = {r: int(self.tiers[r].backlog) for r in ROLES}

        incoming_orders_now = dict(self._stage_demand_now)

        # 1) ship to downstream (satisfy backlog + current incoming order)
        ship_out = {r: 0 for r in ROLES}
        for r in ROLES:
            tier = self.tiers[r]
            demand = int(incoming_orders_now.get(r, 0))

            need = int(tier.backlog) + demand
            can_ship = min(int(tier.inventory), need)
            tier.inventory -= can_ship

            if self.order_handling == "LOST_SALES":
                tier.backlog = 0
            else:
                tier.backlog = need - can_ship

            ship_out[r] = int(can_ship)

        inv_end = {r: int(self.tiers[r].inventory) for r in ROLES}
        bl_end = {r: int(self.tiers[r].backlog) for r in ROLES}

        # 2) Shipments were already scheduled in _begin_week() based on available inventory
        # No need to schedule again here

        # 3) each role decides order to upstream (human or AI)
        order_to_upstream = {r: 0 for r in ROLES}
        for r in ROLES:
            tier = self.tiers[r]
            if str(self.control_mode.get(r, "HUMAN")).upper() == "HUMAN":
                order_to_upstream[r] = max(0, int(orders.get(r, 0)))
            else:
                order_to_upstream[r] = self._ai_order(r, tier)

        # 4) push orders upstream into info pipelines
        upstream_of = {
            "retailer": "distributor",
            "distributor": "wholesaler",
            "wholesaler": "factory",
            "factory": None,
        }
        for r in ROLES:
            up = upstream_of[r]
            if up is not None:
                self._schedule_order(up, order_to_upstream[r])

        # 5) factory production (1-week production delay)
        self._schedule_factory_production(incoming_orders_now.get("factory", 0))

        # 6) costs + snapshot
        holding_cost = {}
        backlog_cost = {}
        production_cost = {}
        total_cost = {}
        cumulative = {}

        for r in ROLES:
            tier = self.tiers[r]

            # Holding cost on inventory BEFORE this week's shipment arrival
            inv_before_arrival = inv_start[r] - int(self._arriving_now.get(r, 0))
            holding = self.cost_holding * inv_before_arrival
            backc = self.cost_backorder * int(tier.backlog)
            prod = self.cost_production * (int(incoming_orders_now.get("factory", 0)) if r == "factory" else 0)
            total = holding + backc + prod

            tier.cumulative_cost += total
            tier.cumulative_holding_cost += holding
            tier.cumulative_backlog_cost += backc
            tier.cumulative_production_cost += prod

            tier.last_ship_out = int(ship_out[r])
            tier.last_order = int(order_to_upstream[r])
            tier.last_inv_end = int(tier.inventory)
            tier.last_bl_end = int(tier.backlog)
            tier.last_holding_cost = float(holding)
            tier.last_backlog_cost = float(backc)
            tier.last_production_cost = float(prod)
            tier.last_total_cost = float(total)

            holding_cost[r] = float(holding)
            backlog_cost[r] = float(backc)
            production_cost[r] = float(prod)
            total_cost[r] = float(total)
            cumulative[r] = float(tier.cumulative_cost)

        if getattr(self, "logger", None):
            self.logger.log_week(
                week=int(self.week),
                customer_demand=int(self.current_demand),
                stage_demand=incoming_orders_now,
                orders=order_to_upstream,
                shipments=ship_out,
                inv_start=inv_start,
                bl_start=bl_start,
                inv_end=inv_end,
                bl_end=bl_end,
                holding_cost=holding_cost,
                backlog_cost=backlog_cost,
                production_cost=production_cost,
                total_cost=total_cost,
                cumulative_cost=cumulative,
            )

        # End condition: stop immediately after processing the last programmed week
        is_last_week = self.week >= self.duration

        # Advance week
        self.week += 1
        self.current_demand = self._generate_customer_demand(self.week)

        if is_last_week:
            return False

        # Prepare next week for UI (arrivals + visible orders)
        self._begin_week()
        return True

    def _schedule_shipment(self, role_receiving: str, qty: int):
        tier = self.tiers[role_receiving]
        if len(tier.incoming_shipments) == 0:
            return

        # Week-based scheduling with 3-position pipeline [0,1,2]:
        # Position [0] = t+1 → arrives next week
        # Position [1] = t+2 → arrives in 2 weeks  
        # Position [2] = t+3 → arrives in 3 weeks
        # 
        # ship_lt=1: schedule to position [0] → displays as t+1 → arrives in 1 week
        # ship_lt=2: schedule to position [1] → displays as t+2 → arrives in 2 weeks
        # For 2-week total delay: info_lt=1 week + ship_lt=1 week = 2 weeks
        delay_index = min(max(0, self.ship_lt - 1), len(tier.incoming_shipments) - 1)
        
        tier.incoming_shipments[delay_index] += max(0, int(qty))

    def _schedule_order(self, role_receiving: str, qty: int):
        tier = self.tiers[role_receiving]
        if len(tier.incoming_orders) == 0:
            return

        # Week-based: info_lt determines weeks to visibility
        # info_lt=1 week: arrives next week, so index 0
        weeks_delay = max(0, self.info_lt - 1)
        delay_index = min(weeks_delay, len(tier.incoming_orders) - 1)
        tier.incoming_orders[delay_index] += max(0, int(qty))

    def _schedule_factory_production(self, qty: int):
        tier = self.tiers["factory"]
        if len(tier.incoming_shipments) == 0:
            return
        # Production arrives next week
        tier.incoming_shipments[0] += max(0, int(qty))

    # -----------------------------
    # UI State
    # -----------------------------
    def get_state(self) -> dict:
        tiers_ui: Dict[str, TierUIState] = {}
        
        # Map to find upstream tier for realistic arrival prediction
        upstream_of = {
            "retailer": "distributor",
            "distributor": "wholesaler",
            "wholesaler": "factory",
            "factory": None,
        }

        for r in ROLES:
            t = self.tiers[r]

            # After _begin_week(), pipeline holds future arrivals only
            # Show actual deque contents - no capping or modification
            ship_t1 = t.incoming_shipments[0] if len(t.incoming_shipments) > 0 else 0
            ship_t2 = t.incoming_shipments[1] if len(t.incoming_shipments) > 1 else 0

            tiers_ui[r] = TierUIState(
                inventory=int(t.inventory),
                backlog=int(t.backlog),

                incoming_order=int(self._stage_demand_now.get(r, 0)),
                incoming_ship_now=int(self._arriving_now.get(r, 0)),
                incoming_ship_t1=int(ship_t1),
                incoming_ship_t2=int(ship_t2),

                ship_out_last=int(t.last_ship_out),
                order_last=int(t.last_order),
                inv_end_last=int(t.last_inv_end),
                bl_end_last=int(t.last_bl_end),
                holding_cost_last=float(t.last_holding_cost),
                backlog_cost_last=float(t.last_backlog_cost),
                production_cost_last=float(t.last_production_cost),
                total_cost_last=float(t.last_total_cost),

                holding_cost_total=float(t.cumulative_holding_cost),
                backlog_cost_total=float(t.cumulative_backlog_cost),
                production_cost_total=float(t.cumulative_production_cost),
                cumulative_cost=float(t.cumulative_cost),
            )

        return {
            "week": int(self.week),
            "duration": int(self.duration),
            "demand": int(self.current_demand),
            "tiers": tiers_ui,
        }
