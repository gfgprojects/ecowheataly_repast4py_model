"""Policy maker agent module for the EcoWHEATaly model.

Defines the PolicyMaker agent that tracks Italian wheat market
prices and manages the set of agri-environmental policies available
to farms (eco-schemes and SRA interventions).
"""
from repast4py import core
from typing import Tuple
import pandas as pd
import params
class PolicyMaker(core.Agent):
    """Repast4py agent representing the Italian policy maker.

    The policy maker maintains a rolling history of Italian wheat
    prices and holds the DataFrame of available agri-environmental
    policies with their parameters (payments, input effects,
    administrative costs). It is shared across MPI ranks via the
    ghost agent mechanism.

    Attributes:
        TYPE: Agent type identifier used by repast4py context.
    """
#    global verboseFlag
    TYPE = 1
    def __init__(self, local_id: int, rank: int,pricesHyst,policies_df):
        """Initialize a PolicyMaker agent.

        Args:
            local_id: Unique identifier for the agent within this rank.
            rank: MPI rank on which this agent resides.
            pricesHyst: List of recent Italian wheat prices (up to 12).
            policies_df: DataFrame of agri-environmental policies with
                columns for payment, input effects, and admin costs.
        """
        super().__init__(id=local_id, type=PolicyMaker.TYPE, rank=rank)
        self.rank=rank
        self.italianPricesHystory=pricesHyst
        self.policies=policies_df
        if params.verboseFlag: print("hello from Policy Maker "+str(self.id)+" I am in rank "+str(rank))

    def updateItalianPricesHystory(self,latestPrice):
        """Append the latest wheat price and keep the last 12 entries.

        Args:
            latestPrice: Most recent Italian wheat equilibrium price.
        """
        self.italianPricesHystory.append(latestPrice)
        if len(self.italianPricesHystory)>12:
            del self.italianPricesHystory[0]

    def save(self) -> Tuple:
        """Serialize the agent state for MPI communication.

        Returns:
            A tuple of ``(uid, italianPricesHystory, policies)``
            used by ``restore_agent`` to reconstruct the agent.
        """
        return (self.uid,self.italianPricesHystory,self.policies)

    def update(self,italian_ph,italian_policies):
        """Update the ghost agent state without full reconstruction.

        Called during MPI synchronization to refresh the ghost copy
        of this agent on remote ranks.

        Args:
            italian_ph: Updated list of Italian wheat prices.
            italian_policies: Updated policies DataFrame.
        """
        self.italianPricesHystory=italian_ph
        self.policies=italian_policies
    def print_status(self):
        """Print a short status message identifying this agent."""
        return print("I am the Policy Maker")
 
