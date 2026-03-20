"""International producer agent module for the EcoWHEATaly model.

Defines the InternationalProducer agent representing a world-region
wheat producer (e.g., North America, Eastern Europe). Each producer
manages its stock, performs monthly market sessions to find the
equilibrium price, and harvests once per year.
"""
from repast4py import core
from typing import Tuple
import pandas as pd
import numpy as np
import params
class InternationalProducer(core.Agent):
    """Repast4py agent representing an international wheat producer.

    Each producer holds a wheat stock that decreases with monthly
    sales and increases at harvest. During market sessions, it
    aggregates demand from all buyers and finds the equilibrium
    price where aggregate demand equals available supply.

    Attributes:
        TYPE: Agent type identifier used by repast4py context.
    """
#    global verboseFlag
    TYPE = 3
    def __init__(self, local_id: int, rank: int,my_params,initial_price):
        """Initialize an InternationalProducer agent.

        Args:
            local_id: Unique identifier for the agent within this rank.
            rank: MPI rank on which this agent resides.
            my_params: Producer parameters including area name,
                coordinates, gather month, and annual production.
            initial_price: Starting average price used to build the
                aggregate demand schedule price grid.
        """
        super().__init__(id=local_id, type=InternationalProducer.TYPE, rank=rank)
        self.rank=rank
        self.area_name=my_params['Area']
        self.latitude=my_params['lat']
        self.longitude=my_params['lon']
        self.gatherMonth=my_params['GatherMonth']
        self.production=my_params['Prod.2020']
        self.stock=round((self.production/12)*(self.gatherMonth-1))
        if self.stock==0: self.stock=self.production
        self.domestic_demand=None
        self.supply=None
        pstep=10
        n_back_steps=5
        start_price=initial_price-pstep*n_back_steps
        end_price=initial_price+pstep*n_back_steps
        prices=np.arange(start_price,end_price+1,pstep)
        self.aggregate_demand=pd.DataFrame(0,index=prices,columns=['quantity'])
        self.equilibrium_price=None
        self.sold_quantity=None
        self.exchanged_quantities=pd.DataFrame(columns=['area','quantity'])

        if params.verboseFlag: print("hello from international producer "+str(self.uid)+" I am in rank "+str(rank)+' '+self.area_name,'latitude',str(self.latitude),'longitude',str(self.longitude),'gather month',str(self.gatherMonth),'production',str(self.production),'stock',self.stock)

    def updateStockAtInitialization(self):
        """Recalculate initial stock based on production and gather month.

        Used by Italy to overwrite the default FAOSTAT-based stock
        after the model replaces Italian production with simulated
        farm output.
        """
        self.stock=round((self.production/12)*(self.gatherMonth-1))
        if self.stock==0: self.stock=self.production
        if params.verboseFlag: print("hello from international producer "+str(self.uid)+" I am in rank "+str(self.rank)+' '+self.area_name,'latitude',str(self.latitude),'longitude',str(self.longitude),'gather month',str(self.gatherMonth),'production',str(self.production),'stock',self.stock)

    def updateStock(self,delta):
        """Apply a proportional change to stock and production.

        Args:
            delta: Fractional change to apply (e.g., -0.05 for a
                5% reduction).
        """
        self.stock=(1+delta)*self.stock
        self.production=(1+delta)*self.production


    def performMarketSession(self,tmpcontext):
        """Perform a monthly market session and find the equilibrium price.

        Collects linear demand functions from all international buyers,
        aggregates them into a demand schedule, and finds the price at
        which aggregate demand equals available monthly supply. Computes
        exchanged quantities per buyer and updates the stock. For Italy,
        also updates the policy maker's price history.

        Args:
            tmpcontext: The simulation Model instance providing access
                to the repast4py context and schedule.
        """
        #print()
        if params.verboseFlag: print('=========',self.area_name,'=========')
        current_month=tmpcontext.runner.schedule.tick%12+1
        if current_month<=self.gatherMonth:
            months_left=self.gatherMonth-current_month+1            
        else:
            months_left=12-(current_month-self.gatherMonth)+1
        if params.verboseFlag: print('current month',current_month,'harvest month',self.gatherMonth,'months left',months_left)

        #supply=round(self.production/12)
        supply=round(self.stock/months_left)
        if params.verboseFlag: print('stock',self.stock,'this month supply',supply)
        #retrieve buyers
        int_buyers=tmpcontext.context.agents(agent_type=2)
        #retrieve average price
        row_of_average_price=self.aggregate_demand.shape[0]//2
        average_price=self.aggregate_demand.index[row_of_average_price]
        #prepare to store intercepts and slopes of buyers demands
        data_from_buyers=pd.DataFrame(columns=['area','intercept','slope'])
        #compute intercepts and slopes
        for tmpbuy in int_buyers:
            tmp_demand=tmpbuy.answerDemandQueryFromProducer(self.area_name)
            tmp_demand_at_av_price=tmp_demand['demand at average price']
            tmp_higher_demand=tmp_demand['higher demand']
            #if tmp_higher_demand>0 and tmp_demand_at_av_price>0:
            if tmp_higher_demand>0 and tmp_demand_at_av_price>0:
                tmp_demand_elasticity=tmp_demand['demand elasticity']
                #tmp_lower_price=average_price/((-tmp_demand_elasticity*((tmp_demand_at_av_price-tmp_higher_demand)/tmp_higher_demand))+1)
                tmp_lower_price=average_price*(1-tmp_demand_elasticity*((tmp_higher_demand-tmp_demand_at_av_price)/tmp_demand_at_av_price))
                tmp_slope=round((tmp_demand_at_av_price-tmp_higher_demand)/(average_price-tmp_lower_price),2)
                tmp_intercept=round(tmp_demand_at_av_price-tmp_slope*average_price,2)
                #proof1=round(tmp_intercept+tmp_slope*average_price)
                #proof2=round(tmp_intercept+tmp_slope*tmp_lower_price)
                #print(f"{self.area_name} received demand data from {tmpbuy.area_name}: av dem {tmp_demand_at_av_price} higher dem {tmp_higher_demand} dem el {tmp_demand_elasticity} slope {tmp_slope} intercept {tmp_intercept}")
            else:
                 tmp_slope=0           
                 tmp_intercept=0
            data_from_buyers.loc[len(data_from_buyers)]=[tmpbuy.area_name,tmp_intercept,tmp_slope]
        #if self.area_name == 'Oceania':
        #    print(data_from_buyers)
        #CUMULATES DEMANDS
        #print(self.aggregate_demand)
        prices=self.aggregate_demand.index
        self.aggregate_demand['quantity']=0
        for idx in data_from_buyers.index:
            tmp_slope=data_from_buyers.loc[idx,'slope']
            tmp_intercept=data_from_buyers.loc[idx,'intercept']
            #print('AAA',str(tmp_slope),'  ',str(tmp_intercept))
            for pt in prices:
                delta=round(tmp_intercept+tmp_slope*pt)
                if delta <0:
                    delta=0
                self.aggregate_demand.loc[pt,'quantity']+=delta
                #if self.area_name=='Oceania':
                #    print(data_from_buyers.loc[idx,'area'],' ',delta)
        #print(self.aggregate_demand['quantity'].to_numpy())
        #FIND EQUILIBRIUM PRICE
        positionsgt=sum(self.aggregate_demand['quantity']>supply)
        low_q=self.aggregate_demand.iloc[positionsgt,0]
        high_q=self.aggregate_demand.iloc[positionsgt-1,0]
        high_p=self.aggregate_demand.index[positionsgt]
        low_p=self.aggregate_demand.index[positionsgt-1]
        q_share=(supply-low_q)/(high_q-low_q)
        #equilibrium_price=low_p+q_share*(high_p-low_p)
        self.equilibrium_price=round(high_p-q_share*(high_p-low_p),3)
        #print(low_q,' ',high_q)
        if params.verboseFlag: print('equilibrium price ',self.equilibrium_price)
        #print(self.aggregate_demand)
        if params.verboseFlag: print(self.area_name,'performing market session. price',self.equilibrium_price)

        #COMPUTE EXCHANGED QUANTITIES USING DEMAND FUNCTIONS
        exchanged_quantities=pd.DataFrame(columns=['area','quantity'])
        for idx in data_from_buyers.index:
            tmp_exchanged=round(data_from_buyers.loc[idx,'intercept']+data_from_buyers.loc[idx,'slope']*self.equilibrium_price)
            exchanged_quantities.loc[len(exchanged_quantities)]=[data_from_buyers.loc[idx,'area'],tmp_exchanged]
        exchanged_quantities.set_index('area',inplace=True)
        self.exchanged_quantities=exchanged_quantities.copy()

        self.sold_quantity=self.exchanged_quantities['quantity'].sum()
        self.stock-=self.sold_quantity
        #print('sold',self.sold_quantity)
        #print('stock',self.stock)
        #print(self.exchanged_quantities)
        #Italy add latest price to policymaker prices list
        if self.area_name=='Italy':
            tmpPolicy=list(tmpcontext.context.agents(agent_type=1))[0]
            tmpPolicy.updateItalianPricesHystory(self.equilibrium_price)


    def harvestIfgatherMonth(self,tmpcontext):
        """Add annual production to stock if the current month is the gather month.

        Italy is excluded because its production is managed separately
        by the Italian farm sub-model.

        Args:
            tmpcontext: The simulation Model instance providing access
                to the schedule tick.
        """
        #print()
        #print('=========',self.area_name,'=========')
        #print('supply',round(self.production/12))
        #print('domestic dem',round(self.domestic_demand/12))
        current_month=tmpcontext.runner.schedule.tick%12+1
        if current_month==self.gatherMonth and self.area_name != 'Italy':
            self.stock+=self.production

    def save(self) -> Tuple:
        """Serialize the agent state for MPI communication.

        Returns:
            The agent's unique identifier tuple ``(id, type, rank)``.
        """
        return self.uid

    def print_status(self):
        """Print a short status message identifying this agent."""
        return print("I am an international producer")
 
