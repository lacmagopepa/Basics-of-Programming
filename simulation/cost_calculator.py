
class CostCalculator:
    def __init__(self,hold=1.0,back=5.0):
        self.hold=hold
        self.back=back
    def holding_cost(self,inv):
        return self.hold*max(0,inv)
    def backlog_cost(self,bl):
        return self.back*max(0,bl)
