
import numpy as np

class DemandGenerator:
    def __init__(self):
        self.scenario="step"

    def set_scenario(self,sc):
        self.scenario=sc

    def next_week(self,week):
        if self.scenario=="step":
            return 4 if week<5 else 8
        if self.scenario=="poisson":
            return int(np.random.poisson(6))
        if self.scenario=="trend_noise":
            return max(0,int(4+0.4*week+np.random.normal(0,1)))
        return 4
