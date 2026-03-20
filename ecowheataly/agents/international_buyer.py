"""International buyer agent module for the EcoWHEATaly model.

Defines the InternationalBuyer agent representing a world-region
wheat buyer (e.g., North Africa, Central Asia). Each buyer maintains
per-producer demand functions and evolves its buying strategy by
shifting demand from expensive to cheap producers over time.
"""
from repast4py import core
from typing import Tuple
import params
import pandas as pd
import math
class InternationalBuyer(core.Agent):
    """Repast4py agent representing an international wheat buyer.

    Each buyer is associated with a geographic area that has its own
    domestic demand and production. It maintains linear demand
    functions toward each international producer and adjusts them
    based on observed price differentials and transport costs.

    Attributes:
        TYPE: Agent type identifier used by repast4py context.
    """
#    global verboseFlag
    TYPE = 2
    def __init__(self, local_id: int, rank: int,my_params,producers_list,transport_info):
        """Initialize an InternationalBuyer agent.

        Args:
            local_id: Unique identifier for the agent within this rank.
            rank: MPI rank on which this agent resides.
            my_params: Buyer parameters including area name,
                coordinates, and domestic demand from input CSV.
            producers_list: List of international producer area names.
            transport_info: DataFrame with transport mode and distance
                from this buyer to each producer.
        """
        super().__init__(id=local_id, type=InternationalBuyer.TYPE, rank=rank)
        self.rank=rank
        self.area_name=my_params['Area']
        self.latitude=my_params['lat']
        self.longitude=my_params['lon']
        self.domestic_demand=my_params['Demand.2020']
        self.transport_info=transport_info
        self.transport_cost_per_ton_per_km_by_sea=params.transport_cost_per_ton_per_km_by_sea
        self.transport_cost_per_ton_per_km_by_land=params.transport_cost_per_ton_per_km_by_land
        self.annealing=False
        self.annealing_speed=0.05
        self.percentage_of_demand_to_move_from_expensive_to_cheap_producer=params.percentage_of_demand_to_move_from_expensive_to_cheap_producer
        self.slopeOfTheMovingFunction=-0.748
        #self.slopeOfTheMovingFunction=-0.76
        self.production=None
        self.demand_elasticity=0.5
        #self.demand_function=pd.DataFrame(index=list(producers_list),columns=range(start_price,end_price+1,pstep))
        self.demand_function=None
        self.bought_quantities=None
        if params.verboseFlag: print("hello from international buyer "+str(self.uid)+" I am in rank "+str(rank)+' '+self.area_name,'latitude',str(self.latitude),'longitude',str(self.longitude),'demand',str(self.domestic_demand))

    def initializeBuyingStrategy(self, int_availability_status):
        """Initialize demand functions toward each international producer.

        Builds per-producer linear demand functions characterized by a
        quantity at the average price, a higher-demand quantity, and an
        elasticity. Allocates import demand across producers based on
        their export market shares. Also prepares the bought-quantities
        tracking structure with transport cost information.

        Args:
            int_availability_status: DataFrame summarizing each
                producer's output, export openness, and market share.
        """
        #In this function the demand functions of a buyer directed to the various producers are initialized.
        #they are organized as a pandas data frame where each row is a producer. 
        #for each producers, the demand function is characterized by two quantities and an elasticity. 
        #Using these values, it is possible to build the linear demand function.
        #The reconstruction of the demand function is performed by producers when they perform their market session
        if params.verboseFlag: print(self.area_name,'initializing demand function')
        international_status=int_availability_status
        quantity_to_be_imported=self.domestic_demand-self.production
        #print(self.area_name,'demanded',str(self.domestic_demand),'produced',str(self.production),'needed',str(quantity_to_be_imported))
        #my_int_info=pd.DataFrame(international_status[['Area','export']],columns=['Area','export'])
        #my_int_info=pd.DataFrame(international_status[['Area','Prod.2020','export']],columns=['Area','Prod.2020','export'])
        my_int_info=international_status[['Area','Prod.2020','export']].copy()
        #assume there is not a domestic market. Will be modified later if domestic market exists
        my_int_info['domestic']=False
        #compute market shares of producers in the international market. If producer does not allow export market share is zero
        for i in my_int_info.index:
            my_int_info.loc[i,'Prod.2020']=round(international_status.loc[i,'Prod.2020']/params.market_sessions_per_year)
            my_int_info.loc[i,'open market share']=international_status.loc[i,'share']*international_status.loc[i,'export']
        my_int_info.rename(columns={'Prod.2020': 'monthly_supply'},inplace=True)
        for i in my_int_info.index:
            my_int_info.loc[i,'monthly_supply_share']=my_int_info.loc[i,'monthly_supply']/my_int_info['monthly_supply'].sum()

        #because sum of shares of market that are open could not sum to 1, we make them sum to 1
        sum_of_open_market_shares=my_int_info['open market share'].sum()
        for i in my_int_info.index:
            my_int_info.loc[i,'open market share rescaled']=my_int_info.loc[i,'open market share']/sum_of_open_market_shares
            #set the domestic market
            if my_int_info.loc[i,'Area']==self.area_name:
                my_int_info.loc[i,'domestic']=True
        #set the demand at average price
        for i in my_int_info.index:
            #to domestic market
            if my_int_info.loc[i,'domestic']:
                if quantity_to_be_imported<0:
                    my_int_info.loc[i,'demand at average price']=round(self.domestic_demand/params.market_sessions_per_year)
                    my_int_info.loc[i,'higher demand']=round(1.1*self.domestic_demand/params.market_sessions_per_year)
                else:
                    my_int_info.loc[i,'demand at average price']=round(self.production/params.market_sessions_per_year)
                    my_int_info.loc[i,'higher demand']=round(1.1*self.production/params.market_sessions_per_year)
            #to foreign markets
            else:
                if my_int_info.loc[i,'export']:
                    if quantity_to_be_imported<0:
                        my_int_info.loc[i,'demand at average price']=0
                        #my_int_info.loc[i,'higher demand']=round(0.01*quantity_to_be_imported/params.market_sessions_per_year)
                        my_int_info.loc[i,'higher demand']=0.01*self.domestic_demand/params.market_sessions_per_year
                    else:
                        if my_int_info.loc[i,'open market share rescaled']>0:
                            tmpimp=round((quantity_to_be_imported/params.market_sessions_per_year)*my_int_info.loc[i,'open market share rescaled'])
                        else:
                            tmpimp=round((0.05*quantity_to_be_imported/params.market_sessions_per_year)*my_int_info.loc[i,'monthly_supply_share'])
                        my_int_info.loc[i,'demand at average price']=tmpimp
                        my_int_info.loc[i,'higher demand']=1.1*tmpimp
                        #if tmpimp>0:
                        #    my_int_info.loc[i,'higher demand']=round(1.1*(quantity_to_be_imported/params.market_sessions_per_year)*my_int_info.loc[i,'open market share rescaled'])
                        #else:
                        #    my_int_info.loc[i,'higher demand']=round(0.01*quantity_to_be_imported/params.market_sessions_per_year)
                else:
                    my_int_info.loc[i,'demand at average price']=0
                    my_int_info.loc[i,'higher demand']=0

            my_int_info.loc[i,'demand elasticity']=self.demand_elasticity
        self.demand_function=my_int_info.copy()
        self.demand_function.set_index('Area',inplace=True)
        pd.set_option('display.max_columns', None)
        #print(my_int_info)
        #prepare the structure where the bought quantities will be recorded
        bought_quantities=pd.DataFrame(index=list(my_int_info['Area']),columns=['price','quantity','asked'])
        for idx in bought_quantities.index:
            bought_quantities.loc[idx,'price']=0
            bought_quantities.loc[idx,'quantity']=0
            bought_quantities.loc[idx,'asked']=self.demand_function.loc[idx,'demand at average price']
        bought_quantities1=pd.merge(bought_quantities,self.transport_info,left_index=True,right_index=True)
        bought_quantities1['transport_cost']=0
        bought_quantities1['price_plus_transport']=0
        bought_quantities1['transport_cost']=bought_quantities1['transport_cost'].astype(float)
        bought_quantities1['price_plus_transport']=bought_quantities1['price_plus_transport'].astype(float)
        for idx in bought_quantities1.index:
            if bought_quantities1.loc[idx,'mode']=='Sea':
                bought_quantities1.loc[idx,'transport_cost']=round(int(bought_quantities1.loc[idx,'distance_km'])*self.transport_cost_per_ton_per_km_by_sea,2)
            if bought_quantities1.loc[idx,'mode']=='Land':
                bought_quantities1.loc[idx,'transport_cost']=round(int(bought_quantities1.loc[idx,'distance_km'])*self.transport_cost_per_ton_per_km_by_land,2)
        self.bought_quantities=bought_quantities1.copy()
        #print(self.area_name)
        #print(self.demand_function)
        #print(bought_quantities1)
        #print(self.transport_info)

    def update_transport_costs(self,delta_tc):
        """Update transport cost coefficients and recalculate per-producer costs.

        Args:
            delta_tc: Increment to add to both sea and land transport
                cost coefficients (per ton per km).
        """
        self.transport_cost_per_ton_per_km_by_sea+=delta_tc
        self.transport_cost_per_ton_per_km_by_land+=delta_tc
        for idx in self.bought_quantities.index:
            if self.bought_quantities.loc[idx,'mode']=='Sea':
                self.bought_quantities.loc[idx,'transport_cost']=round(int(self.bought_quantities.loc[idx,'distance_km'])*self.transport_cost_per_ton_per_km_by_sea,2)
            if self.bought_quantities.loc[idx,'mode']=='Land':
                self.bought_quantities.loc[idx,'transport_cost']=round(int(self.bought_quantities.loc[idx,'distance_km'])*self.transport_cost_per_ton_per_km_by_land,2)
 
    def answerDemandQueryFromProducer(self,prodName):
        """Return this buyer's demand function parameters for a producer.

        Args:
            prodName: Area name of the querying producer.

        Returns:
            A pandas Series with demand at average price, higher
            demand, and demand elasticity for the given producer.
        """
        return self.demand_function.loc[prodName]
    def checkObtainedQuantitiesAndEvolveBuyingStrategy(self,tmpcontext):
        """Update buying strategy based on latest market outcomes.

        Records the equilibrium prices and exchanged quantities from
        each producer, then shifts demand from expensive to cheap
        producers using a logistic function of the price range.
        Applies optional simulated annealing to reduce the magnitude
        of demand shifts over time.

        Args:
            tmpcontext: The simulation Model instance providing access
                to the repast4py context.
        """
        int_producers=tmpcontext.context.agents(agent_type=3)
        for tmpprod in int_producers:
            self.bought_quantities.loc[tmpprod.area_name,'price']=tmpprod.equilibrium_price
            self.bought_quantities.loc[tmpprod.area_name,'price_plus_transport']=tmpprod.equilibrium_price+self.bought_quantities.loc[tmpprod.area_name,'transport_cost']
            self.bought_quantities.loc[tmpprod.area_name,'quantity']=tmpprod.exchanged_quantities.loc[self.area_name,'quantity']
        #update demand elasticity
        self.demand_elasticity=(1-0.05)*(self.demand_elasticity-0.5)+0.5
        self.demand_function['demand elasticity']=self.demand_elasticity
        #change the demand function
        #print(self.demand_function)
        #print(self.bought_quantities)
        #prepare the price quantities info
        pq_info=pd.merge(self.demand_function[['monthly_supply','open market share rescaled','demand at average price']],self.bought_quantities['price_plus_transport'],left_index=True,right_index=True)
        pq_info.sort_values('price_plus_transport',inplace=True)
        price_range=pq_info['price_plus_transport'].max()-pq_info['price_plus_transport'].min()
        #if self.area_name == 'Italy': print(pq_info)
        #moving demand from expensive to cheap markets
        total_asked_quantity=round(self.bought_quantities['asked'].sum())
        #moving a percentage of the demand
        #logistic function with possible annealing
        if self.annealing:
            self.percentage_of_demand_to_move_from_expensive_to_cheap_producer-=self.annealing_speed*self.percentage_of_demand_to_move_from_expensive_to_cheap_producer


        #percentage_of_demand_to_move=0.05/(1+math.exp(-0.8*(price_range-8.0))) #con prezzo iniziale=100
        #percentage_of_demand_to_move=self.percentage_of_demand_to_move_from_expensive_to_cheap_producer/(1+math.exp(-0.748*(price_range-8.0))) #con prezzo iniziale=95.63
        percentage_of_demand_to_move=self.percentage_of_demand_to_move_from_expensive_to_cheap_producer/(1+math.exp(self.slopeOfTheMovingFunction*(price_range-8.0))) #con prezzo iniziale=95.63
        #percentage_of_demand_to_move=0.02/(1+math.exp(-0.9*(price_range-8.0))) #con prezzo iniziale=95.63
        #percentage_of_demand_to_move=0.025/(1+math.exp(-0.9*(price_range-6.5)))
        #percentage_of_demand_to_move=0.05/(1+math.exp(-3.0*(price_range-3.0)))
        quantity_to_move=round(total_asked_quantity*percentage_of_demand_to_move)
        #print(self.area_name,percentage_of_demand_to_move,quantity_to_move)
        quantity_added_to_cheap_producers=0
        #useful device the columns order of pq_info is modified
        col_q_idx=pq_info.columns.get_indexer(['demand at average price'])[0]
        col_ms_idx=pq_info.columns.get_indexer(['monthly_supply'])[0]
        #add quantities to cheap areas
        tmp_row=0
        while quantity_added_to_cheap_producers <= quantity_to_move:
            actual_q=pq_info.iloc[tmp_row,col_q_idx]
            tmp_dq=0
            if actual_q>0:
                tmp_dq=round(actual_q*0.1)
            else:
                tmp_dq=round(pq_info.iloc[tmp_row,col_ms_idx]*0.01)
            #add quantity to cell
            pq_info.iloc[tmp_row,col_q_idx]+=tmp_dq
            quantity_added_to_cheap_producers+=tmp_dq
            tmp_row+=1
            #print(quantity_added_to_cheap_producers,'   ',quantity_to_move)

        #if self.area_name == 'Italy': print(pq_info)
        #remove excess quantity from latest update
        pq_info.iloc[tmp_row-1,col_q_idx]-=quantity_added_to_cheap_producers - quantity_to_move
        quantity_added_to_cheap_producers = quantity_to_move
        #reduce quantities to expensive areas
        pq_info.sort_values('price_plus_transport',ascending=False,inplace=True)

        quantity_decreased_to_expensive_producers=0
        tmp_row=0
        while quantity_decreased_to_expensive_producers <= quantity_to_move:
            actual_q=pq_info.iloc[tmp_row,col_q_idx]
            tmp_dq=0
            if actual_q>0:
                tmp_dq=round(actual_q*1.0)
            #remove quantity to cell
            pq_info.iloc[tmp_row,col_q_idx]-=tmp_dq
            quantity_decreased_to_expensive_producers+=tmp_dq
            tmp_row+=1
        #remove excess quantity from latest update
        pq_info.iloc[tmp_row-1,col_q_idx]+=quantity_decreased_to_expensive_producers - quantity_to_move
        quantity_decreased_to_expensive_producers = quantity_to_move
        #if self.area_name == 'Italy': print(pq_info)

        if params.verboseFlag: print(self.area_name,'updating demand function. Monthly demand:',total_asked_quantity,'to move',quantity_to_move,'bought',self.bought_quantities['quantity'].sum())
        #update demand function table
        for tmp_idx in pq_info.index:
            tmp_new_dem=pq_info.loc[tmp_idx,'demand at average price']
            if(tmp_new_dem==round(tmp_new_dem*1.1)):
                self.demand_function.loc[tmp_idx,'demand at average price']=0
                self.demand_function.loc[tmp_idx,'higher demand']=0
            else:
                self.demand_function.loc[tmp_idx,'demand at average price']=tmp_new_dem
                self.demand_function.loc[tmp_idx,'higher demand']=round(tmp_new_dem*1.1)
        #if self.area_name=='Central Asia':
        #    print(self.demand_function)



        #print(self.area_name)
        #print(self.bought_quantities)
            #print(tmpprod.area_name,tmpprod.equilibrium_price)
            #print(tmpprod.exchanged_quantities.loc[self.area_name])
        #print(self.bought_quantities['quantity'].sum())
        #print(self.bought_quantities['asked'].sum())
        #print(round(self.domestic_demand/12))
        #print(self.bought_quantities)
        #if params.verboseFlag: 
    def switchAnnealingOn(self):
        """Enable simulated annealing on demand reallocation."""
        self.annealing=True

    def switchAnnealingOff(self):
        """Disable simulated annealing on demand reallocation."""
        self.annealing=False

    def resetPercentageToMove(self,percentage):
        """Set the percentage of demand to shift between producers.

        Args:
            percentage: New demand-movement fraction (0 to 1).
        """
        self.percentage_of_demand_to_move_from_expensive_to_cheap_producer=percentage

    def resetAnnealingSpeed(self,speed):
        """Set the annealing speed for demand reallocation decay.

        Args:
            speed: New annealing speed coefficient.
        """
        self.annealing_speed=speed

    def resetDemandElasticity(self,new_elasticity):
        """Set the demand elasticity for all producer demand functions.

        Args:
            new_elasticity: New elasticity value applied to all
                demand functions.
        """
        self.demand_elasticity=new_elasticity

    def save(self) -> Tuple:
        """Serialize the agent state for MPI communication.

        Returns:
            The agent's unique identifier tuple ``(id, type, rank)``.
        """
        return self.uid

    def print_status(self):
        """Print a short status message identifying this agent."""
        return print(str(self.area_name),'I am an international buyer')
 
