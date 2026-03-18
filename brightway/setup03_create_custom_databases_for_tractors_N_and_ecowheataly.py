import bw2data as bd
import bw2io as bi
#bi.bw2setup()

#importing a process exported from openLCA software
print('===========================================================')
print('===========================================================')
print('IMPORTING THE MACHINERY PROCESS')
print('===========================================================')
print('===========================================================')


ei_path="usda_tractors"
ei_name="usda_item"
ei_importer = bi.SingleOutputEcospold1Importer(ei_path, ei_name,use_mp=False)

#ei_importer.apply_strategies()

bs3=bd.Database('biosphere3')
bio_names=[]
bio_categories=[]
bio_combo=[]
bio_combo1=[]
for bitem in bs3:
    bio_names.append(bitem['name'])
    bio_categories.append(str(bitem['categories']))
    bio_combo1.append((bitem['code'],bitem['name']+"~"+str(bitem['categories'])))
    bio_combo.append(bitem['name']+"~"+str(bitem['categories']))

#use fuzzy

from thefuzz import fuzz
from thefuzz import process
this_proc_names=[]
this_proc_categories=[]
strings_to_match=[]
chosen_by_fuzzy=[]
not_matched=[]
new_exchanges=[]
this_process=list(ei_importer)[0]
for i in range(len(this_process['exchanges'])):
#for i in range(9):
    this_proc_item=this_process['exchanges'][i]
    if this_proc_item['type']=='biosphere':
        this_proc_names.append(this_proc_item['name'])
        this_proc_categories.append(this_proc_item['categories'])
        str_to_match=this_proc_item['name']+"~"+str(this_proc_item['categories'])
        #str_to_match=this_proc_item['name']
        strings_to_match.append(str_to_match)
#        extracted=process.extractOne(str_to_match,bio_combo,scorer=fuzz.token_set_ratio)
        extracted=process.extractOne(str_to_match,bio_combo,scorer=fuzz.token_sort_ratio)
        #extracted=process.extractOne(str_to_match,bio_names,scorer=fuzz.token_set_ratio)
        chosen_by_fuzzy.append(extracted)
#        print(str_to_match)
#        print(extracted)
#        print()
        if extracted[1]>80:
            splitted_extracted=extracted[0].split('~')
            extracted_name=splitted_extracted[0]
            extracted_categories=splitted_extracted[1]
            extracted_codes=[bs['code'] for bs in bs3 if (bs['name']==extracted_name) and (str(bs['categories'])==str(extracted_categories))]
            extracted_code=extracted_codes[0]
            matches_in_bs3=[bs for bs in bs3 if (bs['name']==extracted_name) and (str(bs['categories'])==str(extracted_categories))]
            match_in_bs3=matches_in_bs3[0]
            new_exchange={'input': ('biosphere3',match_in_bs3['code']),'unit':match_in_bs3['unit'],'type':'biosphere','amount':this_proc_item['amount']}
            new_exchanges.append(new_exchange)
            this_proc_item['code']=extracted_code
            this_proc_item['name']=extracted_name
            this_proc_item['categories']=extracted_categories
            this_proc_item['input']=('biosphere3',extracted_code)
            if this_proc_item['name'] != extracted_name:
                print("warning: "+this_proc_item['name']+" replaced by "+extracted_name)
        else:
            not_matched.append(str_to_match+" with "+str(extracted))



self_exchange={'input': (ei_name,this_process['name']),'unit':this_process['unit'],'type':'production','amount':1}
new_exchanges.append(self_exchange)

new_process={(ei_name,this_process['name']):{'name':this_process['name'],'unit':this_process['unit'],'exchanges':new_exchanges}}

new_db=bd.Database(ei_name)
new_db.register()
new_db.write(new_process)


print('===========================================================')
print('===========================================================')
print('IMPORTING THE NITROGEN PROCESS')
print('===========================================================')
print('===========================================================')

import pandas as pd
print('   inporting the csv file')
df = pd.read_csv('csv_fertilization_process/fert1.csv',delimiter=';') 

#setup variables to apply thefuzz package

bs3=bd.Database('biosphere3')
bio_names=[]
bio_categories=[]
bio_combo=[]
bio_combo1=[]
for bitem in bs3:
    bio_names.append(bitem['name'])
    bio_categories.append(str(bitem['categories']))
    bio_combo1.append((bitem['code'],bitem['name']+"~"+str(bitem['categories'])))
    bio_combo.append(bitem['name']+"~"+str(bitem['categories']))

print('   pairing csv descriptions with biosphere3 using string matching')


#use fuzzy

from thefuzz import fuzz
from thefuzz import process
this_proc_names=[]
this_proc_categories=[]
strings_to_match=[]
chosen_by_fuzzy=[]
not_matched=[]
new_exchanges=[]

for i in range(df.shape[0]):
    this_proc_names.append(str(df.loc[i]['name']))
    this_proc_categories.append(str(df.loc[i]['to_element']))
    str_to_match=str(df.loc[i]['name'])+"~"+str(df.loc[i]['to_element'])
    strings_to_match.append(str_to_match)
    extracted=process.extractOne(str_to_match,bio_combo,scorer=fuzz.token_sort_ratio)
    chosen_by_fuzzy.append(extracted)
    if extracted[1]>80:
        splitted_extracted=extracted[0].split('~')
        extracted_name=splitted_extracted[0]
        extracted_categories=splitted_extracted[1]
        matches_in_bs3=[bs for bs in bs3 if (bs['name']==extracted_name) and (str(bs['categories'])==str(extracted_categories))]
        match_in_bs3=matches_in_bs3[0]
        quantity=df.loc[i]['N3_144_ha']
        if 'Gas' in df.loc[i]['name']:
            quantity=round(df.loc[i]['N3_144_ha']/0.76,2)
        #new_exchange={'input': ('biosphere3',match_in_bs3['code']),'unit':match_in_bs3['unit'],'type':match_in_bs3['type'],'amount':quantity}
        new_exchange={'input': ('biosphere3',match_in_bs3['code']),'unit':match_in_bs3['unit'],'type':'biosphere','amount':quantity}
        new_exchanges.append(new_exchange)
        #this_proc_item['code']=extracted_code
        #this_proc_item['name']=extracted_name
        #this_proc_item['categories']=extracted_categories
        #this_proc_item['input']=('biosphere3',extracted_code)
        if df.loc[i]['name'] != extracted_name:
            print("     warning: "+df.loc[i]['name']+" REPLACED BY "+extracted_name)
    else:
        not_matched.append(str_to_match+" WITH "+str(extracted))

print()
print("   the following poor matches were dropped:")
print()
for nm in not_matched:
    print("     "+nm)

this_process_name='application to N fertilizer use in winter wheat production systems'

db_name="bentrup_item"
if db_name in bd.databases:
    del bd.databases[db_name]

self_exchange={'input': (db_name,this_process_name),'unit':'kilogram','type':'production','amount':144}
new_exchanges.append(self_exchange)

new_process={(db_name,this_process_name):{'name':this_process_name,'unit':'kilogram','exchanges':new_exchanges}}

print()
print("   writing database")
print()

new_db=bd.Database(db_name)
new_db.register()
new_db.write(new_process)


print('===========================================================')
print('===========================================================')
print('CREATING ECOWHEATALY DATABASE')
print('===========================================================')
print('===========================================================')


#delete existing ecowheataly database if present
if 'ecowheataly' in bd.databases:
    del bd.databases['ecowheataly']

#create ecowheataly database
ecowheatalydb = bd.Database("ecowheataly")
ecowheatalydb.register()
wheat_prod=ecowheatalydb.new_activity(code = 'EcoWheataly production', name = "EcoWheataly production", unit = "ha")
#wheat_prod.new_exchange(input=('usda_item','ccfa048cb86343798ac04f50a504c3af'),amount=900,unit="megajoule",type='technosphere').save()
wheat_prod.new_exchange(input=('usda_item','work; ag. tractors for growing win wheat, 2014 fleet, all fuels; 100-175HP'),amount=0,unit="MJ",type='technosphere').save()
wheat_prod.new_exchange(input=('bentrup_item','application to N fertilizer use in winter wheat production systems'),amount=0,unit="kilogram",type='technosphere').save()
#Fungicide harmful: 'Tebuconazole' (kilogram, None, ('soil', 'agricultural'))
wheat_prod.new_exchange(input=('biosphere3','a805071f-ce96-4d72-bdd5-4334d9aa3c23'),amount=0,unit="kilogram",type='biosphere').save()
#Herbicide caution: 'Glyphosate' (kilogram, None, ('soil', 'agricultural'))
wheat_prod.new_exchange(input=('biosphere3','3850d44e-8919-47bc-9c0a-51ccc4ec9d9f'),amount=0,unit="kilogram",type='biosphere').save()
#Herbicide irritationg: '2,4-D dimethylamine salt' (kilogram, None, ('soil', 'agricultural'))
wheat_prod.new_exchange(input=('biosphere3','41a4e1fe-34ee-54d9-b049-3a60ada1ae3e'),amount=0,unit="kilogram",type='biosphere').save()
#Herbicide harmful: 'MCPA' (kilogram, None, ('soil', 'agricultural'))
wheat_prod.new_exchange(input=('biosphere3','e5492922-eaf5-4409-aa49-7f2a35cd0336'),amount=0,unit="kilogram",type='biosphere').save()
#Growth regulator harmful: 'Trinexapac-ethyl' (kilogram, None, ('soil', 'agricultural'))
wheat_prod.new_exchange(input=('biosphere3','51c7daf4-14e1-45e9-aa67-051c4ddcd9da'),amount=0,unit="kilogram",type='biosphere').save()
#Insecticide_harmful: 'Deltamethrin' (kilogram, None, ('soil', 'agricultural'))
wheat_prod.new_exchange(input=('biosphere3','282973e4-3c2d-4a9c-a3f2-d39a5b36aa76'),amount=0,unit="kilogram",type='biosphere').save()
#Insecticide toxic: 'Pirimicarb' (kilogram, None, ('soil', 'agricultural'))
wheat_prod.new_exchange(input=('biosphere3','1c0699e2-9be2-4c30-8328-fc0ad8caac58'),amount=0,unit="kilogram",type='biosphere').save()
#Molluscicide irritating: 'Metaldehyde' (kilogram, None, ('soil', 'agricultural'))
wheat_prod.new_exchange(input=('biosphere3','597847df-518f-4bd6-ae50-1de01f2761a4'),amount=0,unit="kilogram",type='biosphere').save()
wheat_prod.save()

print('Databases created')

