# simulation/logger.py
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, Optional

CSV_COLUMNS = [
    "week","role","customer_demand","stage_demand","order_placed","shipment_sent",
    "inventory_start","backlog_start","inventory_end","backlog_end",
    "holding_cost","backlog_cost","production_cost","total_cost","cumulative_cost",
    "scenario","policy","control","seed","tier_control","tier_policy",
]


class Logger:
    def __init__(self, path: str = "logs/game.csv"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # run-level meta
        self.scenario: str = "UNKNOWN"
        self.policy: str = "UNKNOWN"
        self.control: str = "UNKNOWN"
        self.seed: Optional[int] = None

        # per-tier meta
        self.control_mode: Dict[str, str] = {}
        self.ai_policies: Dict[str, str] = {}

        # ensure file exists with header
        if not self.path.exists():
            self._reset_file()

    def _reset_file(self) -> None:
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            w.writeheader()

    def start_new_run(self, config: Dict[str, Any]) -> None:
        """Call once when a new game starts to store meta + reset CSV header."""
        self.scenario = str(config.get("scenario", "UNKNOWN"))

        self.control_mode = dict(config.get("control_mode", {}))
        self.ai_policies = dict(config.get("ai_policies", {}))

        # control label
        humans = [r for r, m in self.control_mode.items() if str(m).upper() == "HUMAN"]
        if len(humans) == 0:
            self.control = "ALL_AI"
        elif len(humans) == len(self.control_mode):
            self.control = "ALL_HUMAN"
        else:
            self.control = "MIXED_HUMAN"

        # policy label (global)
        uniq = {self.ai_policies.get(r) for r in self.ai_policies.keys() if self.ai_policies.get(r) is not None}
        self.policy = (list(uniq)[0] if len(uniq) == 1 else "MIXED") or "UNKNOWN"

        # seed
        seed_mode = str(config.get("random_seed_mode", "")).upper()
        seed_val = config.get("random_seed_value", None)
        self.seed = int(seed_val) if seed_mode == "FIXED" and seed_val is not None else None

        # fresh file for this run
        self._reset_file()

    def _meta_for_role(self, role: str) -> Dict[str, Any]:
        tier_control = str(self.control_mode.get(role, "AI")).upper()
        tier_policy = "HUMAN" if tier_control == "HUMAN" else (self.ai_policies.get(role) or self.policy)

        return {
            "scenario": self.scenario,
            "policy": self.policy,
            "control": self.control,
            "seed": self.seed if self.seed is not None else "",
            "tier_control": tier_control,
            "tier_policy": tier_policy,
        }

    def log_week(
        self,
        *,
        week: int,
        customer_demand: int,
        stage_demand: Dict[str, int],
        orders: Dict[str, int],
        shipments: Dict[str, int],
        inv_start: Dict[str, int],
        bl_start: Dict[str, int],
        inv_end: Dict[str, int],
        bl_end: Dict[str, int],
        holding_cost: Dict[str, float],
        backlog_cost: Dict[str, float],
        production_cost: Dict[str, float],
        total_cost: Dict[str, float],
        cumulative_cost: Dict[str, float],
    ) -> None:
        """Write 4 rows (one per role) for this completed week."""
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)

            for role in ["retailer", "distributor", "wholesaler", "factory"]:
                row = {
                    "week": week,
                    "role": role,
                    "customer_demand": customer_demand,
                    "stage_demand": int(stage_demand.get(role, 0)),
                    "order_placed": int(orders.get(role, 0)),
                    "shipment_sent": int(shipments.get(role, 0)),
                    "inventory_start": int(inv_start.get(role, 0)),
                    "backlog_start": int(bl_start.get(role, 0)),
                    "inventory_end": int(inv_end.get(role, 0)),
                    "backlog_end": int(bl_end.get(role, 0)),
                    "holding_cost": float(holding_cost.get(role, 0.0)),
                    "backlog_cost": float(backlog_cost.get(role, 0.0)),
                    "production_cost": float(production_cost.get(role, 0.0)),
                    "total_cost": float(total_cost.get(role, 0.0)),
                    "cumulative_cost": float(cumulative_cost.get(role, 0.0)),
                }
                row.update(self._meta_for_role(role))

                # enforce exact column order
                out = {k: row.get(k, "") for k in CSV_COLUMNS}
                w.writerow(out)
