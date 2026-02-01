
class TierState:
    def __init__(self,name):
        self.name=name
        self.inventory=12
        self.backlog=0
        self.pipeline=[4,4]
        self.last_demand_observed=0
        self.last_order_received=0
        self.last_order_placed=0
        self.last_shipment_received=0
        self.last_shipment_sent=0
        self.last_holding_cost=0
        self.last_backlog_cost=0
        self.total_cost=0

    def process_week(self,downstream_order,order_override,cost_calc):
        arriving=self.pipeline.pop(0)
        self.inventory+=arriving
        self.pipeline.append(0)
        self.last_shipment_received=arriving

        self.last_demand_observed=downstream_order
        self.last_order_received=downstream_order

        total_demand=downstream_order+self.backlog
        shipped=min(self.inventory,total_demand)
        self.inventory-=shipped
        self.backlog=max(0,total_demand-shipped)
        self.last_shipment_sent=shipped

        order_up=max(0,int(order_override))
        self.last_order_placed=order_up
        self.pipeline[-1]+=order_up

        h=cost_calc.holding_cost(self.inventory)
        b=cost_calc.backlog_cost(self.backlog)
        self.last_holding_cost=h
        self.last_backlog_cost=b
        self.total_cost+=h+b

        return order_up
