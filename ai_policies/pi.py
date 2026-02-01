
class PIController:
    def __init__(self,alpha=0.6,beta=0.2):
        self.alpha=alpha
        self.beta=beta
        self.integral=0
    def compute_order(self,inv,bl):
        err=bl
        self.integral+=err
        return max(0,int(self.alpha*err+self.beta*self.integral))
