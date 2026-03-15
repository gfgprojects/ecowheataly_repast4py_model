from repast4py import core
from typing import Tuple
import pandas as pd
import params
class PolicyMaker(core.Agent):
#    global verboseFlag
    TYPE = 1
    def __init__(self, local_id: int, rank: int,pricesHyst,policies_df):
        super().__init__(id=local_id, type=PolicyMaker.TYPE, rank=rank)
        self.rank=rank
        self.italianPricesHystory=pricesHyst
        self.policies=policies_df
        if params.verboseFlag: print("hello from Policy Maker "+str(self.id)+" I am in rank "+str(rank))

    def updateItalianPricesHystory(self,latestPrice):
        self.italianPricesHystory.append(latestPrice)
        if len(self.italianPricesHystory)>12:
            del self.italianPricesHystory[0]

    def save(self) -> Tuple:
        return (self.uid,self.italianPricesHystory,self.policies)
    #used to update the ghosts when it does not need to be recreated
    #arguments are taken from the return of the save function. The first element of the save return tuple is the first argument;
    #the second element of the save return function is the second argument and so on ...
    def update(self,italian_ph,italian_policies):
        self.italianPricesHystory=italian_ph
        self.policies=italian_policies
    def print_status(self):
        return print("I am the Policy Maker")
 
