#exec(open('compute_inputs_and_lca.py').read())
from scipy.optimize import fsolve
import math
import fileinput
import os
import sys
import json
import bw2data as bd
import bw2calc as bc
import pandas as pd
 
########## definizione dei parametri ###############
## $output = shell_exec("python compute_inputs.py $prezzo_grano_10kg $prezzo_concime $prezzo_erbicida $prezzo_insetticida $s1 $s2 $s3 $lambda1 $lambda2 $lambda3 $max_yield"); ##
 
#### BLOCCO DI RECUPERO DEI  PARAMETRI-VARIABILI INSERITE NEL PHP
 
## PASSO IL PREZZO DEL GRANO
#p_w = float(sys.argv[1])
 
## PASSO IL PREZZO DEL CONCIME
#p_x_1 = int(sys.argv[2])
 
## PASSO IL PREZZO DEL ERBICIDA
#p_x_2 = int(sys.argv[3])
 
## PASSO IL PREZZO DEL INSETTICIDA
#p_x_3 = int(sys.argv[4])
 
##DEBUG INPUTS
#print(p_w, p_x_1, p_x_2, p_x_3)
 
#[da GUI] prezzo del grano per quintale
p_w=35
#[da GUI] prezzo del fertilizzante al kg
p_x_1=0.35
#[da GUI]prezzo del diserbante al kg o litro
p_x_2=15
#[da GUI]prezzo dellinsetticida al kg o litro
p_x_3=15
 
#utilizzando la privincia, la posizione e l'esposizione vengono calcolati i seguenti parametri.
#attualmente i parametri sono ipotizzati. Il codice che li calcola utilizzando i dati rica è ancora da implementare
 
#### tra parentesi quadra i valori del DB RICA fatto da Edmondo
 
#massimo rendimento possibile quintali per ettaro [max_yield]
bar_y=50
#bar_y = float(sys.argv[11])
#percentuale di resa che si perde se non si concima [s1]
s_1=0.5
#s_1 = float(sys.argv[5])
#percentuale di resa che si perde se non diserba [s2]
s_2=0.4
#s_2 = float(sys.argv[6])
#percentuale di resa che si perde se non da' l'insetticida [s3]
s_3=0.3
#s_3= float(sys.argv[7])
 
#massima percentuale di resa recuperabile con la fertilizzazione [s1]
#bar_s_1 = float(sys.argv[5])
bar_s_1=s_1
#massima percentuale di resa recuperabile con i trattamenti erbicidi [s2]
#bar_s_2 = float(sys.argv[6])
bar_s_2=s_2
#massima percentuale di resa recuperabile con i trattamenti insetticidi [s3]
#bar_s_3 = float(sys.argv[7])
bar_s_3=s_3
 
#parametro che regola la velocità di recupero della resa relativo ai fertilizzanti [lambda1]
#lambda_1 = float(sys.argv[8])
lambda_1=0.01
#parametro che regola la velocità di recupero della resa relativo ai diserbanti [lambda2]
#lambda_2 = float(sys.argv[9])
lambda_2=0.8
#parametro che regola la velocità di recupero della resa relativo agli insetticidi [lambda3]
#lambda_3 = float(sys.argv[10])
lambda_3=0.7
 
########## preparazione alla massimizzazione ###############
 
#vettore dei prezzi utilizzato dalla funzione foc_residual
p_x_i=[p_x_1,p_x_2,p_x_3]
#vettore delle perdite utilizzato dalla funzione foc_residual
s_i=[s_1,s_2,s_3]
#vettore dei recuperi delle rese utilizzato dalla funzione foc_residual
bar_s_i=[bar_s_1,bar_s_2,bar_s_3]
#vettore utilizzato nella funzione foc_residual
lambda_i=[lambda_1,lambda_2,lambda_3]
 
 
## AGGIUNTA GIANFRANCO- MODIFICA 20250612
 
#concentrazione del primo input
concentration_1=0.46
concentration_2=1
concentration_3=1
 
########## preparazione alla massimizzazione ###############
 
 
#vettore dei prezzi utilizzato dalla funzione foc_residual
p_x_i=[p_x_1,p_x_2,p_x_3]
#vettore delle perdite utilizzato dalla funzione foc_residual
s_i=[s_1,s_2,s_3]
#vettore dei recuperi delle rese utilizzato dalla funzione foc_residual
bar_s_i=[bar_s_1,bar_s_2,bar_s_3]
#vettore utilizzato nella funzione foc_residual
lambda_i=[lambda_1,lambda_2,lambda_3]
#vettore delle concentrazioni
concentration_i=[concentration_1,concentration_2,concentration_3]
 
#definizione della funzione che verrà utilizzata nella massimizzazione
 
def foc_residual(y):
    total_cost=0
    for i in range(len(s_i)):
        tmp_cost=p_x_i[i]/(lambda_i[i]*concentration_i[i]*(1+bar_s_i[i]-s_i[i])*bar_y-lambda_i[i]*y)
        total_cost+=tmp_cost
    residual=p_w-total_cost
    return residual
 
 
#########  massimizzazione #################################
 
#il risultato della massimizzazione fornisce la resa per ettaro che massimizza il profitto. L'agricoltore dovrà quindi applicare gli input produttivi che gli consentono di raggiungere quella resa
hat_y=fsolve(foc_residual,bar_y*0.5)[0]
print('yield',str(round(hat_y,2)))
#da valutare se utilizzare la funzione minimize al posto di fsolve
 
 
########## controlli tecnici (opzionale) ###############
#for i in range(len(s_i)):
#    yl=(1-s_i[i])*bar_y
#    yh=(1-s_i[i]+bar_s_i[i])*bar_y
#    print(str(round(yl,2)),'less eq hat_y less',str(round(yh,2)))
#    if hat_y<yl:
#        #hat_y=yl
#        print('yield',str(round(hat_y,2)))
 
 
#########  calcolo degli input #################################
#input che consentono il raggiungimento della resa ottimale
 
hat_x_i=[]
for i in range(len(s_i)):
    hat_x=-1/lambda_i[i]*concentration_i[i]*math.log(((1+bar_s_i[i]-s_i[i])*bar_y-hat_y)/(bar_s_i[i]*bar_y))
    if hat_x<0:
        hat_x=0
    hat_x_i.append(round(hat_x,2))
    print('x',str(i),'=',str(round(hat_x,2)))
 
#########  calcolo del profitto #################################
#da valutare come inserire il costo del carburante
total_cost_hat_y=0
for i in range(len(s_i)):
    total_cost_hat_y+=p_x_i[i]*hat_x_i[i]
 
profit_hat_y=p_w*hat_y-total_cost_hat_y
 
print('profit',str(round(profit_hat_y)))
 
 
recipe=[m for m in bd.methods if 'ReCiPe 2016' in str(m) and '20180117' in str(m)]
recipe_ecow_mid=[m for m in recipe if 'ecowheataly' in str(m) and 'Midpoint' in str(m)]
recipe_ecow_end=[m for m in recipe if 'ecowheataly' in str(m) and 'Endpoint' in str(m)]
 
#load ecowheataly database
ecowheatalydb = bd.Database("ecowheataly")
#print('   set functional unit as 1 hectare')
#functional unit setup
#functional_unit={ecowheatalydb.get('EcoWheataly production'): 1}
 
# Caricamento database
#ecowheatalydb = bd.Database("ecowheataly")
production_activity = ecowheatalydb.get('EcoWheataly production')
 
# Definizione della FU e dei metodi da usare
#functional_unit = {production_activity.key: 1}
functional_unit={ecowheatalydb.get('EcoWheataly production'): 1}
#chosen_methods = bd.methods[:5]  # Scegli i primi 5 metodi (oppure filtra quelli che ti interessano)
#chosen_methods = list(bd.methods)[:5]
 
 
#print('   set endpoint assessment methods')
#methods setup
chosen_methods=recipe_ecow_end
#print('end configuration')
 
 
##### aggiunta LCA_fo_GUI
 
# Inputs per ettaro
hours_of_tractor_use = 12.5
#hat_x_i = [100, 1.2, 0.5]  # [fertilizer, herbicide, insecticide]
 
# Calcolo dei principi attivi
kg_of_nitrogen=round(hat_x_i[0]*0.46,2)
Herbicide_irritating=round(hat_x_i[1]*0.6,2)
Insecticide_harmful=round(hat_x_i[2]*0.025,2)
MJ=100/0.2779*hours_of_tractor_use 
# consumo energetico per un trattore da 100 kW
 
# Caricamento database
#ecowheatalydb = bd.Database("ecowheataly")
#production_activity = ecowheatalydb.get('EcoWheataly production')
 
# Definizione della FU e dei metodi da usare
#functional_unit = {production_activity.key: 1}
#chosen_methods = bd.methods[:5]  # Scegli i primi 5 metodi (oppure filtra quelli che ti interessano)
#chosen_methods = list(bd.methods)[:5]
 
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
 
#print('------------------')
#print('Sustainability indicators')
#print('------------------')
print('damage to humans', tot_DALY * 365 * 24)  # espresso in ore di vita perse
print('damage to ecosystem', tot_species)
 
 
#PROVA OUTPUT JSON#
output = {
    "yield": round(hat_y,2),
    "profit": round(profit_hat_y),
    "inputs": {
        "fertilizer": round(hat_x_i[0],2),
        "herbicide": round(hat_x_i[1],2),
        "insecticide": round(hat_x_i[2],2),
        "damage to humans": round(tot_DALY * 365 * 24, 2),
        "damage to ecosystem": round(tot_species, 2)
    }
}
 
print(json.dumps(output))



