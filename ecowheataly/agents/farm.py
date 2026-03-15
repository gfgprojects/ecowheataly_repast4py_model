"""Class for Farmers"""
import constants
import params
import lca_matrices

from repast4py import core
from typing import Tuple
from repast4py import random as repastrandom
from scipy.optimize import root
from scipy.optimize import fsolve
import math
import utils.utils as ut
import numpy as np
import bw2data as bd

#characterization matrices and final demand vector for LCA (A and B matrix are defined in the Farm init)
C_daly=np.array(lca_matrices.cDalyM)
C_species=np.array(lca_matrices.cSpeciesM)
f_vec=[0,0,1]


class Farm(core.Agent):
    TYPE = 0
    def __init__(self, local_id: int, rank: int,my_params,my_place_params):
        super().__init__(id=local_id, type=Farm.TYPE, rank=rank)
        #print(my_params)
        #print(my_place_params)
        self.rank=rank
        self.farm_code=str(my_params['farm code'])
        #start reshape farm code if farm is artificial. Create a code with rank,id etc.
        strrank=str(rank)
        strid=str(self.id)
        if self.farm_code[0]=='0':
            while len(strrank)<5:
                strrank='0'+strrank
            while len(strid)<8:
                strid='0'+strid
            self.farm_code=strrank+strid+'0000'
        while len(self.farm_code)<19:
            self.farm_code=self.farm_code+'0'
        self.farm_code=self.farm_code+'1'
        #end reshape farm code

        self.province=my_params['province']
        self.altimetry=my_params['altimetry']
        self.wheat_acreage=my_params['crop_acreage']
        self.farm_acreage=my_params['farm_acreage']
        self.policy_adopted='any'
        self.policy_unconstrained_inputs=[1,1,1]
        self.policy_multiplier_N=1
        self.policy_multiplier_H=1
        self.policy_multiplier_I=1
        self.policy_multiplier_hat_y=1
        self.rnd_for_beta=repastrandom.default_rng.random()*0.02-0.01
        self.rnd_for_policy_adoption=repastrandom.default_rng.random()
        #print("hello from farm "+str(self.id)+" I am in rank "+str(rank))
        #if self.farm_code[0]=='0': print(self.farm_code+','+my_params['province']+','+my_params['altimetry']+','+str(my_params['crop_acreage'])+','+str(my_params['farm_acreage'])+','+str(my_params['gender'])+','+str(my_params['young'])+',0,'+str(self.rank)+'\n')
        #print(self.farm_code,',',my_params['province'],',',my_params['altimetry'],',',my_params['crop_acreage'],',',my_params['farm_acreage'],',',str(float(my_place_params.loc[my_place_params.index[0],'risk'])))

        if params.verboseFlag: print("hello from farm "+str(self.id)+" I am in rank "+str(rank))
        if params.verboseFlag: print("farm ",str(my_params['farm code']),my_params['province'],my_params['altimetry'],my_params['crop_acreage'],str(float(my_place_params.loc[my_place_params.index[0],'risk'])))
        #self.bar_y=round(float(my_place_params['max_yield']*10),1)
        self.bar_y=round(float(my_place_params.loc[my_place_params.index[0],'max_yield']),2)
        #print(my_params['province']+','+my_params['altimetry']+','+str(self.bar_y))
        #self.bar_y=constants.bar_y
        self.risk=my_place_params['risk']
        #filled by the decide_production_inputs function
        self.hat_y=0
        self.harvested_y=0
        self.harvested_production=0
        self.Nitrogen_per_ha=0
        self.Herbicide_per_ha=0
        self.Insecticide_per_ha=0
        self.hours_of_tractor_use_ha=0
        self.profit_per_ha=0
        self.recipe_daly=0
        self.recipe_species=0

        self.hat_y_after_policy=0
        self.Nitrogen_per_ha_after_policy=0
        self.Herbicide_per_ha_after_policy=0
        self.Insecticide_per_ha_after_policy=0
        self.hours_of_tractor_use_ha_after_policy=0
 
        self.unconstrained_hat_y=0
        self.constrained_hat_y=0
        self.unconstrained_Nitrogen_per_ha=0
        self.unconstrained_Herbicide_per_ha=0
        self.unconstrained_Insecticide_per_ha=0
        self.unconstrained_inputs=[0,0,0]
        self.constrained_Nitrogen_per_ha=0
        self.constrained_Herbicide_per_ha=0
        self.constrained_Insecticide_per_ha=0
        self.constrained_inputs=[0,0,0]

        s1=my_place_params.loc[my_place_params.index[0],'s1']
        s2=my_place_params.loc[my_place_params.index[0],'s2']
        s3=my_place_params.loc[my_place_params.index[0],'s3']
        #if s1==0: print(self.province,self.altimetry,str(s1))
        #s2=float(my_place_params['s2'])
        #s3=float(my_place_params['s3'])
        #s1=constants.s_1
        #s2=constants.s_2
        #s3=constants.s_3
        self.p_w=constants.p_w                #wheat price per ton used in international markets
        self.p_w_ql=round(constants.p_w/10,3) #wheat price per quintal used in maximization
        self.p_x_i=[constants.p_x_1,constants.p_x_2,constants.p_x_3]
        self.s_i=[s1,s2,s3]
        #self.s_i=[constants.s_1,constants.s_2,constants.s_3]
        #self.s_i=[s1,s2,s3]
        #self.bar_s_i=[constants.bar_s_1,constants.bar_s_2,constants.bar_s_3]
        self.bar_s_i=[s1,s2,s3]
        my_lambda_1=my_place_params.loc[my_place_params.index[0],'lambda1']*(1+(repastrandom.default_rng.random()-0.5)*2*0.0)
        my_lambda_2=my_place_params.loc[my_place_params.index[0],'lambda2']
        my_lambda_3=my_place_params.loc[my_place_params.index[0],'lambda3']
        #my_lambda_1=constants.lambda_1*(1+(repastrandom.default_rng.random()-0.5)*2*0.2)
        #my_lambda_2=constants.lambda_2*(1+(repastrandom.default_rng.random()-0.5)*2*0.2)
        #my_lambda_3=constants.lambda_3*(1+(repastrandom.default_rng.random()-0.5)*2*0.2)
        #my_lambda_1=constants.lambda_1
        #my_lambda_2=constants.lambda_2
        #my_lambda_3=constants.lambda_3
        self.lambda_i=[my_lambda_1,my_lambda_2,my_lambda_3]
        #matrices fro LCA to be customized (the characterization matrices and the final demand vector are defined after the includes
        self.A=np.array(lca_matrices.activitiesM)
        self.B=np.array(lca_matrices.biosphereM)

    def _foc_residual(self,y):
        total_cost=0
        for i in range(len(self.s_i)):
            tmp_cost=self.p_x_i[i]/(self.lambda_i[i]*(1+self.bar_s_i[i]-self.s_i[i])*self.bar_y-self.lambda_i[i]*y)
            total_cost+=self.policy_unconstrained_inputs[i]*tmp_cost
        residual=self.p_w_ql-total_cost
        return residual

    def updateWheatPrice(self,tmpmodel):
        """update wheat price"""
        if tmpmodel.runner.schedule.tick>0:
            tmp_policy_maker=tmpmodel.context.ghost_agent((0,1,0))
            self.p_w=round(sum(tmp_policy_maker.italianPricesHystory)/len(tmp_policy_maker.italianPricesHystory),2)
            self.p_w_ql=round(self.p_w/10,3)
            #self.p_w=constants.p_w

    def compute_unconstrained_production_inputs(self):
        self.policy_unconstrained_inputs=[1,1,1]
        #self.pt+=repastrandom.default_rng.random()-0.5
        if params.verboseFlag: print("farm "+str(self.id)+" I am in rank "+str(self.rank)+" uid "+str(self.uid)+' inputs decision:')
        tmp_sol=None
        sol_not_found=True
        while sol_not_found:
            tmp_guess_share=(repastrandom.default_rng.uniform(low=0.3,high=1.0,size=1))[0]
            tmp_sol=root(self._foc_residual,tmp_guess_share*self.bar_y)
            sol_not_found= not tmp_sol.success
        hat_y=tmp_sol.x[0]

        #hat_y=fsolve(self._foc_residual,15)[0]
        self.hat_y=round(hat_y,2)
        self.unconstrained_hat_y=self.hat_y

        #if self.uid[0]==18 and self.uid[1]==0 and self.uid[2]==1:
        #    print('----- unconstrained-----')
        #    print(self.hat_y)
        if params.verboseFlag: print('target production',int(self.hat_y*10),'kg/ha')
        hat_x_i=[]
        for i in range(len(self.s_i)):
            if self.bar_s_i[i]*self.bar_y==0: print(self.province,self.altimetry,str(self.bar_s_i[i]))
            log_arg=((1+self.bar_s_i[i]-self.s_i[i])*self.bar_y-self.hat_y)/(self.bar_s_i[i]*self.bar_y)
            #print(log_arg)
            #if log_arg <= 0:
            #    log_arg=0.1
            hat_x=-1/self.lambda_i[i]*math.log(log_arg)
            if hat_x<0:
                hat_x=0
            hat_x_i.append(hat_x)
            if params.verboseFlag: print('x',str(i),'=',str(round(hat_x,2)))
        #hat_x_i[0]=repastrandom.default_rng.integers(10,high=150,size=1)[0]
        if False:
            if self.uid[0]==0 and self.uid[1]==0 and self.uid[2]==1:
                print("farm "+str(self.id)+" I am in rank "+str(self.rank)+" uid "+str(self.uid)+' inputs decision:')
                print('ppq',str(self.p_w_ql))
                print(self.p_x_i)
                print(self.s_i)
                print(self.lambda_i)
                print('bar_y',str(self.bar_y))
                print('hat_y',str(self.hat_y))
                print(hat_x_i)
                print(self.province)
                print(self.altimetry)
        #if self.uid[0]==18 and self.uid[1]==0 and self.uid[2]==1:
        #    print('inputs')
        #    print(hat_x_i)
        self.unconstrained_Nitrogen_per_ha=hat_x_i[0]
        self.unconstrained_Herbicide_per_ha=hat_x_i[1]
        self.unconstrained_Insecticide_per_ha=hat_x_i[2]
        self.unconstrained_inputs=hat_x_i
        self.profit_per_ha=self.p_w_ql*self.hat_y-self.p_x_i[0]*self.unconstrained_Nitrogen_per_ha-self.p_x_i[1]*self.unconstrained_Herbicide_per_ha-self.p_x_i[2]*self.unconstrained_Insecticide_per_ha

    def compute_constrained_production_inputs(self):
        #self.pt+=repastrandom.default_rng.random()-0.5
        if params.verboseFlag: print("farm "+str(self.id)+" I am in rank "+str(self.rank)+" uid "+str(self.uid)+' inputs decision:')
        #tmp_sol=None
        #sol_not_found=True
        #while sol_not_found:
        #    tmp_guess_share=(repastrandom.default_rng.uniform(low=0.3,high=1.0,size=1))[0]
        #    tmp_sol=root(self._foc_residual,tmp_guess_share*self.bar_y)
        #    sol_not_found= not tmp_sol.success
        #hat_y=tmp_sol.x[0]
        hat_y_vector=[]
        for i in range(len(self.s_i)):
            if self.policy_unconstrained_inputs[i]==0:
                tmp_conditional_y=self.bar_y*(1-self.s_i[i])+self.bar_y*self.s_i[i]*(1-math.exp(-self.lambda_i[i]*self.constrained_inputs[i]))
                hat_y_vector.append(tmp_conditional_y)
        if False:
        #if self.uid[0]==260 and self.uid[1]==0 and self.uid[2]==1:
            print('------constrained------')
            print(self.policy_unconstrained_inputs)
            print(self.constrained_inputs)
            print(hat_y_vector)

        #hat_y=fsolve(self._foc_residual,15)[0]
        self.hat_y=round(min(hat_y_vector),2)
        self.constrained_hat_y=self.hat_y
        #if self.uid[0]==18 and self.uid[1]==0 and self.uid[2]==1:
        #    print(self.hat_y)

        if params.verboseFlag: print('target production',int(self.hat_y*10),'kg/ha')
        hat_x_i=[]
        for i in range(len(self.s_i)):
            if self.bar_s_i[i]*self.bar_y==0: print(self.province,self.altimetry,str(self.bar_s_i[i]))
            log_arg=((1+self.bar_s_i[i]-self.s_i[i])*self.bar_y-self.hat_y)/(self.bar_s_i[i]*self.bar_y)
            #print(log_arg)
            #if log_arg <= 0:
            #    log_arg=0.1
            hat_x=-1/self.lambda_i[i]*math.log(log_arg)
            if hat_x<0:
                hat_x=0
            hat_x_i.append(hat_x)
            if params.verboseFlag: print('x',str(i),'=',str(round(hat_x,2)))
        #hat_x_i[0]=repastrandom.default_rng.integers(10,high=150,size=1)[0]
        if False:
            if self.uid[0]==0 and self.uid[1]==0 and self.uid[2]==1:
                print("farm "+str(self.id)+" I am in rank "+str(self.rank)+" uid "+str(self.uid)+' inputs decision:')
                print('ppq',str(self.p_w_ql))
                print(self.p_x_i)
                print(self.s_i)
                print(self.lambda_i)
                print('bar_y',str(self.bar_y))
                print('hat_y',str(self.hat_y))
                print(hat_x_i)
                print(self.province)
                print(self.altimetry)
        #if self.uid[0]==18 and self.uid[1]==0 and self.uid[2]==1:
        #    print(hat_x_i)
        self.constrained_Nitrogen_per_ha=hat_x_i[0]
        self.constrained_Herbicide_per_ha=hat_x_i[1]
        self.constrained_Insecticide_per_ha=hat_x_i[2]
        self.profit_per_ha=self.p_w_ql*self.hat_y-self.p_x_i[0]*self.constrained_Nitrogen_per_ha-self.p_x_i[1]*self.constrained_Herbicide_per_ha-self.p_x_i[2]*self.constrained_Insecticide_per_ha




    def decide_production_inputs(self):
        #self.pt+=repastrandom.default_rng.random()-0.5
        if params.verboseFlag: print("farm "+str(self.id)+" I am in rank "+str(self.rank)+" uid "+str(self.uid)+' inputs decision:')
        self.policy_unconstrained_inputs=[1,1,1]
        tmp_sol=None
        sol_not_found=True
        while sol_not_found:
            tmp_guess_share=(repastrandom.default_rng.uniform(low=0.3,high=1.0,size=1))[0]
            tmp_sol=root(self._foc_residual,tmp_guess_share*self.bar_y)
            sol_not_found= not tmp_sol.success
        hat_y=tmp_sol.x[0]

        #hat_y=fsolve(self._foc_residual,15)[0]
        self.hat_y=round(hat_y,2)
        if params.verboseFlag: print('target production',int(self.hat_y),'kg/ha')
        hat_x_i=[]
        for i in range(len(self.s_i)):
            if self.bar_s_i[i]*self.bar_y==0: print(self.province,self.altimetry,str(self.bar_s_i[i]))
            log_arg=((1+self.bar_s_i[i]-self.s_i[i])*self.bar_y-self.hat_y)/(self.bar_s_i[i]*self.bar_y)
            #print(log_arg)
            #if log_arg <= 0:
            #    log_arg=0.1
            hat_x=-1/self.lambda_i[i]*math.log(log_arg)
            if hat_x<0:
                hat_x=0
            hat_x_i.append(hat_x)
            if params.verboseFlag: print('x',str(i),'=',str(round(hat_x,2)))
        #hat_x_i[0]=repastrandom.default_rng.integers(10,high=150,size=1)[0]
        if False:
            if self.uid[0]==0 and self.uid[1]==0 and self.uid[2]==1:
                print("farm "+str(self.id)+" I am in rank "+str(self.rank)+" uid "+str(self.uid)+' inputs decision:')
                print('ppq',str(self.p_w_ql))
                print(self.p_x_i)
                print(self.s_i)
                print(self.lambda_i)
                print('bar_y',str(self.bar_y))
                print('hat_y',str(self.hat_y))
                print(hat_x_i)
                print(self.province)
                print(self.altimetry)
        self.Nitrogen_per_ha=hat_x_i[0]
        self.Nitrogen_per_ha_after_policy=hat_x_i[0]*self.policy_multiplier_N
        self.Herbicide_per_ha=hat_x_i[1]
        self.Herbicide_per_ha_after_policy=hat_x_i[1]*self.policy_multiplier_H
        self.Insecticide_per_ha=hat_x_i[2]
        self.Insecticide_per_ha_after_policy=hat_x_i[2]*self.policy_multiplier_I
        self.hat_y_after_policy=self.hat_y*self.policy_multiplier_hat_y
        if False:
        #if self.uid[0]==260 and self.uid[1]==0 and self.uid[2]==1:
            print('-----production-----')
            print(self.policy_unconstrained_inputs)
            print(hat_x_i)
            print(self.Nitrogen_per_ha_after_policy,self.Herbicide_per_ha_after_policy,self.Insecticide_per_ha_after_policy)

        if self.altimetry =='Montagna':
            self.hours_of_tractor_use_ha=round(15+0.1*self.hat_y*0.1,2) #remember hat_y 100kg
            self.hours_of_tractor_use_ha_after_policy=round(15+0.1*self.hat_y_after_policy*0.1,2)
        if self.altimetry =='Collina':
            self.hours_of_tractor_use_ha=round(12.5+0.1*self.hat_y*0.1,2) #remember hat_y is in 100kg unit
            self.hours_of_tractor_use_ha_after_policy=round(12.5+0.1*self.hat_y_after_policy*0.1,2)
        if self.altimetry =='Pianura':
            self.hours_of_tractor_use_ha=round(10+0.1*self.hat_y*0.1,2) #remember hat_y is in 100kg unit
            self.hours_of_tractor_use_ha_after_policy=round(10+0.1*self.hat_y_after_policy*0.1,2)
        self.profit_per_ha=self.p_w_ql*self.hat_y-self.p_x_i[0]*self.Nitrogen_per_ha-self.p_x_i[1]*self.Herbicide_per_ha-self.p_x_i[2]*self.Insecticide_per_ha

    def keep_or_change_policy(self,tmpmodel):
        tmp_policy_maker=tmpmodel.context.ghost_agent((0,1,0))
        tmp_policies=tmp_policy_maker.policies
        self.policy_multiplier_hat_y=1
        self.policy_multiplier_N=1
        self.policy_multiplier_H=1
        self.policy_multiplier_I=1
        if tmp_policies['payment/ha'].sum()==0:
            self.policy_adopted='any'
        else:
            #uncontrained profit
            self.compute_unconstrained_production_inputs()
            unconstrained_profit_per_ha=self.profit_per_ha
            ##################
            #find probabilities of adoption
            ##################

            prob_tresholds=[]
            tmp_profit_loss=0
            for i,row in tmp_policies.iterrows():
                #tmp_beta=(repastrandom.default_rng.uniform(low=max([row['profit']-0.01,0.0]),high=row['profit'],size=1))[0]
                if row['profit']>=0:
                    tmp_beta=row['profit']+self.rnd_for_beta
                    tmp_profit_loss=round(tmp_beta*unconstrained_profit_per_ha,2)
                else:
                    self.policy_unconstrained_inputs=[1,1,1]
                    if row['n_type']=='mandatory': self.policy_unconstrained_inputs[0]=0
                    if row['h_type']=='mandatory': self.policy_unconstrained_inputs[1]=0
                    if row['i_type']=='mandatory': self.policy_unconstrained_inputs[2]=0
                    #make a vector that will be used by compute_constrained_production_inputs ..., but only the mandatory will be used
                    self.constrained_inputs=[self.unconstrained_Nitrogen_per_ha*(1-row['n_effect']),self.unconstrained_Herbicide_per_ha*(1-row['h_effect']),self.unconstrained_Insecticide_per_ha*(1-row['i_effect'])]
                    #if self.uid[0]==260 and self.uid[1]==0 and self.uid[2]==1:
                    #    print(self.policy_unconstrained_inputs)
                    #    print(self.constrained_inputs)
                    self.compute_constrained_production_inputs()
                    tmp_profit_loss=unconstrained_profit_per_ha-self.profit_per_ha
                tmp_paym=row['payment/ha']
                tmp_admin_costs=row['admin_costs']/self.farm_acreage
                treshold_for_adoption=tmp_paym-tmp_profit_loss-tmp_admin_costs
                prob_treshold_for_adoption=1/(1+math.exp(-0.3*(treshold_for_adoption)))
                prob_tresholds.append(prob_treshold_for_adoption)
                #if self.uid[0]==18 and self.uid[1]==0 and self.uid[2]==1:
                #    print(tmp_profit_loss,treshold_for_adoption,prob_treshold_for_adoption)
                #    print(tmp_paym,tmp_beta,tmp_profit_loss)
                #    print(tmp_admin_costs,treshold_for_adoption,prob_treshold_for_adoption)
            #if self.uid[0]==18 and self.uid[1]==0 and self.uid[2]==1:
            #    print(self.policy_adopted)
            #    print(self.p_w_ql)
            ##################
            #Adopt policy or not
            ##################
            #if a policy is in place (not any), keep the current policy or move to any 
            if self.policy_adopted !='any':
                current_policy_idx=tmp_policies.index.get_loc(self.policy_adopted)
                prob_current_policy=prob_tresholds[current_policy_idx]
                #if self.uid[0]==18 and self.uid[1]==0 and self.uid[2]==1:
                #    print(prob_current_policy)
                #tmp_rnd=repastrandom.default_rng.random()
                tmp_rnd=self.rnd_for_policy_adoption
                #if self.uid[0]==18 and self.uid[1]==0 and self.uid[2]==1:
                #    print(tmp_rnd)
                if tmp_rnd>prob_current_policy:
                    self.policy_adopted='any'
                    #if moved to any, move to most probable policy or keep any  
                    if len(prob_tresholds)>1:
                        prob_treshold_for_adoption=max(prob_tresholds)
                        max_prob_idx=prob_tresholds.index(prob_treshold_for_adoption)
                        best_candidate_policy=tmp_policies.index[max_prob_idx]
                        #decide if adopting or not
                        #tmp_rnd_number=repastrandom.default_rng.random()
                        tmp_rnd_number=self.rnd_for_policy_adoption
                        if tmp_rnd_number<prob_treshold_for_adoption:
                            self.policy_adopted=best_candidate_policy
            #if no policy is in place, adopt policy or continus with any
            else:
                prob_treshold_for_adoption=max(prob_tresholds)
                max_prob_idx=prob_tresholds.index(prob_treshold_for_adoption)
                best_candidate_policy=tmp_policies.index[max_prob_idx]
                #decide if adopting or not
                #tmp_rnd_number=repastrandom.default_rng.random()
                tmp_rnd_number=self.rnd_for_policy_adoption
                if tmp_rnd_number<prob_treshold_for_adoption:
                    self.policy_adopted=best_candidate_policy
            #if self.uid[0]==260 and self.uid[1]==0 and self.uid[2]==1:
            #    print(prob_tresholds)
            #    print(self.policy_adopted)
            #if self.policy_adopted=='sra19plus20':
            #    print(self.uid)
            #if self.uid[0]==18 and self.uid[1]==0 and self.uid[2]==1:
            #    print(self.policy_adopted)
            ##################
            #Prepare for computing final inputs
            ##################
            if self.policy_adopted !='any':
                chosen_policy=tmp_policies.loc[self.policy_adopted]
                if chosen_policy['profit']>=0:
                    #In this case, production inputs and output are computed using multipliers. This block Update multipliers
                    production_effect=chosen_policy['product']
                    #self.policy_multiplier_hat_y-=(repastrandom.default_rng.uniform(low=0.0,high=production_effect,size=1))[0]
                    self.policy_multiplier_hat_y-=production_effect
                    #n_info=chosen_policy['nitrogen'].split('|')
                    #n_type=n_info[0]
                    #n_effect=float(n_info[1])
                    #h_info=chosen_policy['herbicide'].split('|')
                    #h_type=h_info[0]
                    #h_effect=float(h_info[1])
                    #i_info=chosen_policy['insecticide'].split('|')
                    #i_type=i_info[0]
                    #i_effect=float(i_info[1])
                    n_type=chosen_policy['n_type']
                    n_effect=chosen_policy['n_effect']
                    h_type=chosen_policy['h_type']
                    h_effect=chosen_policy['h_effect']
                    i_type=chosen_policy['i_type']
                    i_effect=chosen_policy['i_effect']
                    if n_type=='optional':
                        self.policy_multiplier_N-=(repastrandom.default_rng.uniform(low=0.0,high=n_effect,size=1))[0]
                    else:
                        self.policy_multiplier_N-=n_effect
                    if h_type=='optional':
                        self.policy_multiplier_H-=(repastrandom.default_rng.uniform(low=0.0,high=h_effect,size=1))[0]
                    else:
                        self.policy_multiplier_H-=h_effect
                    if i_type=='optional':
                        self.policy_multiplier_I-=(repastrandom.default_rng.uniform(low=0.0,high=i_effect,size=1))[0]
                    else:
                        self.policy_multiplier_I-=i_effect
                else:
                    if chosen_policy['n_type']=='mandatory': self.policy_unconstrained_inputs[0]=0
                    if chosen_policy['h_type']=='mandatory': self.policy_unconstrained_inputs[1]=0
                    if chosen_policy['i_type']=='mandatory': self.policy_unconstrained_inputs[2]=0
                    #make a vector that will be used by compute_constrained_production_inputs ..., but only the mandatory will be used
                    self.constrained_inputs=[self.unconstrained_Nitrogen_per_ha*(1-chosen_policy['n_effect']),self.unconstrained_Herbicide_per_ha*(1-chosen_policy['h_effect']),self.unconstrained_Insecticide_per_ha*(1-chosen_policy['i_effect'])]
                    self.compute_constrained_production_inputs()
                    self.policy_multiplier_hat_y+=self.constrained_hat_y/self.unconstrained_hat_y-1
                    if self.unconstrained_Nitrogen_per_ha>0:
                        self.policy_multiplier_N+=self.constrained_Nitrogen_per_ha/self.unconstrained_Nitrogen_per_ha-1
                    if self.unconstrained_Herbicide_per_ha>0:
                        self.policy_multiplier_H+=self.constrained_Herbicide_per_ha/self.unconstrained_Herbicide_per_ha-1
                    if self.unconstrained_Insecticide_per_ha>0:
                        self.policy_multiplier_I+=self.constrained_Insecticide_per_ha/self.unconstrained_Insecticide_per_ha-1
            #if self.uid[0]==260 and self.uid[1]==0 and self.uid[2]==1:
            #if self.unconstrained_Nitrogen_per_ha==0:
            #    print(self.province,self.altimetry)
            if False:
                print('=====================')
                print(self.uid)
                print(self.policy_adopted)
                print(self.s_i)
                print(self.lambda_i)
                print(self.bar_y)
                print(treshold_for_adoption)
                print(tmp_profit_loss)
                print('----------------')
                print(self.constrained_hat_y)
                print(self.constrained_Nitrogen_per_ha)
                print(self.constrained_Herbicide_per_ha)
                print(self.constrained_Insecticide_per_ha)
                print('----------------')
                print(self.unconstrained_hat_y)
                print(self.unconstrained_Nitrogen_per_ha)
                print(self.unconstrained_Herbicide_per_ha)
                print(self.unconstrained_Insecticide_per_ha)
                print('----------------')
                print(self.policy_multiplier_hat_y)
                print(self.policy_multiplier_N)
                print(self.policy_multiplier_H)
                print(self.policy_multiplier_I)
            #if self.policy_adopted=='sra19plus20':
            #    if self.policy_multiplier_H==1:
            #        print(self.uid)
                    #print(self.policy_multiplier_N,self.policy_multiplier_H,self.policy_multiplier_I)

            #if self.uid[0]==0 and self.uid[1]==0 and self.uid[2]==1:
            #    print(prob_tresholds)
            #    print(self.policy_adopted)
            #    print(tmp_eco4)
            #    print(tmp_profit_loss)
            #    print(treshold_for_adoption)
            #    print(prob_treshold_for_adoption)
            #    print(self.policy_adopted)

    def perform_life_cyle_impact_assessment(self):

        #customize A and B matrices
        #hours_of_tractor_use = 12.5
        MJ=100/0.2779*self.hours_of_tractor_use_ha_after_policy
        #assigning tractor power
        self.A[0,2]=-MJ
        #assigning Nitrogen fertilizer. 0.46 is average Nitrogen concentration in commercial product
        self.A[1,2]=-self.Nitrogen_per_ha_after_policy*0.46
        #assigning insecticide with active principle deltamethrin. 0.025 is deltamethrin concentration in commercial product
        self.B[2,2]=self.Herbicide_per_ha_after_policy*0.025
        #assigning herbicide with active principle 2,4-D. 0.6 is 2,4-D concentration in commercial product
        self.B[46,2]=self.Insecticide_per_ha_after_policy*0.6
        #LCA computation
        s_vec=np.linalg.solve(self.A,f_vec)
        i_vec=np.matmul(self.B,s_vec)
        daly_sum=sum(np.matmul(C_daly,i_vec))
        species_sum=sum(np.matmul(C_species,i_vec))
        self.recipe_daly=daly_sum*365*24
        self.recipe_species=species_sum*100000

        #if self.uid[0]==0:
        #    print('daly: '+str(daly_sum*365*24))
        #    print('Species: '+str(species_sum))

    def harvest(self):
        #s_1=self.s_i[0]
        #lambda_1=self.lambda_i[0]
        #x_1=self.Nitrogen_per_ha
        #self.hat_y=self.bar_y*((1-s_1)+s_1*(1-math.exp(-lambda_1*x_1)))
        self.harvested_y=round((repastrandom.default_rng.normal(loc=0.5*self.hat_y_after_policy,scale=self.risk,size=1))[0],2)
        #self.harvested_y=0.5*self.hat_y
        if self.harvested_y<0: self.harvested_y=0
        if self.harvested_y>self.hat_y: self.harvested_y=self.hat_y
        #self.harvested_y=round(self.hat_y*(repastrandom.default_rng.uniform(low=0.34,high=1.0,size=1))[0],1)
        #print(self.harvested_y)
        #self.harvested_y=self.hat_y
        self.harvested_production=int(round(self.harvested_y*self.wheat_acreage*100))
        if params.verboseFlag: print('harvested yield',self.harvested_y,'ql/ha acreage: ',self.wheat_acreage,' production ',self.harvested_production)
        #if self.uid[0]==0 and self.uid[1]==0 and self.uid[2]==1:
        #    print('harvested yield',int(self.harvested_y),'ql/ha acreage: ',self.wheat_acreage,' production ',self.harvested_production)


    def add_to_aggregate_variables(self,aggregate_log: ut.AggregateData):
        aggregate_log.production+=self.harvested_production
        aggregate_log.hours_of_tractor_use+=self.hours_of_tractor_use_ha_after_policy*self.wheat_acreage
        aggregate_log.nitrogen+=self.Nitrogen_per_ha_after_policy*self.wheat_acreage
        aggregate_log.herbicide+=self.Herbicide_per_ha_after_policy*self.wheat_acreage
        aggregate_log.insecticide+=self.Insecticide_per_ha_after_policy*self.wheat_acreage
        if self.policy_adopted=='eco4':
            aggregate_log.eco4+=self.wheat_acreage
        if self.policy_adopted=='sra19':
            aggregate_log.sra19+=self.wheat_acreage
        if self.policy_adopted=='sra20':
            aggregate_log.sra20+=self.wheat_acreage
        if self.policy_adopted=='sra19plus20':
            aggregate_log.sra19plus20+=self.wheat_acreage

    def save(self) -> Tuple:
        return self.uid


