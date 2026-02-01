# persistence/analysis_tools.py
from __future__ import annotations

import csv
from typing import Dict, List, Any

from config import LOG_PATH, ROLES


def _var(xs: List[float]) -> float:
    xs = list(xs)
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def compute_report(path: str = LOG_PATH) -> Dict[str, Any] | None:
    """Parse the weekly CSV log and compute KPI report + time series for plotting."""
    try:
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return None

    if not rows:
        return None

    def _get_int(row, keys, default=0):
        for k in keys:
            if k in row and row[k] not in (None, ""):
                try:
                    return int(float(row[k]))
                except Exception:
                    pass
        return default

    def _get_float(row, keys, default=0.0):
        for k in keys:
            if k in row and row[k] not in (None, ""):
                try:
                    return float(row[k])
                except Exception:
                    pass
        return default

    weeks = sorted({int(float(r.get("week", 0))) for r in rows if r.get("week") is not None})
    by_role: Dict[str, Dict[int, Dict[str, float]]] = {r: {} for r in ROLES}

    customer_demand_by_week = {w: 0 for w in weeks}

    for r in rows:
        role = r.get("role")
        if role not in by_role:
            continue
        w = int(float(r.get("week", 0)))

        # Backward compatible: old schema had 'demand', 'order', 'shipment', 'inv', 'bl', 'cost'
        customer_demand = _get_int(r, ["customer_demand", "demand"], 0)
        customer_demand_by_week[w] = customer_demand

        by_role[role][w] = {
            "stage_demand": _get_int(r, ["stage_demand"], 0),
            "order": _get_int(r, ["order_placed", "order"], 0),
            "ship": _get_int(r, ["shipment_sent", "shipment"], 0),
            "inv_end": _get_int(r, ["inventory_end", "inv"], 0),
            "bl_end": _get_int(r, ["backlog_end", "bl"], 0),
            "total_cost": _get_float(r, ["total_cost", "cost"], 0.0),
            "cumulative_cost": _get_float(r, ["cumulative_cost"], 0.0),
        }

    # time series
    customer_demand = [customer_demand_by_week[w] for w in weeks]
    orders = {r: [by_role[r].get(w, {}).get("order", 0) for w in weeks] for r in ROLES}
    inventory = {r: [by_role[r].get(w, {}).get("inv_end", 0) for w in weeks] for r in ROLES}
    backlog = {r: [by_role[r].get(w, {}).get("bl_end", 0) for w in weeks] for r in ROLES}
    weekly_cost = {r: [by_role[r].get(w, {}).get("total_cost", 0.0) for w in weeks] for r in ROLES}

    # totals
    role_totals = {}
    for r in ROLES:
        last_cum = 0.0
        for w in weeks:
            last_cum = by_role[r].get(w, {}).get("cumulative_cost", last_cum)
        total_cost = last_cum if last_cum > 0 else float(sum(weekly_cost[r]))
        avg_inv = (sum(inventory[r]) / len(inventory[r])) if weeks else 0.0
        avg_bl = (sum(backlog[r]) / len(backlog[r])) if weeks else 0.0
        role_totals[r] = {
            "total_cost": total_cost,
            "avg_inv": avg_inv,
            "avg_bl": avg_bl,
        }

    total_cost_all = sum(role_totals[r]["total_cost"] for r in ROLES)

    # service level (fill rate at customer) ≈ shipped from retailer / customer demand
    shipped_to_customer = sum(by_role["retailer"].get(w, {}).get("ship", 0) for w in weeks)
    total_customer_demand = sum(customer_demand)
    service_level = (shipped_to_customer / total_customer_demand) if total_customer_demand > 0 else 0.0

    # bullwhip: Var(orders placed by tier) / Var(customer demand)
    v_demand = _var([float(x) for x in customer_demand])
    bullwhip = {}
    for r in ROLES:
        vr = _var([float(x) for x in orders[r]])
        bullwhip[r] = (vr / v_demand) if v_demand > 0 else 0.0

    # attach bullwhip into per-tier totals
    for r in ROLES:
        role_totals[r]["bullwhip"] = bullwhip.get(r, 0.0)

    return {
        "weeks": weeks,
        "customer_demand": customer_demand,
        "orders": orders,
        "inventory": inventory,
        "backlog": backlog,
        "weekly_cost": weekly_cost,
        "role_totals": role_totals,
        "total_cost_all": total_cost_all,
        "service_level": service_level,
        "bullwhip": bullwhip,
    }


def compute_bullwhip_and_cost(path: str = LOG_PATH) -> Dict[str, Dict]:
    """Backward-compatible helper for older EndScreen code."""
    rep = compute_report(path)
    if not rep:
        return {"bullwhip": {}, "cost_totals": {}}
    cost_totals = {r: rep["role_totals"][r]["total_cost"] for r in ROLES}
    return {"bullwhip": rep["bullwhip"], "cost_totals": cost_totals}


def compute_bullwhip_vs_demand(path: str = LOG_PATH) -> Dict[str, float]:
    """Compute bullwhip ratio per tier as Var(order_placed) / Var(customer_demand)."""
    rep = compute_report(path)
    if not rep:
        return {r: 0.0 for r in ROLES}

    demand = [float(x) for x in rep.get("customer_demand", [])]
    v_d = _var(demand)
    out: Dict[str, float] = {}
    for r in ROLES:
        o = [float(x) for x in rep["orders"].get(r, [])]
        v_o = _var(o)
        out[r] = (v_o / v_d) if v_d > 0 else 0.0
    return out

