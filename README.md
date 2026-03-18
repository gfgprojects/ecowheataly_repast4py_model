# ECOWHEATALY Repast4Py Model

Agent-based model of the wheat production system implemented in **Repast4Py**.

The model simulates interactions between farms, policy makers, and international market actors in order to analyse the effects of agricultural policies, environmental constraints, and market dynamics on wheat production and sustainability outcomes.

The model is part of the **ECOWHEATALY** research project.

Visit the [Documentation](https://gfgprojects.github.io/ecowheataly_repast4py_model/) page for additional details.

---

## Overview

ECOWHEATALY is an **agent-based simulation model (ABM)** designed to study:

- the behaviour of heterogeneous wheat farms
- policy interventions in agricultural systems
- international wheat market dynamics
- environmental impacts of agricultural production

The model integrates:

- farm decision-making
- policy incentives and constraints
- international buyers and producers
- sustainability indicators based on **Life Cycle Assessment (LCA)**.

The model is implemented using **Repast4Py**, allowing scalable simulations with **MPI parallel computing**.

---

## Model Architecture

The simulation includes several interacting agents:

| Agent | Description |
|------|-------------|
| Farm | Represents agricultural producers deciding production and input use |
| Policy Maker | Implements agricultural policy instruments |
| International Buyers | Demand wheat on the global market |
| International Producers | Compete with domestic production |

The main simulation engine coordinates:

- market sessions
- farm production decisions
- policy interactions
- environmental indicator computation.

---

## Repository Structure

```
ecowheataly_repast4py_model
│
├── ecowheataly_repast_model.py # Main simulation model
├── params.py # Model parameters
│
├── agents/
│ ├── farm.py
│ ├── policy_maker.py
│ ├── international_buyer.py
│ └── international_producer.py
│
└── utils/
  └── utils.py
```

---

## Requirements

The model requires Python and several scientific and simulation libraries.

Main dependencies include:

- `repast4py`
- `mpi4py`
- `numpy`
- `pandas`
- `brightway2` (for environmental impact calculations)

A working MPI implementation must be installed in computational setting.
This is required by repast4py.

Follow the instructions [here](https://repast.github.io/repast4py.site/index.html) if you have not an MPI environment.

Then proceed to the installation through the following commands:

```bash
git clone https://github.com/gfgprojects/ecowheataly_repast4py_model.git
cd ecowheataly_repast4py_model
python3 -m venv repast4py_venv        #optional: create an environment
source repast4py_venv/bin/activate    #optional: activate the environment
env CC=mpicxx CXX=mpicxx 
pip install -r requirements.txt
cd brightway
python setup01_brightway2_database_and_methods.py
python setup02_recipe_2016_ecowheataly_customization.py
python setup03_create_custom_databases_for_tractors_N_and_ecowheataly.py
```
Install additional dependencies if needed:

```bash
pip install -r requirements1.txt
```
all dependencies are listed in requirements_all.txt


