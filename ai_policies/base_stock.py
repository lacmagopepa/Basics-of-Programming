
class BaseStockPolicy:
    def __init__(self,target=20):
        self.target=target
    def compute_order(self,inv,bl):
        return max(0,self.target-inv+bl)
