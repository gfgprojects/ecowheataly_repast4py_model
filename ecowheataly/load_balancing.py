#exec(open('load_balancing.py').read())
"""this script loads lb_input_real_farms.csv and split it into several files. The number of file is equal to the number of ranks"""

import sys
import pandas as pd
import numpy as np
import os

n_ranks=4
if len(sys.argv)>1:
    n_ranks=int(sys.argv[1])-1

farmsFromRica=None
farmsFromRicaExists=False
#load the files
if os.path.exists('lb_input_real_farms.csv'):
    farmsFromRicaExists=True
    farmsFromRica = pd.read_csv('lb_input_real_farms.csv')
else:
    print('lb_input_real_farms.csv not found, attempting to create artificial farms only')
province_features=None
if os.path.exists('lb_input_provinces_n_farms_census.csv'):
    province_features=pd.read_csv('lb_input_provinces_n_farms_census.csv')
else:
    print('lb_input_provinces_n_farms_census.csv not found, cannot create farms!')
    sys.exit()


#(name in census, name in rica)
province_pairing=[
        #("Aosta","Valle d'Aosta / Vallée d'Aoste"),
        #("Bolzano - Bozen","Bolzano / Bozen"),
        #("Caltinisetta","Caltanissetta"),
        #("Carbonia Iglesias","Sud Sardegna"),
        #("Forlì-Cesena","Forli'-Cesena"),
        #("Massa-Carrara","Massa Carrara"),
        #("Medio Campidano","Sud Sardegna"),
        #("Ogliastra","Nuoro"),
        #("Olbia-Tempio","Sassari"),
        #("Pesaro Urbino","Pesaro e Urbino"),
        #("Reggio Emilia","Reggio nell'Emilia"),
        ("Reggio Calabria","Reggio di Calabria")
        ]
if farmsFromRicaExists:
    for pair in province_pairing:
        idx_to_change=farmsFromRica[(farmsFromRica['province']==str(pair[1]))].index
        if len(idx_to_change)>0:
            for idx in idx_to_change:
                farmsFromRica.loc[idx,'province']=str(pair[0])

    #idx_to_change=farmsFromRica[(farmsFromRica['province']=='Reggio di Calabria')].index
    #for idx in idx_to_change:
        #farmsFromRica.loc[idx,'province']='Reggio Calabria'



    prov_alt_from_rica=[row['province']+','+row['altimetry'] for index,row in farmsFromRica.iterrows()]
    prov_alt_from_census=[row['province']+','+row['altimetry'] for index,row in province_features.iterrows()]

    #prov_alt_from_rica=[row['province']+','+row['altimetry'] for index,row in farmsFromRica.iterrows()]
    #prov_alt_from_census=[row['province']+','+row['altimetry'] for index,row in province_features.iterrows()]

    set_rica=set(prov_alt_from_rica)
    set_census=set(prov_alt_from_census)

    if not set_rica.issubset(set_census): 
        not_matched=set_rica.difference(set_census)
        #set_census.difference(set_rica)
        print('Not all provinces,altimetry in Rica are in census, Please check')
        print(not_matched)
        for nm in not_matched:
            tmpsp=nm.split(',')
            tmp_df=farmsFromRica[(farmsFromRica['province']==tmpsp[0]) & (farmsFromRica['altimetry']==tmpsp[1])]
            ###drop from RICA
            farmsFromRica.drop(index=tmp_df.index,inplace=True)
            print(nm,str(len(tmp_df)),'farms removed from RICA')
            ###add to census
            #province_features.loc[len(province_features)] = [tmpsp[0],tmpsp[1],tmp_df.shape[0]]
            #ltowrite=tmpsp[0]+','+tmpsp[1]+','+str(tmp_df.shape[0])
            #print(ltowrite,'added to provinces features')
        #exit()
    else:
        print('All provinces,altimetry in Rica are in census. Proceeding to the allocation')

###################
#Create files informing each rank on how many farms to create
###################

sorted_provinces=province_features.sort_values('province')

n_farms=sorted_provinces['n_farms']
n_farms_cumsum=sorted_provinces['n_farms'].cumsum()
total_n_of_farms=province_features['n_farms'].sum()
farms_in_each_rank=total_n_of_farms//n_ranks
n_of_spare_farms=total_n_of_farms%n_ranks

n_of_farms_in_each_rank=[]

#allocate the same number of farms in each rank
for i in range(n_ranks):
    n_of_farms_in_each_rank.append(farms_in_each_rank)
#allocate spare farms
for i in range(n_of_spare_farms):
    n_of_farms_in_each_rank[i]=n_of_farms_in_each_rank[i]+1

n_of_farms_in_each_rank_cumsum=np.cumsum(n_of_farms_in_each_rank)

#determine each province-altimetry rank
in_rank=[]

for rowi in n_farms_cumsum:
    in_rank.append(n_ranks-1)

in_rank=np.array(in_rank)
n_of_farms_in_each_rank_cumsum_flip=np.flip(np.delete(n_of_farms_in_each_rank_cumsum,n_ranks-1))
ranks_flip=np.flip(range(n_ranks-1))

for i in range(len(n_of_farms_in_each_rank_cumsum_flip)):
    tres=n_of_farms_in_each_rank_cumsum_flip[i]
    in_rank[n_farms_cumsum<=tres]=ranks_flip[i]


#split province-altimetry 
ranks_coupling=[]
#first group province-altimetry
current_rank=in_rank[0]
i=0
tmpprov=sorted_provinces.iloc[i,:]['province']
tmpalt=sorted_provinces.iloc[i,:]['altimetry']
if current_rank>0:
    for j in range(current_rank):
        nf_in_current_rank=n_of_farms_in_each_rank[j]
        ranks_coupling.append([tmpprov,tmpalt,nf_in_current_rank,j])
    nf_in_current_rank=n_farms_cumsum.iat[i]-n_of_farms_in_each_rank_cumsum[current_rank-1]
    ranks_coupling.append([tmpprov,tmpalt,nf_in_current_rank,current_rank])
else:
    tmpprov=sorted_provinces.iloc[i,:]['province']
    tmpalt=sorted_provinces.iloc[i,:]['altimetry']
    tmpnf=sorted_provinces.iloc[i,:]['n_farms']
    ranks_coupling.append([tmpprov,tmpalt,tmpnf,current_rank])

#from second group to end  province-altimetry
for i in range(1,len(in_rank)):
    tmpprov=sorted_provinces.iloc[i,:]['province']
    tmpalt=sorted_provinces.iloc[i,:]['altimetry']
    current_rank=in_rank[i]
    if in_rank[i]>in_rank[i-1]:
        if (in_rank[i]-in_rank[i-1])>1:
            farms_to_allocate=sorted_provinces.iloc[i,:]['n_farms']
            farms_allocated=0
            involved_ranks=range(in_rank[i-1],in_rank[i])
            nf_in_previous_rank=n_of_farms_in_each_rank_cumsum[involved_ranks[0]]-n_farms_cumsum.iat[i-1]
            if nf_in_previous_rank>0: 
                ranks_coupling.append([tmpprov,tmpalt,nf_in_previous_rank,involved_ranks[0]])
            farms_allocated+=nf_in_previous_rank
            for emptyr in range(involved_ranks[1],in_rank[i]):
                nf_in_previous_rank=n_of_farms_in_each_rank[emptyr]
                ranks_coupling.append([tmpprov,tmpalt,nf_in_previous_rank,emptyr])
                farms_allocated+=nf_in_previous_rank
            nf_in_present_rank=farms_to_allocate-farms_allocated
            ranks_coupling.append([tmpprov,tmpalt,nf_in_present_rank,in_rank[i]])

        else:
            nf_in_current_rank=n_farms_cumsum.iat[i]-n_of_farms_in_each_rank_cumsum[current_rank-1]
            nf_in_previous_rank=n_of_farms_in_each_rank_cumsum[current_rank-1]-n_farms_cumsum.iat[i-1]
            if nf_in_previous_rank>0:
                ranks_coupling.append([tmpprov,tmpalt,nf_in_previous_rank,current_rank-1])
            ranks_coupling.append([tmpprov,tmpalt,nf_in_current_rank,current_rank])
    else:
        tmpprov=sorted_provinces.iloc[i,:]['province']
        tmpalt=sorted_provinces.iloc[i,:]['altimetry']
        tmpnf=sorted_provinces.iloc[i,:]['n_farms']
        ranks_coupling.append([tmpprov,tmpalt,tmpnf,current_rank])

allocated_provinces=pd.DataFrame(ranks_coupling,columns=['province','altimetry','n_farms','rank'])
        
n_real_per_rank=[0] * n_ranks

if farmsFromRicaExists:
    ########################################
    #take out real farms and save their information on a file
    ########################################

    if sum(farmsFromRica['crop_acreage'].isna())>0:
        print('missing data in crop acreage assigning arbitrary value')
        farmsFromRica.loc[farmsFromRica['crop_acreage'].isna(),'crop_acreage']=3

    #The following code add a column to the farmsFromRica dataframe. The column reports the rank where each farm will be created in the abm
    grouped=farmsFromRica.groupby(['province','altimetry'])

    to_take_out=[]
    for key in grouped.groups.keys():
        to_take_out.append([key[0],key[1],len(grouped.groups[key])])

    to_take_out_df=pd.DataFrame(to_take_out,columns=['province','altimetry','n_farms'])
    removedf_vec=[]
    for index, row in to_take_out_df.iterrows():
        tmp_df=allocated_provinces[(allocated_provinces['province']==row['province']) & (allocated_provinces['altimetry']==row['altimetry'])]
        tmp_df_n_rows=tmp_df.shape[0]
        maxf=0
        if tmp_df_n_rows>1:
            cumsum_vec=tmp_df['n_farms'].cumsum()
            to_zero_pos=len(cumsum_vec[cumsum_vec<row['n_farms']])
            removedf=0
            if to_zero_pos >0:
                removedf=0
                for i in range(to_zero_pos):
                    idx=tmp_df.iloc[i].name
                    removedf+=allocated_provinces.loc[idx,'n_farms']
                    removedf_vec.append([allocated_provinces.loc[idx,'province'],allocated_provinces.loc[idx,'altimetry'],allocated_provinces.loc[idx,'n_farms'],allocated_provinces.loc[idx,'rank']])
                    allocated_provinces.loc[idx,'n_farms']=0
            idx=tmp_df.iloc[to_zero_pos].name
            allocated_provinces.loc[idx,'n_farms']+=-(row['n_farms']-removedf)
            removedf_vec.append([allocated_provinces.loc[idx,'province'],allocated_provinces.loc[idx,'altimetry'],(row['n_farms']-removedf),allocated_provinces.loc[idx,'rank']])
            maxf=cumsum_vec.iloc[tmp_df_n_rows-1]
        else:
            idx=tmp_df.iloc[0].name
            allocated_provinces.loc[idx,'n_farms']+=-row['n_farms']
            removedf_vec.append([allocated_provinces.loc[idx,'province'],allocated_provinces.loc[idx,'altimetry'],row['n_farms'],allocated_provinces.loc[idx,'rank']])
            maxf=int(tmp_df.loc[idx,'n_farms'])
        if row['n_farms']>maxf: print('farms to take out greater than desired farms')

    to_remove_with_rank=pd.DataFrame(removedf_vec,columns=['province','altimetry','n_farms','rank'])

    bursted=[]
    for index, row in to_remove_with_rank.iterrows():
        rep=row['n_farms']
        for i in range(rep):
            bursted.append([row['province'],row['altimetry'],row['rank']])
    bursted_df=pd.DataFrame(bursted,columns=['province','altimetry','rank'])

    grouped_for_rank=bursted_df.groupby(['province','altimetry'])

    for key in grouped_for_rank.groups.keys():
        tmp_rank=bursted_df.loc[grouped_for_rank.groups[key],'rank']
        tmpfFR=farmsFromRica[(farmsFromRica['province']==key[0]) & (farmsFromRica['altimetry']==key[1])]
        farmsFromRica.loc[tmpfFR.index,'rank']=tmp_rank.array

    farmsFromRica=farmsFromRica.astype({'rank':'int'})


    #Create a file for each rank with real farms to create in the rank

    rica_farms_grouped_by_ranks=farmsFromRica.groupby('rank')

    n_real_per_rank=[]
    for key in rica_farms_grouped_by_ranks.groups.keys():
        group_idx=rica_farms_grouped_by_ranks.groups[key]
        tmpfarmsFromRica=farmsFromRica.loc[group_idx]
        n_real_per_rank.append(tmpfarmsFromRica.shape[0])
        tmpfarmsFromRica.to_csv('abm_input_real_farms_'+str(key+1)+'.csv',index=False)


#Create a file for each rank with information on how many artificial farms to create in the rank
allocated_provinces=allocated_provinces[allocated_provinces['n_farms']>0]
artificial_farms_grouped_by_ranks=allocated_provinces.groupby('rank')

n_artificial_per_rank=[]
for key in artificial_farms_grouped_by_ranks.groups.keys():
    group_idx=artificial_farms_grouped_by_ranks.groups[key]
    tmp_artificial=allocated_provinces.loc[group_idx,['province','altimetry','n_farms']]
    #print(list(tmp_artificial['n_farms']))
    n_artificial_per_rank.append(tmp_artificial['n_farms'].sum())
    tmp_artificial.to_csv('abm_input_artificial_farms_'+str(key+1)+'.csv',index=False)

for i in range(len(n_artificial_per_rank)):
    print('rank',i+1,'n real farm',str(n_real_per_rank[i]),'n artificial farm',str(n_artificial_per_rank[i]),'total',str(n_real_per_rank[i]+n_artificial_per_rank[i]))
print('total number of real farms',str(sum(n_real_per_rank)))
print('total number of artificial farms',str(sum(n_artificial_per_rank)))
print('total number of farms',str(sum(n_real_per_rank)+sum(n_artificial_per_rank)))


#The following code can be used if we do not want to create artificial farms.
#It allocate the farms found in lb_input_real_farms.csv file evenly among the ranks

#if params.verboseFlag: print(farmsFromRica)
if False:
    n_farms=farmsFromRica.shape[0]
    n_ranks=4
    if len(sys.argv)>1:
        n_ranks=int(sys.argv[1])
    farms_in_each_rank=n_farms//n_ranks
    n_of_spare_farms=n_farms%n_ranks

    n_of_farms_in_each_rank=[]

    #allocate the same number of farms in each rank
    for i in range(n_ranks):
        n_of_farms_in_each_rank.append(farms_in_each_rank)
    #allocate spare farms
    for i in range(n_of_spare_farms):
        n_of_farms_in_each_rank[i]=n_of_farms_in_each_rank[i]+1

    #establish for each rank the lines to be read from the abm_input_real_farms.csv file
    n_farms_sum=0
    n_start=[]
    n_end=[]
    for i in range(n_ranks):
        n_start.append(n_farms_sum)
        n_farms_sum+=n_of_farms_in_each_rank[i]
        n_end.append(n_farms_sum-1)

    for i in range(n_ranks):
        tmp_df=farmsFromRica.loc[n_start[i]:n_end[i],:]
        tmp_df.to_csv('abm_input_real_farms_'+str(i)+'.csv',index=False)


