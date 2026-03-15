"""mpi4py dipende da un'implementazione di MPI
 (Message Passing Interface) per funzionare correttamente.
  Su macOS, né Conda né Pip installano automaticamente MPI,
   quindi dobbiamo farlo manualmente. Non usare conda che non funziona"""
# installare brew o aggiornarlo:
# !brew update
# ! brew upgrade
# !brew install openmpi
# !MPICC=$(which mpicc) pip install --no-cache-dir --force-reinstall mpi4py
# !CC=$(which mpicc) CXX=$(which mpicxx) pip install --no-cache-dir --force-reinstall repast4py
from mpi4py import MPI
from repast4py import context as ctx
from repast4py import core,schedule,logging
from repast4py import random as repastrandom
from typing import Tuple
import random as pyrandom
import scipy.stats as dist
from functools import partial

import os
import numpy as np
import pandas as pd

import bw2data as bd
import bw2calc as bc
 
#os.getcwd()
#os.chdir('./ecowheataly_repast4py_model')
#library_path = os.path.abspath('./')
#import sys
#sys.path.append(library_path)
#from agents import farm

import agents.farm as agfarm
import agents.policy_maker as agpm
import agents.international_buyer as agintbuyer
import agents.international_producer as agintproducer
import utils.utils as ut

import params

farm_counter=0

# questo implementa la creazione dell'ambiente parallelo
comm = MPI.COMM_WORLD
# context = core.Context(comm, "ABM_example")
#num_processes = comm.Get_size()  # Numero di processi MPI disponibili
rank = comm.Get_rank()  # Rank del processo attuale
#num_cores = os.cpu_count()  # Numero totale di core fisici/logici disponibili
international_producers_summary=None


def restore_agent(agent_data: Tuple):
    uid=agent_data[0]
    match uid[1]:
        case agfarm.Farm.TYPE:
            tmp = agfarm.Farm(uid[0],uid[2])
        case agpm.PolicyMaker.TYPE:
            tmp = agpm.PolicyMaker(uid[0],uid[2],agent_data[1],agent_data[2])
        case _:
            print("restore function: agent type not matched")
    return tmp

class Model:
    """Repast4py model"""
#    def __init__(self, comm: MPI.Intracomm, params: Dict):
    def __init__(self, comm: MPI.Intracomm):
        # create the schedule
        self.runner = schedule.init_schedule_runner(comm)
        #self.runner.schedule_repeating_event(1, 1, self.step,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1)
        #self.runner.schedule_repeating_event(1, 1, self.log_agents,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.1)
        self.switchOnItalianProduction=50
        #Schedule
        self.runner.schedule_repeating_event(1, 1, self.performInternationalMarketsSessions,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1)
        self.runner.schedule_repeating_event(1, 1, self.log_international_data,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.01)
        self.runner.schedule_repeating_event(1, 1, self.producersHarvestIfgatherMonth,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.05)
        self.runner.schedule_repeating_event(6, 12, self.performItalianProductionSystemModel,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.1)
        self.runner.schedule_repeating_event(6, 12, self.computeItalianProduction,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.2)
        self.runner.schedule_repeating_event(6, 12, self.updateItalianProductionAndStock,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.25)
        self.runner.schedule_repeating_event(6, 12, self.computeLCAindicators,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.3)
        self.runner.schedule_repeating_event(1, 1, self.buyersCheckObtainedQuantitiesAndEvolveBuyingStrategy,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.4)
        #############################
        #### increasing transport costs
        #############################
        if True:
            #self.runner.schedule_repeating_event(50, 5, self.updateInternationalBuyersTransportCosts,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.5)
            self.runner.schedule_event(50,self.updateInternationalBuyersTransportCosts,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.5)
            self.runner.schedule_event(52,self.updateInternationalBuyersTransportCosts,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.5)
            self.runner.schedule_event(54,self.updateInternationalBuyersTransportCosts,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.5)
            self.runner.schedule_event(56,self.updateInternationalBuyersTransportCosts,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.5)
            self.runner.schedule_event(58,self.updateInternationalBuyersTransportCosts,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.5)
            self.runner.schedule_event(60,self.switchOnInternationalBuyersAnnealing,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.6)
        #self.runner.schedule_event(70,self.updateInternationalBuyersTransportCosts,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.5)
        #self.runner.schedule_event(47,self.updateInternationalBuyersDemandToMovePercentage,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.5)
        #############################
        #### Policy introduction
        #############################
        self.runner.schedule_repeating_event(140,12,self.updatePolicies,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.5)
        #self.runner.schedule_event(121,self.recordFarmsData,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.6)
        self.runner.schedule_event(143,self.recordFarmsData,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.6)
        #self.runner.schedule_event(213,self.policyMakerUpdatePolicy,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.6)



        #############################
        #### Aggregate shocks events
        #############################
        if True:
            self.runner.schedule_event(200,self.updateInternationalProducerStock,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.5)

            #self.runner.schedule_event(150,self.resetInternationalBuyersAnnealingSpeed,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.55)
            self.runner.schedule_event(200,self.resetInternationalBuyersPercentageToMove,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.6)
            self.runner.schedule_event(200,self.resetInternationalBuyersDemandElasticity,priority_type=schedule.PriorityType.BY_PRIORITY,priority=1.7)
        #self.runner.schedule_stop(250)
        self.runner.schedule_stop(300)


        #self.runner.schedule_end_event(self.at_end)
        # create the context to hold the agents and manage cross process
        # synchronization
        self.context = ctx.SharedContext(comm)
        #create random seed for processes
        size = comm.Get_size()
        #by setting this seed random numbers will be the same in different runs
        #comment the following line if you want different results in different runs
        np.random.seed(59302785)
        seeds=[]
        for i in range(size):
            seeds.append(np.random.randint(1,1000000))
        rank = comm.Get_rank()
        repastrandom.init(seeds[rank])
        if params.verboseFlag: print("RANK "+str(rank))
        if params.verboseFlag: print("Random seed "+str(repastrandom.seed))
        #getting knowledge of other ranks
        otherRanks=list(range(size))
        #remove my rank from the list
        otherRanks.pop(rank)
        if params.verboseFlag: print("rank "+str(rank)+" says: ranks different from mine are "+str(otherRanks))

        all_policies=pd.read_csv('abm_input_policies.csv',index_col='name')
        policies=all_policies.loc[['eco4','sra19','sra20','sra19plus20']]
        #policies=all_policies.loc[['sra20','sra19plus20']]
        #policies=all_policies.loc['sra19plus20'].to_frame().T
        # Creating agents in rank 0: policy maker, international buyers and producers
        if(rank==0):
            if params.verboseFlag: print('Adding Policy Maker to rank 0')
            emptyPricesList=[]
            policymaker=agpm.PolicyMaker(0,rank,emptyPricesList,policies)
            if params.verboseFlag: print(policymaker.uid)
            self.context.add(policymaker)
            #international buyers and producers
            international_buyers_data=pd.read_csv('abm_input_international_buyers_with_ports.csv')
            international_producers_data=pd.read_csv('abm_input_international_producers_with_ports.csv')
            #compute a matrix called international_producers_summary to give info about wheat availability for international markets
            international_production_surplus=international_producers_data.copy()
            for i in international_producers_data.index:
                #international_production_surplus.iloc[i,7]=0
                for j in range(9,23):
                    international_production_surplus.iloc[i,j]-=international_buyers_data.iloc[i,j-1]
            global international_producers_summary
            international_producers_summary=international_producers_data[['Area','Prod.2020']].copy()
            international_producers_summary['latest']=0
            international_producers_summary['nexcesses']=0
            international_producers_summary['mean']=0
            international_producers_summary['cv']=0.0
            international_producers_summary['mean_gt_0']=0
            international_producers_summary['share']=0.0
            international_producers_summary['export']=True
            #international_producers_summary.loc[4,'export']=False
            #international_producers_summary.loc[5,'export']=False
            #Oceania
            #international_producers_summary.loc[6,'export']=False

            for i in international_producers_summary.index:
                international_producers_summary.loc[i,'latest']=international_production_surplus.iloc[i,19]
                international_producers_summary.loc[i,'nexcesses']=sum(international_production_surplus.iloc[i,17:20]>0)
                tmp_mean=round(international_production_surplus.iloc[i,17:20].mean())      
                international_producers_summary.loc[i,'mean']=tmp_mean
                if tmp_mean>0:
                    international_producers_summary.loc[i,'mean_gt_0']=tmp_mean
                else:
                    international_producers_summary.loc[i,'mean_gt_0']=0

                tmp_sd=round(international_production_surplus.iloc[i,17:20].std())
                international_producers_summary.loc[i,'cv']= tmp_sd/tmp_mean                                                 
            tot_excess_prod=international_producers_summary['mean_gt_0'].sum()
            for i in international_producers_summary.index:
                international_producers_summary.loc[i,'share']= international_producers_summary.loc[i,'mean_gt_0']/tot_excess_prod
            #create buyers and producers
            # load file with transport details
            transport_info=pd.read_csv('abm_input_buyer_producer_matrix_searoute.csv',index_col=0)
            for i in range(international_buyers_data.shape[0]):
                tmp_int_buy_data=international_buyers_data.loc[i]
                tmp_int_buy_transport_info=transport_info.loc[tmp_int_buy_data.Area].to_frame()
                tmp_int_buy_transport_info.index.name='Area'
                #rename column
                tmp_int_buy_transport_info=tmp_int_buy_transport_info.set_axis(['col0'],axis=1)
                tmp_int_buy_transport_info=tmp_int_buy_transport_info['col0'].str.split('|', expand=True)
                tmp_int_buy_transport_info=tmp_int_buy_transport_info.set_axis(['mode','distance_km'],axis=1)
                #print(tmp_int_buy_transport_info[tmp_int_buy_data.Area].str.split('|', n=1, expand=True))
                #print(tmp_int_buy_data.Area)
                #print(tmp_int_buy_transport_info)
                intbuyer=agintbuyer.InternationalBuyer(i,rank,tmp_int_buy_data,international_producers_data['Area'],tmp_int_buy_transport_info)
                self.context.add(intbuyer)
            if params.verboseFlag: print()
            for i in range(international_producers_data.shape[0]):
                tmp_int_prod_data=international_producers_data.loc[i]
                intproducer=agintproducer.InternationalProducer(i,rank,tmp_int_prod_data,params.initial_average_price)
                self.context.add(intproducer)
            #initialize quantities offered in the international market
            #get agents from the context
            international_producers=list(self.context.agents(agent_type=3))
            international_buyers=list(self.context.agents(agent_type=2))
            #set to zero domestic production for all buyers. Buyers with production will be modified in the next for loop
            for tmpbuy in international_buyers:
                tmpbuy.production=0
            for tmpprod in international_producers:
                for tmpbuy in international_buyers:
                    if (tmpprod.area_name==tmpbuy.area_name):
                        tmpprod.domestic_demand=tmpbuy.domestic_demand
                        tmpprod.supply=tmpprod.production-tmpprod.domestic_demand
                        tmpbuy.production=tmpprod.production
                if tmpprod.area_name=='Italy':
                    self.italianProducer=tmpprod


            #for tmpprod in international_producers:
            #   print(f"{tmpprod.area_name} produzione {tmpprod.production} domanda {tmpprod.domestic_demand} supply {tmpprod.supply}")
            if params.verboseFlag: print()
            self.buyersInitializeBuyingStrategy()
            if params.verboseFlag: print()
            #self.marketsPerformSessions()
            if params.verboseFlag: print()
            #self.buyersAccountConsumption()
            if params.verboseFlag: print()

        if params.verboseFlag: print('Creating Italian farms')

        #Creating Farms
        real_farms_file_exists=os.path.exists('abm_input_real_farms_'+str(rank)+'.csv')
        artificial_farms_file_exists=os.path.exists('abm_input_artificial_farms_'+str(rank)+'.csv')
        if not real_farms_file_exists and not artificial_farms_file_exists and rank > 0:
            comm.Abort(2)

        # Keeping pandas from truncating long strings
        pd.set_option('display.max_colwidth',200)
        provinces_features= pd.read_csv('abm_input_provinces_params.csv')
        #need parameter revisions for Catanzaro Pianura and Rieti Collina
        for i,row in provinces_features.iterrows():
            if row['province']=='Catanzaro' and row['altimetry']=='Pianura':
                provinces_features.loc[i,'s3']=0.4
                #provinces_features.loc[i,'max_yield']=50.0
                provinces_features.loc[i,'lambda1']=0.05
                #print(row)
            if row['province']=='Rieti' and row['altimetry']=='Collina':
                provinces_features.loc[i,'lambda1']=0.05
                #row['max_yield']=50.0
                #print(row)

        global farm_counter
        #start creating real farms
        if real_farms_file_exists:
            farmsFromRica = pd.read_csv('abm_input_real_farms_'+str(rank)+'.csv')
            for i in range(farmsFromRica.shape[0]):
                #tmp_farm_params=farmsFromRica.loc[farmsFromRica.index==i,]
                tmp_farm_params=farmsFromRica.loc[i,]
                tmp_province=farmsFromRica.loc[i,'province']
                tmp_altimetry=farmsFromRica.loc[i,'altimetry']
                tmp_prov_params=provinces_features.query("province==@tmp_province and altimetry==@tmp_altimetry")
                #create age
                age_distribution_and_params=tmp_prov_params.loc[tmp_prov_params.index,'age distribution'].to_string(index=False).split('|')
                age_distribution=None
                dist_type=age_distribution_and_params[0]
                param1=float(age_distribution_and_params[1])
                if len(age_distribution_and_params)==3:
                    param2=float(age_distribution_and_params[2])
                    age_distribution=getattr(dist,dist_type)(param1,param2)
                    #age_distribution=partial(getattr(dist,dist_type),param1,param2)
                elif len(age_distribution_and_params)==4:
                    param2=float(age_distribution_and_params[2])
                    param3=float(age_distribution_and_params[3])
                    age_distribution=getattr(dist,dist_type)(param1,param2,param3)
                    #age_distribution=partial(getattr(dist,dist_type),param1,param2,param3)
                elif len(age_distribution_and_params)==5:
                    param2=float(age_distribution_and_params[2])
                    param3=float(age_distribution_and_params[3])
                    param4=float(age_distribution_and_params[4])
                    age_distribution=getattr(dist,dist_type)(param1,param2,param3,param4)
                    #age_distribution=partial(getattr(dist,dist_type),param1,param2,param3,param4)
                else:
                    age_distribution=getattr(dist,dist_type)(param1)
                    #age_distribution=partial(getattr(dist,dist_type),param1)
                tmp_age=round(age_distribution.rvs(size=1)[0])
                if tmp_farm_params['young']=='N':
                    while tmp_age<=40 or tmp_age > age_distribution.ppf(0.9):
                        tmp_age=round(age_distribution.rvs(size=1)[0])
                if tmp_farm_params['young']=='S':
                    while tmp_age < 18 or tmp_age>40:
                        tmp_age=round(age_distribution.rvs(size=1)[0])
                tmp_farm_params['young']=tmp_age 


#print(tmp_prov_params)
                farm=agfarm.Farm(farm_counter, rank,tmp_farm_params,tmp_prov_params)
                self.context.add(farm)
                farm_counter+=1
        #end creating real farms
        
        #start creating artificial farms
        if artificial_farms_file_exists:
            artificial_farms = pd.read_csv('abm_input_artificial_farms_'+str(rank)+'.csv')
            for i in range(artificial_farms.shape[0]):
                n_farms=artificial_farms.loc[i,'n_farms']
                province=artificial_farms.loc[i,'province']
                altimetry=artificial_farms.loc[i,'altimetry']
                tmp_prov_params=provinces_features.query("province==@province and altimetry==@altimetry")
                #if province=='Rieti' and altimetry=='Collina': print(tmp_prov_params[['province','altimetry','s1']])
                #retrieve wheat acreage, farm acreage, and age distributions
                wheat_acreage_distribution_and_params=tmp_prov_params.loc[tmp_prov_params.index,'wheat acreage distribution'].to_string(index=False).split('|')
                #print('RANK '+str(rank)+' farms'+str(n_farms))
                #print(wheat_acreage_distribution_and_params)
                farm_acreage_distribution_and_params=tmp_prov_params.loc[tmp_prov_params.index,'farm acreage distribution'].to_string(index=False).split('|')
                age_distribution_and_params=tmp_prov_params.loc[tmp_prov_params.index,'age distribution'].to_string(index=False).split('|')
                ladies_prob=tmp_prov_params.loc[tmp_prov_params.index,'share of ladies'].to_list()[0]                
                #create wheat acreage distribution
                wheat_acreage_distribution=None
                dist_type=wheat_acreage_distribution_and_params[0]
                param1=float(wheat_acreage_distribution_and_params[1])
                if len(wheat_acreage_distribution_and_params)==3:
                    param2=float(wheat_acreage_distribution_and_params[2])
                    wheat_acreage_distribution=getattr(dist,dist_type)(param1,param2)
                    #wheat_acreage_distribution=partial(getattr(dist,dist_type),param1,param2)
                elif len(wheat_acreage_distribution_and_params)==4:
                    param2=float(wheat_acreage_distribution_and_params[2])
                    param3=float(wheat_acreage_distribution_and_params[3])
                    #wheat_acreage_distribution=partial(getattr(dist,dist_type),param1,param2,param3)
                    wheat_acreage_distribution=getattr(dist,dist_type)(param1,param2,param3)
                elif len(wheat_acreage_distribution_and_params)==5:
                    param2=float(wheat_acreage_distribution_and_params[2])
                    param3=float(wheat_acreage_distribution_and_params[3])
                    param4=float(wheat_acreage_distribution_and_params[4])
                    #wheat_acreage_distribution=partial(getattr(dist,dist_type),param1,param2,param3,param4)
                    wheat_acreage_distribution=getattr(dist,dist_type)(param1,param2,param3,param4)
                else:
                    #wheat_acreage_distribution=partial(getattr(dist,dist_type),param1)
                    wheat_acreage_distribution=getattr(dist,dist_type)(param1)
                #create farm acreage distribution
                farm_acreage_distribution=None
                dist_type=farm_acreage_distribution_and_params[0]
                param1=float(farm_acreage_distribution_and_params[1])
                if len(farm_acreage_distribution_and_params)==3:
                    param2=float(farm_acreage_distribution_and_params[2])
                    farm_acreage_distribution=getattr(dist,dist_type)(param1,param2)
                    #farm_acreage_distribution=partial(getattr(dist,dist_type),param1,param2)
                elif len(farm_acreage_distribution_and_params)==4:
                    param2=float(farm_acreage_distribution_and_params[2])
                    param3=float(farm_acreage_distribution_and_params[3])
                    farm_acreage_distribution=getattr(dist,dist_type)(param1,param2,param3)
                    #farm_acreage_distribution=partial(getattr(dist,dist_type),param1,param2,param3)
                elif len(farm_acreage_distribution_and_params)==5:
                    param2=float(farm_acreage_distribution_and_params[2])
                    param3=float(farm_acreage_distribution_and_params[3])
                    param4=float(farm_acreage_distribution_and_params[4])
                    farm_acreage_distribution=getattr(dist,dist_type)(param1,param2,param3,param4)
                    #farm_acreage_distribution=partial(getattr(dist,dist_type),param1,param2,param3,param4)
                else:
                    farm_acreage_distribution=getattr(dist,dist_type)(param1)
                    #farm_acreage_distribution=partial(getattr(dist,dist_type),param1)
                #create age acreage distribution
                age_distribution=None
                dist_type=age_distribution_and_params[0]
                param1=float(age_distribution_and_params[1])
                if len(age_distribution_and_params)==3:
                    param2=float(age_distribution_and_params[2])
                    age_distribution=getattr(dist,dist_type)(param1,param2)
                    #age_distribution=partial(getattr(dist,dist_type),param1,param2)
                elif len(age_distribution_and_params)==4:
                    param2=float(age_distribution_and_params[2])
                    param3=float(age_distribution_and_params[3])
                    age_distribution=getattr(dist,dist_type)(param1,param2,param3)
                    #age_distribution=partial(getattr(dist,dist_type),param1,param2,param3)
                elif len(age_distribution_and_params)==5:
                    param2=float(age_distribution_and_params[2])
                    param3=float(age_distribution_and_params[3])
                    param4=float(age_distribution_and_params[4])
                    age_distribution=getattr(dist,dist_type)(param1,param2,param3,param4)
                    #age_distribution=partial(getattr(dist,dist_type),param1,param2,param3,param4)
                else:
                    age_distribution=getattr(dist,dist_type)(param1)
                    #age_distribution=partial(getattr(dist,dist_type),param1)


                #generate features for each firm calling the created distributions
                scaling_factor_f=1.26
                scaling_factor_w=3.65
                tmp_prob_f=farm_acreage_distribution.cdf(0.5)
                tmp_prob_w=wheat_acreage_distribution.cdf(0.5)
                for i in range(n_farms):
                    tmp_farm_acreage=round(scaling_factor_f*farm_acreage_distribution.rvs(size=1)[0],2)
                    while tmp_farm_acreage < farm_acreage_distribution.ppf(tmp_prob_f) or tmp_farm_acreage > scaling_factor_f*farm_acreage_distribution.ppf(0.975) or tmp_farm_acreage<0:
                        tmp_farm_acreage=round(scaling_factor_f*farm_acreage_distribution.rvs(size=1)[0],2)
                    tmp_wheat_acreage=round(scaling_factor_w*wheat_acreage_distribution.rvs(size=1)[0],2)
                    while tmp_wheat_acreage < wheat_acreage_distribution.ppf(tmp_prob_w) or tmp_wheat_acreage > scaling_factor_w*wheat_acreage_distribution.ppf(0.975):
                        tmp_wheat_acreage=round(scaling_factor_w*wheat_acreage_distribution.rvs(size=1)[0],2)
                    if tmp_farm_acreage<tmp_wheat_acreage or tmp_wheat_acreage<0:
                        tmp_wheat_acreage=round(repastrandom.default_rng.uniform(low=0.05)*tmp_farm_acreage,2)
                    if tmp_wheat_acreage<0.5:
                        tmp_wheat_acreage=0.5
                    #if tmp_wheat_acreage<tmp_farm_acreage*0.1:
                    #    tmp_wheat_acreage=round(tmp_farm_acreage*0.1,2)
                    tmp_age=round(age_distribution.rvs(size=1)[0])
                    while tmp_age < 18 or tmp_age > age_distribution.ppf(0.9):
                        tmp_age=round(age_distribution.rvs(size=1)[0])
                    tmp_gender='M'
                    if repastrandom.default_rng.random()<ladies_prob:
                        tmp_gender='F'
                    #tmp_young='N'
                    #if tmp_age<40:
                    #    tmp_young='S'

                    tmp_cluster=0
                    tmp_farm_params_df=pd.DataFrame([['0000000000000000000',province,altimetry,tmp_wheat_acreage,tmp_farm_acreage,tmp_gender,tmp_age,tmp_cluster,rank]],columns=['farm code','province','altimetry','crop_acreage','farm_acreage','gender','young','clusters','rank'])
                    tmp_farm_params=tmp_farm_params_df.loc[0,]
                    if tmp_prov_params.shape[0]>0:
                        farm=agfarm.Farm(farm_counter, rank,tmp_farm_params,tmp_prov_params)
                        self.context.add(farm)
                        farm_counter+=1
        #end creating artificial farms

        if params.verboseFlag: print("setting agents to be requested to other ranks")

        ghostsToRequest=[]
#        ghostsToRequest.append(((0,0,otherRanks[0]),otherRanks[0]))
#        ghostsToRequest.append(((0,0,otherRanks[1]),otherRanks[1]))
        if params.verboseFlag: print('ranks different from 0 request policy maker')
        if(rank!=0):
            ghostsToRequest.append(((0,1,0),0))


        if params.verboseFlag: print("rank "+str(rank)+" ghostsToRequest: "+str(ghostsToRequest))
        if params.verboseFlag: print('Calling request_agents function creates the policy maker object in the rank')
        obtained_ag=self.context.request_agents(ghostsToRequest,restore_agent)
        if params.verboseFlag: print("rank "+str(rank)+" obtainded agents: "+str(obtained_ag))
        if params.verboseFlag: print("rank "+str(rank)+" ghosted agents: "+str(self.context._agent_manager._ghosted_agents))
        if params.verboseFlag: print("rank "+str(rank)+" ghost agents: "+str(self.context._agent_manager._ghost_agents))

#        print(self.context.projections)
#        print(self.context.bounded_projs)
#        print(self.context.non_bounded_projs)


       # initialize the logging
        if(rank==0):
            with open('output/aggregate_recipe_endpoint.csv', 'w') as file:
                file.write('tick,DALY,species\n')
                file.flush()
            #create headings for files wrote by rank 0 
            international_producers=list(self.context.agents(agent_type=3))
            producers_names=[]
            for ip in international_producers:
                producers_names.append(ip.area_name)
            producers_names.sort()
            pasted_producers_names=producers_names[0]
            for runner in range(1,len(producers_names)):
                pasted_producers_names=pasted_producers_names+','+producers_names[runner]
            pasted_producers_names='tick,'+pasted_producers_names+'\n'
            with open('output/aggregate_international_prices.csv', 'w') as file:
                file.write(pasted_producers_names)
                file.flush()
            with open('output/aggregate_international_producers_stocks.csv', 'w') as file:
                file.write(pasted_producers_names)
                file.flush()
            with open('output/aggregate_international_producers_sold_quantity.csv', 'w') as file:
                file.write(pasted_producers_names)
                file.flush()

       #create the file to log farms data
        output_file_name='output/farms_data.csv'
        self.agent_logger = logging.TabularLogger(comm,output_file_name, ['tick','(id,type,rank)','farm code','province','altimetry','target_yield(kg)','crop_acreage','farm_acreage','yield(kg)','production(kg)','hours_of_tractor_use','N/ha(kg)','herbicide','insecticide','daly','nspecies','policy_adopted'],delimiter=',')
       #create the file to log aggregate data
        self.aggregate_data_log = ut.AggregateData()
        loggers = logging.create_loggers(self.aggregate_data_log, op=MPI.SUM, names={'production': 'production_kg'}, rank=rank)
        loggers += logging.create_loggers(self.aggregate_data_log, op=MPI.SUM, names={'hours_of_tractor_use': 'hours_of_tractor_use'}, rank=rank)
        loggers += logging.create_loggers(self.aggregate_data_log, op=MPI.SUM, names={'nitrogen': 'nitrogen_kg'}, rank=rank)
        loggers += logging.create_loggers(self.aggregate_data_log, op=MPI.SUM, names={'herbicide': 'herbicide_kg'}, rank=rank)
        loggers += logging.create_loggers(self.aggregate_data_log, op=MPI.SUM, names={'insecticide': 'insecticide_kg'}, rank=rank)
        for tmppol in policies.index:
            loggers += logging.create_loggers(self.aggregate_data_log, op=MPI.SUM, names={tmppol: tmppol+'_ha'}, rank=rank)
        #loggers += logging.create_loggers(self.meet_log, op=MPI.MAX, names={'max_meets': 'max'}, rank=rank)
        self.aggregate_data_set = logging.ReducingDataSet(loggers, comm, 'output/aggregate_data.csv')
        #we need the italian production. Note that the self.aggregate_data_log.production reports the aggregate value of each single rank. Because we have to aggregate among ranks we need to retrieve the logger and make it perform a reduction below in the computeItalianProduction function
        self.italianProductionLogger=loggers[0]
        self.italianTractorUseLogger=loggers[1]
        self.italianNitrogenLogger=loggers[2]
        self.italianHerbicideLogger=loggers[3]
        self.italianInsecticideLogger=loggers[4]
        #substitute Italian FAOSTAT production with the production from the model 
        self.performItalianProductionSystemModel()
        #self.updatePolicies()
        #self.performItalianProductionSystemModel()
        #self.policyMakerUpdatePolicy()
        #self.updatePolicies()
        self.computeItalianProduction()
        #self.recordFarmsData()
        self.updateItalianProductionAndStock()
        self.computeLCAindicators()

    def buyersInitializeBuyingStrategy(self):
        international_buyers=list(self.context.agents(agent_type=2))
        for tmpbuy in international_buyers:
            tmpbuy.initializeBuyingStrategy(international_producers_summary)

    def policyMakerUpdatePolicy(self):
        if rank==0:
            tmp_policy_maker=self.context.agent((0,1,0))
            tmp_policy_maker.policies.loc['eco4','payment/ha']=0
            tmp_policy_maker.policies.loc['sra19','payment/ha']=0
            tmp_policy_maker.policies.loc['sra20','payment/ha']=0
            tmp_policy_maker.policies.loc['sra19plus20','payment/ha']=0
        self.context.synchronize(restore_agent)

    def performInternationalMarketsSessions(self):
        if rank==0:
            if params.verboseFlag: 
                print('=================================')
                print('tick',self.runner.schedule.tick,'rank',rank,'marketsPerformSessions')
                print('=================================')
            international_producers=list(self.context.agents(agent_type=3))
            for tmpprod in international_producers:
                tmpprod.performMarketSession(self)
        #syncronize ghosts: in this case, the ghosts of policy maker update the prices list
        self.context.synchronize(restore_agent)

    def producersHarvestIfgatherMonth(self):
        if rank==0:
            if params.verboseFlag: 
                print('=================================')
                print('tick',self.runner.schedule.tick,'rank',rank,'producersHarvestIfgatherMonth')
                print('=================================')
            international_producers=list(self.context.agents(agent_type=3))
            for tmpprod in international_producers:
                tmpprod.harvestIfgatherMonth(self)

    def buyersCheckObtainedQuantitiesAndEvolveBuyingStrategy(self):
        if rank==0:
            international_buyers=list(self.context.agents(agent_type=2))
            for tmpbuy in international_buyers:
                tmpbuy.checkObtainedQuantitiesAndEvolveBuyingStrategy(self)
    def switchOnInternationalBuyersAnnealing(self):
        if rank==0:
            international_buyers=list(self.context.agents(agent_type=2))
            for tmpbuy in international_buyers:
                tmpbuy.switchAnnealingOn()
    def resetInternationalBuyersPercentageToMove(self):
        if rank==0:
            international_buyers=list(self.context.agents(agent_type=2))
            for tmpbuy in international_buyers:
                tmpbuy.resetPercentageToMove(0.01)

    def resetInternationalBuyersAnnealingSpeed(self):
        if rank==0:
            international_buyers=list(self.context.agents(agent_type=2))
            for tmpbuy in international_buyers:
                tmpbuy.resetAnnealingSpeed(0.15)

    def resetInternationalBuyersDemandElasticity(self):
        if rank==0:
            international_buyers=list(self.context.agents(agent_type=2))
            for tmpbuy in international_buyers:
                tmpbuy.resetDemandElasticity(2.0)

    def switchOffInternationalBuyersAnnealing(self):
        if rank==0:
            international_buyers=list(self.context.agents(agent_type=2))
            for tmpbuy in international_buyers:
                tmpbuy.switchAnnealingOff()

    def updateInternationalBuyersTransportCosts(self):
        if rank==0:
            international_buyers=list(self.context.agents(agent_type=2))
            for tmpbuy in international_buyers:
                tmpbuy.update_transport_costs(0.0001)
                #tmpbuy.slopeOfTheMovingFunction-=0.05
                #tmpbuy.percentage_of_demand_to_move_from_expensive_to_cheap_producer=round(tmpbuy.percentage_of_demand_to_move_from_expensive_to_cheap_producer-0.01,4)
            #print(tmpbuy.transport_cost_per_ton_per_km_by_sea)
            #print(tmpbuy.percentage_of_demand_to_move_from_expensive_to_cheap_producer)
    def updateInternationalBuyersDemandToMovePercentage(self):
        if rank==0:
            international_buyers=list(self.context.agents(agent_type=2))
            for tmpbuy in international_buyers:
                tmpbuy.percentage_of_demand_to_move_from_expensive_to_cheap_producer=0.01
 
    def updateInternationalProducerStock(self):
        if rank==0:
            international_producers=list(self.context.agents(agent_type=3))
            for tmpprod in international_producers:
                if tmpprod.area_name == 'Eastern Europe':
                    tmpprod.updateStock(-0.0533)
        

    def interacting_with_ghosts(self):
        print("INTERACTION")
        if rank == 0:
            tmp=self.context.agent((0,1,0))
#            tmp=self.context._agent_manager._ghost_agents[(0,1,0)]
#            tmp.agent.print_status()
        else:
            tmp=self.context.ghost_agent((0,1,0))
        tmp.print_status()
        print("end_interaction")

    def performItalianProductionSystemModel(self):
        if rank>0:
            if params.verboseFlag: print('tick',self.runner.schedule.tick,'rank',rank,'performItalianProductionSystemModel')
            for farm in self.context.agents(agent_type=0):
                farm.updateWheatPrice(self)
                farm.decide_production_inputs()
                farm.perform_life_cyle_impact_assessment()
                farm.harvest()

    def updatePolicies(self):
        if rank>0:
            for farmer in self.context.agents(agent_type=0):
                farmer.keep_or_change_policy(self)

    def recordFarmsData(self):
        tick = self.runner.schedule.tick
        if rank>0:
            if params.verboseFlag: print('tick',self.runner.schedule.tick,'rank',rank,'recordFarmsData')
            for farmer in self.context.agents(agent_type=0):
                self.agent_logger.log_row(round(tick),farmer.uid,farmer.farm_code,farmer.province,farmer.altimetry,int(farmer.hat_y*100),farmer.wheat_acreage,farmer.farm_acreage,int(farmer.harvested_y*100),farmer.harvested_production,round(farmer.hours_of_tractor_use_ha_after_policy,2),round(farmer.Nitrogen_per_ha_after_policy),round(farmer.Herbicide_per_ha_after_policy,2),round(farmer.Insecticide_per_ha_after_policy,2),round(farmer.recipe_daly,4),round(farmer.recipe_species,4),farmer.policy_adopted)
        self.agent_logger.write()


    def computeItalianProduction(self):
        tick = self.runner.schedule.tick
        if rank>0:
            if params.verboseFlag: print('tick',self.runner.schedule.tick,'rank',rank,'computeItalianProduction')
            for farmer in self.context.agents(agent_type=0):
                #if params.recordItalianFarmersData:
                #    self.agent_logger.log_row(round(tick),farmer.uid,farmer.farm_code,farmer.province,farmer.altimetry,int(farmer.hat_y*100),farmer.wheat_acreage,int(farmer.harvested_y*100),farmer.harvested_production,round(farmer.hours_of_tractor_use_ha,2),round(farmer.Nitrogen_per_ha),round(farmer.Herbicide_per_ha,2),round(farmer.Insecticide_per_ha,2),round(farmer.recipe_daly,4),round(farmer.recipe_species,4),farmer.policy_adopted)
                farmer.add_to_aggregate_variables(self.aggregate_data_log)
        #if params.recordItalianFarmersData:
        #    self.agent_logger.write()
        #write to file the variable specified in utils/utils.py AggregateData object
        self.aggregate_data_set.log(round(tick))
        self.aggregate_data_set.write()
        self.italianProductionLogger.log()
        italianProduction=self.italianProductionLogger.reduce(comm)
        self.italianTractorUseLogger.log()
        italianTractorUse=self.italianTractorUseLogger.reduce(comm)
        self.italianNitrogenLogger.log()
        italianNitrogen=self.italianNitrogenLogger.reduce(comm)
        self.italianHerbicideLogger.log()
        italianHerbicide=self.italianHerbicideLogger.reduce(comm)
        self.italianInsecticideLogger.log()
        italianInsecticide=self.italianInsecticideLogger.reduce(comm)
        if rank==0:
            if params.verboseFlag: 
                print('=================================')
                print('tick',self.runner.schedule.tick,'rank',rank,'computeItalianProduction')
                print('=================================')
                print('tick',self.runner.schedule.tick,'rank',rank,'Italian production',italianProduction[0],'kg; N ',italianNitrogen[0])
            self.italianProductionDurumTons=round(italianProduction[0]/1000)
            self.italianTractorUseH=italianTractorUse
            self.italianNitrogenKg=italianNitrogen
            self.italianHerbicideKg=italianHerbicide
            self.italianInsecticideKg=italianInsecticide
        self.aggregate_data_log.production = 0
        self.aggregate_data_log.hours_of_tractor_use = 0
        self.aggregate_data_log.nitrogen = 0
        self.aggregate_data_log.herbicide = 0
        self.aggregate_data_log.insecticide = 0
        self.aggregate_data_log.eco4 = 0
        self.aggregate_data_log.sra19 = 0
        self.aggregate_data_log.sra20 = 0
        self.aggregate_data_log.sra19plus20 = 0

    def updateItalianProductionAndStock(self):
        if rank==0:
            if self.runner.schedule.tick<self.switchOnItalianProduction:
                italianProductionDurumAndSoft=2*3253936
            else:
                italianProductionDurumAndSoft=self.italianProductionDurumTons*2
            self.italianProducer.production=italianProductionDurumAndSoft
            if round(self.runner.schedule.tick)==0:
                self.italianProducer.updateStockAtInitialization()
            else:
                self.italianProducer.stock+=italianProductionDurumAndSoft
            #check the update
            #international_producers=list(self.context.agents(agent_type=3))
            #for tmpProd in international_producers:
            #    if tmpProd.area_name=='Italy':
            #        print('ITA',tmpProd.production)
            if params.verboseFlag:
                print('=================================')
                print('tick',self.runner.schedule.tick,'rank',rank,'updateItalianProductionAndStock')



    def computeLCAindicators(self):
        recipe=[m for m in bd.methods if 'ReCiPe 2016' in str(m) and '20180117' in str(m)]
        recipe_ecow_end=[m for m in recipe if 'ecowheataly' in str(m) and 'Endpoint' in str(m)]
        #load ecowheataly database
        ecowheatalydb = bd.Database("ecowheataly")
        production_activity = ecowheatalydb.get('EcoWheataly production')
        functional_unit={ecowheatalydb.get('EcoWheataly production'): 1}
        chosen_methods=recipe_ecow_end
        # Inputs per ettaro
        hours_of_tractor_use = 12.5
        #hat_x_i = [100, 1.2, 0.5]  # [fertilizer, herbicide, insecticide]
         
        # Calcolo dei principi attivi
        #kg_of_nitrogen=round(hat_x_i[0]*0.46,2)
        #Herbicide_irritating=round(hat_x_i[1]*0.6,2)
        #Insecticide_harmful=round(hat_x_i[2]*0.025,2)
        #kg_of_nitrogen=100
        #Herbicide_irritating=1.2
        #Insecticide_harmful=0.5
        #MJ=100/0.2779*hours_of_tractor_use
        if rank==0:
            MJ=100/0.2779*self.italianTractorUseH[0]
            kg_of_nitrogen=0.46*self.italianNitrogenKg[0]
            Herbicide_irritating=0.025*self.italianHerbicideKg[0]
            Insecticide_harmful=0.6*self.italianInsecticideKg[0]
            # Aggiornamento quantità degli scambi
            for ex in production_activity.exchanges():
                if 'ag. tractors' in str(ex.input):
                    ex['amount'] = MJ
                    ex.save()
                if 'N fertilizer' in str(ex.input):
                    ex['amount'] = kg_of_nitrogen
                    ex.save()
                if '2,4-D' in str(ex.input):
                    ex['amount'] = Herbicide_irritating
                    ex.save()
                if 'Deltamethrin' in str(ex.input):
                    ex['amount'] = Insecticide_harmful
                    ex.save()
             
            # Calcolo degli impatti
            all_scores = {}
            wheat_lca = bc.LCA(functional_unit, chosen_methods[0])
            wheat_lca.lci()
            wheat_lca.lcia()
  
            for category in chosen_methods:
                wheat_lca.switch_method(category)
                wheat_lca.lcia()
                all_scores[category] = {
                    'score': wheat_lca.score,
                    'unit': bd.Method(category).metadata.get('unit', 'unknown')
                }
             
            # Risultati in DataFrame
            df = pd.DataFrame.from_dict(all_scores).T
            summary_data = []
             
            for idx in df.index:
                summary_data.append([
                    idx[3] if len(idx) > 3 else '',
                    idx[4] if len(idx) > 4 else '',
                    idx[5] if len(idx) > 5 else '',
                    df.loc[idx, 'score'],
                    df.loc[idx, 'unit']
                ])
             
            lca_results = pd.DataFrame(summary_data, columns=['Method', 'Damage to', 'Geo CFs', 'Score', 'Unit'])
             
            # Aggiusta unità per le particelle
            if len(lca_results) > 1:
                lca_results.loc[1, 'Unit'] = 'DALY/' + lca_results.loc[1, 'Unit']
             
            # Sommario indicatori
            tot_DALY = 0
            tot_species = 0
             
            for idx in lca_results.index:
                unit = lca_results.loc[idx]['Unit']
                score = lca_results.loc[idx]['Score']
                if 'DALY' in unit:
                    tot_DALY += score
                else:
                    tot_species += score
            if params.verboseFlag: 
                print('------------------')
                print('Sustainability indicators')
                print('------------------')
                print('damage to humans', round(tot_DALY,2))
                print('damage to ecosystem', round(tot_species,2))
            ltowrite=str(round(self.runner.schedule.tick))+','+str(round(tot_DALY,5))+','+str(round(tot_species,5))+'\n'
            with open('output/aggregate_recipe_endpoint.csv', 'a') as file:
                file.write(ltowrite)
                file.flush()
                 
    def step(self):
        for farm in self.context.agents(agent_type=0):
            farm.decide_production_inputs()
            farm.harvest()
    def log_international_data(self):
        if(rank==0):
            international_producers=list(self.context.agents(agent_type=3))
            producers_names=[]
            for ip in international_producers:
                producers_names.append([ip.area_name, ip.equilibrium_price,ip.stock,ip.sold_quantity])
            prices_df=pd.DataFrame(producers_names,columns=['area_name','eq_price','stock','sold_quantity'])
            prices_df.sort_values(['area_name'],inplace=True)
            pasted_prices=str(prices_df.loc[prices_df.index[0],'eq_price'])
            pasted_stocks=str(prices_df.loc[prices_df.index[0],'stock'])
            pasted_sold=str(prices_df.loc[prices_df.index[0],'sold_quantity'])
            for runner in range(1,len(prices_df.index)):
                pasted_prices=pasted_prices+','+str(prices_df.loc[prices_df.index[runner],'eq_price'])
                pasted_stocks=pasted_stocks+','+str(prices_df.loc[prices_df.index[runner],'stock'])
                pasted_sold=pasted_sold+','+str(prices_df.loc[prices_df.index[runner],'sold_quantity'])
            pasted_prices=str(round(self.runner.schedule.tick))+','+pasted_prices+'\n'
            pasted_stocks=str(round(self.runner.schedule.tick))+','+pasted_stocks+'\n'
            pasted_sold=str(round(self.runner.schedule.tick))+','+pasted_sold+'\n'
            with open('output/aggregate_international_prices.csv', 'a') as file:
                file.write(pasted_prices)
                file.flush()
            with open('output/aggregate_international_producers_stocks.csv', 'a') as file:
                file.write(pasted_stocks)
                file.flush()
            with open('output/aggregate_international_producers_sold_quantity.csv', 'a') as file:
                file.write(pasted_sold)
                file.flush()

    def log_agents(self):
        tick = self.runner.schedule.tick
        for farmer in self.context.agents(agent_type=0):
            #add a line to write in the farmers log file 
            self.agent_logger.log_row(tick,farmer.uid,farmer.farm_code,farmer.province,farmer.altimetry,int(farmer.hat_y*10),farmer.wheat_acreage,int(farmer.harvested_y*10),farmer.harvested_production,round(farmer.Nitrogen_per_ha),round(farmer.Herbicide_per_ha,2),round(farmer.Insecticide_per_ha,2),round(farmer.recipe_daly,2),round(farmer.recipe_series*100000,2))
            #cumulates aggregates
            farmer.add_to_aggregate_variables(self.aggregate_data_log)
        #write to the farmers log file
        self.agent_logger.write()
        #write to the aggregate log file
        self.aggregate_data_set.log(tick)
        self.aggregate_data_set.write()
        #reset the aggregate values for next time tick
        self.aggregate_data_log.production = 0

    def start(self):
        if params.verboseFlag:
            print("hello, I am going to run the start function")
        self.runner.execute()
        #self.interacting_with_ghosts()
        if params.verboseFlag:
            print("simulation performed!")
            print()
            print('===================================')
            print()



def run():
    model = Model(MPI.COMM_WORLD)
    model.start()

if __name__ == "__main__":
    run()
