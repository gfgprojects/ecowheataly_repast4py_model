#Created on October 2023 by Gianfranco Giulioni within the activities of the following research project:
#FINANCING INSTITUTION
    #EU Financing plan: Next Generation EU
    #IT Financing plan: Piano Nazionale di Ripresa e Resilienza (PNRR)
    #Thematic Priority: Missione 4: istruzione e ricerca
    #IT Managing institution: Ministero dell’Universita' e della Ricerca
    #Investment name: Progetti di Ricerca di Significativo Interesse Nazionale (PRIN)
    #Call: Bando 2022
#PROJECT DETAILS
    #Title: Evaluation of Policies for Enhancing Sustainable Wheat Production in Italy
    #Short name: ECOWHEATALY
    #Contract No: 202288L9YN
    #Investment No: Codice Unico Progetto (CUP): D53D23006260006
    #Start date: 28/09/2023
    #Duration: 24 months
    #Website: www.ecowheataly.it
#License: GPL-3 

#type
#exec(open('setup_recipe_2016_ecowheataly_customization.py').read())
#to the python prompt to execute
#or use your favorite IDE facilities

#Install the bw-recipe-2016 package:
#pip install bw-recipe-2016
#from bw_recipe_2016 import add_recipe_2016
#add_recipe_2016()
import bw2data as bd

print('Cheking ReCiPe 2016')
recipe=[m for m in bd.methods if 'ReCiPe 2016' in str(m) and '20180117' in str(m)]
if len(recipe)==0:
    from bw_recipe_2016 import add_recipe_2016
    print('ReCiPe 2016 not found: start generating them')
    add_recipe_2016()
else:
    print('ReCiPe 2016 found')

print('Cheking Ecowheataly ReCiPe 2016 methods')
ecow=[m for m in bd.methods if 'ecowheataly' in str(m)]
if len(ecow)>0:
    print('Ecowheataly ReCiPe 2016 methods found: I will delete them and generate them again')
    for mt in ecow:
        bd.Method(mt).deregister()
    print('Ecowheataly ReCiPe 2016 methods deleted')


print('Start generating Ecowheataly ReCiPe 2016 methods')

# Load biosphere database
bs3 = bd.Database("biosphere3")

#remove previousely created ecowheataly methods
#ecow=[m for m in bd.methods if 'ecowheataly' in str(m)]
##for mt in ecow:
#    bd.Method(mt).deregister()

#create groups of ReCiPe methods
recipe=[m for m in bd.methods if 'ReCiPe 2016' in str(m) and '20180117' in str(m)]
recipe_Im=[m for m in recipe if 'Individualist' in str(m) and 'Midpoint' in str(m)]
recipe_Hm=[m for m in recipe if 'Hierarchist' in str(m) and 'Midpoint' in str(m)]
recipe_Em=[m for m in recipe if 'Egalitarian' in str(m) and 'Midpoint' in str(m)]
recipe_NP=[m for m in recipe if 'Individualist' not in str(m) and 'Hierarchist' not in str(m) and 'Egalitarian' not in str(m)]
recipe_Ie=[m for m in recipe if 'Individualist' in str(m) and 'Endpoint' in str(m)]
recipe_He=[m for m in recipe if 'Hierarchist' in str(m) and 'Endpoint' in str(m)]
recipe_Ee=[m for m in recipe if 'Egalitarian' in str(m) and 'Endpoint' in str(m)]

print()
print("Regionalizing Terrestrial acidification Midpoint")
amm_conversion_coef=4.76/1.96
nit_conversion_coef=0.7/0.36
sul_conversion_coef=1.25/1


tmp_method_name=('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Terrestrial Acidification')
tmp_method=bd.Method(tmp_method_name)
tmp_method_unit=tmp_method.metadata['unit']
method_cfs=tmp_method.load()
#print(f'** {tmp_method_name} ** ')
#print(*method_cfs,sep='\n')
new_CFs=[]
for cf in method_cfs:
    element_name=bs3.get(cf[0][1])['name']
    if 'Sul' in element_name:
        #print(str(bs3.get(cf[0][1]))+" .......... CF: "+str(cf[1]))
        #print(str(bs3.get(cf[0][1]))+" .......... CF: "+str(round(cf[1]*sul_conversion_coef,2)))
        new_CFs.append([cf[0],cf[1]*sul_conversion_coef])
        #print(f' adjusting Sul in {element_name}')
    elif 'Nit' in element_name:
        #print(str(bs3.get(cf[0][1]))+" .......... CF: "+str(cf[1]))
        #print(str(bs3.get(cf[0][1]))+" .......... CF: "+str(round(cf[1]*nit_conversion_coef,2)))
        new_CFs.append([cf[0],cf[1]*nit_conversion_coef])
        #print(f' adjusting Nit in {element_name}')
    elif 'Amm' in element_name:
        #print(str(bs3.get(cf[0][1]))+" .......... CF: "+str(cf[1]))
        #print(str(bs3.get(cf[0][1]))+" .......... CF: "+str(round(cf[1]*amm_conversion_coef,2)))
        new_CFs.append([cf[0],cf[1]*amm_conversion_coef])
        #print(f' adjusting Amm in {element_name}')
new_method_name=tmp_method_name+('Ecosystems','Italy','ecowheataly')
ReCiPe_2016_terrestrial_acidification_Italy = bd.Method(new_method_name); 
ReCiPe_2016_terrestrial_acidification_Italy.validate(new_CFs);
ReCiPe_2016_terrestrial_acidification_Italy.register(**{'unit':tmp_method_unit});
ReCiPe_2016_terrestrial_acidification_Italy.write(new_CFs);


print("Regionalizing Terrestrial acidification Endpoint Egalitarian")
tmp_method_name=('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Terrestrial ecosystems', 'Terrestrial Acidification', 'Egalitarian')
tmp_method=bd.Method(tmp_method_name)
tmp_method_unit=tmp_method.metadata['unit']
method_cfs=tmp_method.load()
#print(f'** {tmp_method_name} ** ')
new_CFs=[]
for cf in method_cfs:
    element_name=bs3.get(cf[0][1])['name']
    if 'Sul' in element_name:
        new_CFs.append([cf[0],cf[1]*sul_conversion_coef])
        #print(f' adjusting Sul in {element_name}')
    elif 'Nit' in element_name:
        new_CFs.append([cf[0],cf[1]*nit_conversion_coef])
        #print(f' adjusting Nit in {element_name}')
    elif 'Amm' in element_name:
        new_CFs.append([cf[0],cf[1]*amm_conversion_coef])
        #print(f' adjusting Amm in {element_name}')
new_method_name=('ReCiPe 2016', '1.1 (20180117)', 'Endpoint','Terrestrial Acidification','Ecosystems','Italy','ecowheataly')
ReCiPe_2016_terrestrial_acidification_Italy_epE = bd.Method(new_method_name); 
ReCiPe_2016_terrestrial_acidification_Italy_epE.validate(new_CFs);
ReCiPe_2016_terrestrial_acidification_Italy_epE.register(**{'unit':tmp_method_unit});
ReCiPe_2016_terrestrial_acidification_Italy_epE.write(new_CFs);

print()
print("Regionalizing Particulate Matter Formation, Midpoint Egalitarian")

#Brightway misses the CFs for PM2.5 Here we add them to the new method
#furthermore we choose the egalitarian perspective because it assess more elements. See table 5.2 pg. 49 of 191 of Recipe documentation

amm_conversion_coef=0.65/0.24
nit_conversion_coef=0.22/0.11
sul_conversion_coef=0.28/0.29
pm25_conversion_coef=2.02/1

tmp_method_name=('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Particulate Matter Formation', 'Egalitarian')
tmp_method=bd.Method(tmp_method_name)
tmp_method_unit=tmp_method.metadata['unit']
method_cfs=tmp_method.load()
#print(f'** {tmp_method_name} ** ')
pm_it_CFs=[]
for cf in method_cfs:
    element_name=bs3.get(cf[0][1])['name']
    if 'Sul' in element_name:
        pm_it_CFs.append([cf[0],round(cf[1]*sul_conversion_coef,2)])
        #print(f' adjusting Sul in {element_name}')
    elif 'Nit' in element_name:
        pm_it_CFs.append([cf[0],round(cf[1]*nit_conversion_coef,2)])
        #print(f' adjusting Nit in {element_name}')
    elif 'Amm' in element_name:
        pm_it_CFs.append([cf[0],round(cf[1]*amm_conversion_coef,2)])
        #print(f' adjusting Amml in {element_name}')

pm25_items=bs3.search('Particulate Matter, < 2.5 um')
pm_lt_25_items=[ite for ite in pm25_items if '10um' not in str(ite)]
#print(f' adjusting pm in pm_lt_25_items')
for pm in pm_lt_25_items:
    pm_it_CFs.append([(pm_lt_25_items[0]['database'],pm_lt_25_items[0]['code']),pm25_conversion_coef])

new_method_name=tmp_method_name[0:4]+('Humans','Italy','ecowheataly')
ReCiPe_2016_particles_formation_Italy = bd.Method(new_method_name); 
ReCiPe_2016_particles_formation_Italy.validate(pm_it_CFs);
ReCiPe_2016_particles_formation_Italy.register(**{'unit':tmp_method_unit})
ReCiPe_2016_particles_formation_Italy.write(pm_it_CFs);

#We compute endpoint by dividing midpoint CFS by 10000 as reported in table 5.3 pg. 49 of 191 of Recipe documentation

print("Regionalizing Particulate Matter Formation, Endpoint Egalitarian")
#tmp_method_name=('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Human health', 'Particulate Matter Formation', 'Egalitarian')
#Use the just created method
tmp_method_name=new_method_name
tmp_method=bd.Method(tmp_method_name)
tmp_method_unit=bd.Method(('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Human health', 'Particulate Matter Formation', 'Egalitarian')).metadata['unit']
method_cfs=tmp_method.load()
#print(f'** {tmp_method_name} ** ')
pm_it_CFs=[]
#print('scaling cf to 1/10000')
for cf in method_cfs:
    pm_it_CFs.append([cf[0],cf[1]/10000])
    #pm_it_CFs.append([cf[0],cf[1]/(6.29*10000)])

new_method_name=('ReCiPe 2016', '1.1 (20180117)', 'Endpoint','Particulate Matter Formation','Humans','Italy','ecowheataly')
ReCiPe_2016_particles_formation_Italy_epE = bd.Method(new_method_name); 
ReCiPe_2016_particles_formation_Italy_epE.validate(pm_it_CFs);
ReCiPe_2016_particles_formation_Italy_epE.register(**{'unit':tmp_method_unit})
ReCiPe_2016_particles_formation_Italy_epE.write(pm_it_CFs);

print()
print("Regionalizing Ozone Formation, Damage to Humans Midpoint")

nit_conversion_coef=1.13/1
nmvoc_conversion_coef=0.57/0.18

tmp_method_name=('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Ozone Formation', 'Damage to Humans')
tmp_method=bd.Method(tmp_method_name)
tmp_method_unit=tmp_method.metadata['unit']
method_cfs=tmp_method.load()
#print(f'** {tmp_method_name} ** ')
ofdh_it_CFs=[]
for cf in method_cfs:
    element_name=bs3.get(cf[0][1])['name']
    if 'Nit' in element_name:
        ofdh_it_CFs.append([cf[0],cf[1]*nit_conversion_coef])
        #print(f' adjusting Nit in {element_name}')
    else:
        ofdh_it_CFs.append([cf[0],cf[1]*nmvoc_conversion_coef])
        #print(f' adjusting nmvoc in {element_name}')

new_method_name=tmp_method_name[0:len(tmp_method_name)-1]+('Humans','Italy','ecowheataly')
ReCiPe_2016_ozone_formation_damage_to_humans_Italy = bd.Method(new_method_name); 
ReCiPe_2016_ozone_formation_damage_to_humans_Italy.validate(ofdh_it_CFs);
ReCiPe_2016_ozone_formation_damage_to_humans_Italy.register(**{'unit':tmp_method_unit});
ReCiPe_2016_ozone_formation_damage_to_humans_Italy.write(ofdh_it_CFs);

print("Regionalizing Ozone Formation, Damage to Humans Endpoint Egalitarian")
tmp_method_name=('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Human health', 'Ozone Formation', 'Damage to Humans', 'Egalitarian')
tmp_method=bd.Method(tmp_method_name)
tmp_method_unit=tmp_method.metadata['unit']
method_cfs=tmp_method.load()
#print(f'** {tmp_method_name} ** ')
ofdh_it_CFs=[]
for cf in method_cfs:
    element_name=bs3.get(cf[0][1])['name']
    if 'Nit' in element_name:
        ofdh_it_CFs.append([cf[0],cf[1]*nit_conversion_coef])
        #print(f' adjusting Nit in {element_name}')
    else:
        ofdh_it_CFs.append([cf[0],cf[1]*nmvoc_conversion_coef])
        #print(f' adjusting nmvoc in {element_name}')

new_method_name=('ReCiPe 2016', '1.1 (20180117)', 'Endpoint','Ozone Formation','Humans','Italy','ecowheataly')
ReCiPe_2016_ozone_formation_damage_to_humans_Italy_epE = bd.Method(new_method_name); 
ReCiPe_2016_ozone_formation_damage_to_humans_Italy_epE.validate(ofdh_it_CFs);
ReCiPe_2016_ozone_formation_damage_to_humans_Italy_epE.register(**{'unit':tmp_method_unit});
ReCiPe_2016_ozone_formation_damage_to_humans_Italy_epE.write(ofdh_it_CFs);


print()
print("Regionalizing Ozone Formation, Damage to Ecosystem Midpoint")

nit_conversion_coef=2.6/1
nmvoc_conversion_coef=1.41/0.29

tmp_method_name=('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Ozone Formation', 'Damage to Ecosystems')
tmp_method=bd.Method(tmp_method_name)
tmp_method_unit=tmp_method.metadata['unit']
method_cfs=tmp_method.load()
#print(f'** {tmp_method_name} ** ')
ofde_it_CFs=[]
for cf in method_cfs:
    element_name=bs3.get(cf[0][1])['name']
    if 'Nit' in element_name:
        ofde_it_CFs.append([cf[0],cf[1]*nit_conversion_coef])
        #print(f' adjusting Nit in {element_name}')
    else:
        ofde_it_CFs.append([cf[0],cf[1]*nmvoc_conversion_coef])
        #print(f' adjusting nmvoc in {element_name}')

new_method_name=tmp_method_name[0:len(tmp_method_name)-1]+('Ecosystems','Italy','ecowheataly')
ReCiPe_2016_ozone_formation_damage_to_ecosystem_Italy = bd.Method(new_method_name); 
ReCiPe_2016_ozone_formation_damage_to_ecosystem_Italy.validate(ofde_it_CFs);
ReCiPe_2016_ozone_formation_damage_to_ecosystem_Italy.register(**{'unit':tmp_method_unit});
ReCiPe_2016_ozone_formation_damage_to_ecosystem_Italy.write(ofde_it_CFs);

print("Regionalizing Ozone Formation, Damage to Ecosystem Endpoint Egalitarian")


tmp_method_name=('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Terrestrial ecosystems', 'Ozone Formation', 'Damage to Ecosystems', 'Egalitarian')
tmp_method=bd.Method(tmp_method_name)
tmp_method_unit=tmp_method.metadata['unit']
method_cfs=tmp_method.load()
#print(f'** {tmp_method_name} ** ')
ofde_it_CFs=[]
for cf in method_cfs:
    element_name=bs3.get(cf[0][1])['name']
    if 'Nit' in element_name:
        ofde_it_CFs.append([cf[0],cf[1]*nit_conversion_coef])
        #print(f' adjusting Nit in {element_name}')
    else:
        ofde_it_CFs.append([cf[0],cf[1]*nmvoc_conversion_coef])
        #print(f' adjusting nmvoc in {element_name}')

new_method_name=('ReCiPe 2016', '1.1 (20180117)', 'Endpoint','Ozone Formation','Ecosystems','Italy','ecowheataly')
ReCiPe_2016_ozone_formation_damage_to_ecosystem_Italy_epE = bd.Method(new_method_name); 
ReCiPe_2016_ozone_formation_damage_to_ecosystem_Italy_epE.validate(ofde_it_CFs);
ReCiPe_2016_ozone_formation_damage_to_ecosystem_Italy_epE.register(**{'unit':tmp_method_unit});
ReCiPe_2016_ozone_formation_damage_to_ecosystem_Italy_epE.write(ofde_it_CFs);


print()
print("Regionalizing Freshwater Eutrophication Midpoint")

phosphorus_conversion_coef=0.46
#we could compute conversion coefficients for water and for soil, however the will give the same result (0.46).
#in fact the coef for water is 0,46/1 and the one for soil is 0.046/0.1 
phosphate_conversion_coef=0.15/0.33
#the previous comment applies even in this case

tmp_method_name=('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Freshwater Eutrophication')
tmp_method=bd.Method(tmp_method_name)
tmp_method_unit=tmp_method.metadata['unit']
method_cfs=tmp_method.load()
#print(f'** {tmp_method_name} ** ')

eutr_it_CFs=[]
for cf in method_cfs:
    element_name=bs3.get(cf[0][1])['name']
    if 'Phospho' in element_name:
        eutr_it_CFs.append([cf[0],cf[1]*phosphorus_conversion_coef])
        #print(f' adjusting Phospho in {element_name}')
    else:
        eutr_it_CFs.append([cf[0],cf[1]*phosphate_conversion_coef])
        #print(f' adjusting phosphate in {element_name}')

new_method_name=tmp_method_name+('Ecosystems','Italy','ecowheataly')
ReCiPe_2016_freshwater_eutrophication_Italy = bd.Method(new_method_name); 
ReCiPe_2016_freshwater_eutrophication_Italy.validate(eutr_it_CFs);
ReCiPe_2016_freshwater_eutrophication_Italy.register(**{'unit':tmp_method_unit});
ReCiPe_2016_freshwater_eutrophication_Italy.write(eutr_it_CFs);

print("Regionalizing Freshwater Eutrophication Endpoint Egalitarian")
print()

tmp_method_name=('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Freshwater ecosystems', 'Freshwater Eutrophication', 'Egalitarian')
tmp_method=bd.Method(tmp_method_name)
tmp_method_unit=tmp_method.metadata['unit']
method_cfs=tmp_method.load()
#print(f'** {tmp_method_name} ** ')

eutr_it_CFs=[]
for cf in method_cfs:
    element_name=bs3.get(cf[0][1])['name']
    if 'Phospho' in element_name:
        eutr_it_CFs.append([cf[0],cf[1]*phosphorus_conversion_coef])
        #print(f' adjusting Phospo in {element_name}')
    else:
        eutr_it_CFs.append([cf[0],cf[1]*phosphate_conversion_coef])
        #print(f' adjusting phosphate in {element_name}')

new_method_name=('ReCiPe 2016', '1.1 (20180117)', 'Endpoint','Freshwater Eutrophication','Ecosystems','Italy','ecowheataly')
ReCiPe_2016_freshwater_eutrophication_Italy_epE = bd.Method(new_method_name); 
ReCiPe_2016_freshwater_eutrophication_Italy_epE.validate(eutr_it_CFs);
ReCiPe_2016_freshwater_eutrophication_Italy_epE.register(**{'unit':tmp_method_unit});
ReCiPe_2016_freshwater_eutrophication_Italy_epE.write(eutr_it_CFs);


#copying method with no regionalization to include the word ecowheataly in their name

#bd.Method(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Global Warming', '1000 year timescale', 'Egalitarian')).copy(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Global Warming 1000 year timescale', 'Humans and Ecosystems','Global','ecowheataly'))
print('Copying global warming 100years Midpoint')
bd.Method(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Global Warming', '100 year timescale', 'Hierarchist')).copy(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Global Warming 100 year timescale', 'Humans and Ecoystems','Global','ecowheataly'))
#bd.Method(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Global Warming', '20 year timescale', 'Individualist')).copy(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Global Warming 20 year timescale', 'Humans and Ecosystems','Global','ecowheataly'))

print('Copying Toxicity Humans carcinogenic Midpoint')
bd.Method(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Toxicity', 'Carcinogenic', 'Hierarchist')).copy(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Toxicity', 'Humans - Carcinogenic','Global','ecowheataly'))
print('Copying Toxicity Humans non-carcinogenic Midpoint')
bd.Method(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Toxicity', 'Non-carcinogenic', 'Hierarchist')).copy(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Toxicity', 'Humans - Non-carcinogenic','Global','ecowheataly'))
print('Copying Toxicity Terrestrial Midpoint')
bd.Method(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Ecotoxicity', 'Terrestrial', 'Hierarchist')).copy(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Toxicity', 'Ecosystems - Terrestrial','Global','ecowheataly'))
print('Copying Toxicity Freshwater Midpoint')
bd.Method(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Ecotoxicity', 'Freshwater', 'Hierarchist')).copy(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Toxicity', 'Ecosystems - Freshwater','Global','ecowheataly'))

#bd.Method(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Ecotoxicity', 'Marine', 'Hierarchist').copy(('ReCiPe 2016', '1.1 (20180117)', 'Midpoint', 'Ecoxicity - Marine', 'Damage to Ecosystems','Global','ecowheataly'))

print('Copying global warming 100years Endpoint')
bd.Method(('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Human health', 'Global Warming', '100 year timescale', 'Hierarchist')).copy(('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Global Warming 100 year timescale', 'Humans and Ecoystems','Global','ecowheataly'))
print('Copying Toxicity Humans carcinogenic Endpoint')
bd.Method(('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Human health', 'Toxicity', 'Carcinogenic', 'Hierarchist')).copy(('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Toxicity', 'Humans - Carcinogenic','Global','ecowheataly'))
print('Copying Toxicity Humans non-carcinogenic Endpoint')
bd.Method(('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Human health', 'Toxicity', 'Non-carcinogenic', 'Hierarchist')).copy(('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Toxicity', 'Humans - Non-carcinogenic','Global','ecowheataly'))
print('Copying Toxicity Terrestrial Endpoint')
bd.Method(('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Terrestrial ecosystems', 'Ecotoxicity', 'Terrestrial', 'Hierarchist')).copy(('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Toxicity', 'Ecosystems - Terrestrial','Global','ecowheataly'))
print('Copying Toxicity Freshwater Endpoint')
bd.Method(('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Freshwater ecosystems', 'Ecotoxicity', 'Freshwater', 'Hierarchist')).copy(('ReCiPe 2016', '1.1 (20180117)', 'Endpoint', 'Toxicity', 'Ecosystems - Freshwater','Global','ecowheataly'))


print('Ecowheataly ReCiPe 2016 methods succesful generated!')

