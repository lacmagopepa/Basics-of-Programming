
from ai_policies.base_stock import BaseStockPolicy
from ai_policies.pi import PIController

class PolicyManager:
    def __init__(self):
        self.policies={
            "BASE_STOCK":BaseStockPolicy(),
            "PI":PIController(),
        }
    def get_policy(self,name):
        return self.policies.get(name,self.policies["BASE_STOCK"])
