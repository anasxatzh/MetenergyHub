
# -*- coding: utf-8 -*-
"""
@author: Chatzieffremidis Anastasis
"""

import pandas as pd
from itertools import combinations as cm

# INITIALIZE INPUT DICT
ehr_inp = dict()

nat_ = [.073, .074, 
         .075, .076, 
         .077, .079, 
         .081, .083, 
         .084, .086, 
         .074, .074,
         .087, .089,
         .090, .091,
         .093, .094,
         .094, .076]
bio_ = [.072, .074, 
         .076, .079, 
         .081, .085, 
         .089, .093, 
         .096, .01, 
         .103, .106,
         .108, .111,
         .114, .116,
         .118, .120,
         .122, .124]

elec_ = [.159, .161,
         .163, .165,
         .166, .169,
         .171, .173,
         .175, .177,
         .179, .181,
         .183, .184,
         .186, .186,
         .187, .187,
         .187, .188]

oil_ = elec_


exportComp_ = [.053, .054, 
         .054, .055, 
         .055, .056, 
         .057, .058, 
         .058, .059, 
         .060, .060,
         .061, .061,
         .062, .062,
         .062, .062,
         .062, .062]
exportComp_ = [k*2 for k in exportComp_]

co2_ = [.024, .028, 
         .031, .035, 
         .038, .042,
         .046, .050, 
         .053, .057,
         .071, .085,
         .099, .112,
         .126, .121,
         .115, .110,
         .104, .098]

gshp =[49130, 47440, 45809,
       44233, 42712, 41243, 39824, 38454,
       37132,
       34621, 33431, 32281, 31170, 30098, 29063, 28064,
       27098, 26166, 25266, 24397
    ]
ashp =[49635, 48313, 47026,
       45773, 44554, 43367, 42212, 41087,
       39993,
       38927, 37890, 36881, 35889, 34992, 29063, 28064,
       28716, 28154, 28154, 24397
    ]
chp =[41087, 41087, 45809,
       41087, 28154, 41243, 28154, 34992,
       37132,
       34621, 47026, 28154, 31170, 30098, 34992, 28064,
       47026, 47026, 47026, 24397
    ]
pv = [49130, 47440, 45809,
       44233, 42712, 41243, 39824, 38454,
       37132,
       34621, 33431, 32281, 31170, 30098, 29063, 28064,
       27098, 26166, 25266, 24397
    ]


gshpL =[2450, 2366, 2284,
       2206, 2130, 2057, 1986, 1918,
       1852,
       1788, 1726, 1667, 1610, 1554, 1501, 1449,
       1399, 1351, 1543, 1523
    ]
ashpL =[610, 594, 578,
       563, 548, 533, 519, 505,
       491,
       478, 466, 453, 441, 428, 418, 407,
       396, 385, 376, 365
    ]
chpL =[610, 594, 578,
       563, 548, 533, 519, 505,
       491,
       478, 466, 453, 441, 428, 418, 407,
       396, 385, 376, 365
    ]
pvL = [610, 594, 578,
       563, 548, 533, 519, 505,
       491,
       478, 466, 453, 441, 428, 418, 407,
       396, 385, 376, 365
    ]

bat = [235, 231, 227, 222, 218, 214, 210, 206, 202,
       198, 195, 191, 188, 184, 181, 177, 174, 171, 167, 164]



gshpC = [
    4, 4.04, 4.08, 4.12, 4.15, 4.21, 4.25, 4.29, 4.33, 4.37, 4.41, 4.46,
    4.5, 4.54, 4.57, 4.62, 4.66, 4.7, 4.74, 4.79
    ]

ashpC = [
    4, 4.04, 4.08, 4.12, 4.15, 4.21, 4.25, 4.29, 4.33, 4.37, 4.41, 4.46,
    4.5, 4.54, 4.57, 4.62, 4.66, 4.7, 4.74, 4.79
    ]

gshpC, ashpC = [k/100 for k in gshpC],\
    [k/100 for k in ashpC]
pvC = [
    .17, .172, .173, .177, .179, .18, .182, .184, .186, .187, .189, .191,
    .182, .194, .196, .198, .199, .201, .214, .213
    ]

excelFileName = r"Time_series_inputs_retrofit.xlsx"
# Defining input values for model sets
Number_of_days : int = 14 # NEEDS TO BE CHANGED TO 365 * 20
Number_of_time_steps : int = 24
numInvestmentStages : int = 2
numYears : int = 4

omcCosts, omsCosts = \
    [.015, .015, .02, .02, .015, .015, .015, .015],[.02, .02]

# CREATE SETS :

ehr_inp["Days"] = list(range(1, Number_of_days + 1))
ehr_inp["Time_steps"] = list(range(1, 
                                   Number_of_time_steps + 1)
                                   )
ehr_inp["Investment_stages"] = list(range(1, 
                                          numInvestmentStages + 1))
# ehr_inp["Energy_system_location"] = ["LocA", "LocB", "LocC", "LocD"]
ehr_inp["Energy_system_location"] = ["LocA", "LocB"]
ehr_inp["Calendar_years"] = list(range(1, numYears + 1))
ehr_inp["Calendar_years"] = [ehr_inp["Calendar_years"][i : i + int(numYears/numInvestmentStages)] \
                                for i in range(0, 
                                               len(ehr_inp["Calendar_years"]), 
                                               int(numYears/numInvestmentStages))]


ehr_inp["Amount_of_calendar_days"] = Number_of_days
ehr_inp["Solar_tech"] = ["PV", "ST"]
ehr_inp["Dispatchable_tech"] = ["ASHP", "GSHP", "Gas_Boiler", "Oil_Boiler", "Bio_Boiler", "CHP"]
ehr_inp["Conversion_tech"] = ehr_inp["Dispatchable_tech"] + ehr_inp["Solar_tech"]
ehr_inp["Omc_cost"] = {k : v for k,v in zip(ehr_inp["Conversion_tech"],
                                            omcCosts)} # as 12%
ehr_inp["Storage_tech"] = ["Thermal_storage_tank", "Battery"]
ehr_inp["Oms_cost"] = {k : v for k,v in zip(ehr_inp["Storage_tech"],
                                            omsCosts)}
ehr_inp["Energy_carriers"] = ["Heat", "Elec", "NatGas", "Oil", "Biomass"]
ehr_inp["Energy_carriers_imp"] = ["Elec", "NatGas", "Oil", "Biomass"]
ehr_inp["Energy_carriers_exp"] = ["Elec"]
ehr_inp["Energy_carriers_exc"] = ["Oil", "Heat"]
ehr_inp["Energy_carriers_dem"] = ["Heat", "Elec"]
# ehr_inp["Retrofit_scenarios"] = ["Noretrofit", "Wall", "Fullretrofit"]
ehr_inp["Retrofit_scenarios"] = ["Noretrofit"]


# DISTANCE BETWEEN LOCATIONS:
# Dab, Dac, Dad, Dbc, Dbd, Dcd
# DISTANCES MISSING (AND REPLACED WITH 60 m) : Dac (1->3), Dbd(2->4)
Distances : list = [90, 60, 80, 150, 60, 105]
combLocs = []

combs = list(cm(ehr_inp["Energy_system_location"], 2))
for elem in combs:
    keep_ = []
    [keep_.append(i.split("c")[1]) for i in elem]
    combLocs.append("Loc_" + "".join(keep_).lower())

ehr_inp["combineLocations"] = combLocs
ehr_inp["Distance_area"] = {k : v for k,v in zip(ehr_inp["combineLocations"],
                                                    Distances)}
print("combineLocations", ehr_inp["combineLocations"])
print("Distance_area", ehr_inp["Distance_area"])


# Defining input values for model parameters
Demands = pd.read_excel(
    excelFileName,
    index_col=[0, 1],
    header=[0, 1],
    sheet_name="Loads",
)  # Read from some Excel/.csv file
ehr_inp["Energy_demand"] = Demands.stack().stack().reorder_levels([3, 2, 0, 1]).to_dict()
ehr_inp["Energy_demand"] = {(k[0], k[2], k[3]):ehr_inp["Energy_demand"][k] \
                            for k in ehr_inp["Energy_demand"].keys()}





Number_of_days = pd.read_excel(
    excelFileName,
    index_col=0,
    header=0,
    sheet_name="Number_of_days",
)  # Read from some Excel/.csv file
ehr_inp["Number_of_days"] = Number_of_days.stack().reorder_levels([1,0]).to_dict()
ehr_inp["Number_of_days"] = {k[1]:ehr_inp["Number_of_days"][k] for k in ehr_inp["Number_of_days"].keys()}


C_to_T = pd.read_excel(
    excelFileName,
    index_col=0,
    header=0,
    sheet_name="C_to_T_matching",
)  # Read from some Excel/.csv file
ehr_inp["C_to_T"] = C_to_T.stack().reorder_levels([1,0]).to_dict()
ehr_inp["C_to_T"] = {k[1]:ehr_inp["C_to_T"][k] for k in ehr_inp["C_to_T"].keys()}

P_solar = pd.read_excel(
    excelFileName,
    index_col=[0, 1],
    header=[0],
    sheet_name="Solar",
)  # Read from some Excel/.csv file
ehr_inp["P_solar"] = P_solar.stack().reorder_levels([2,0,1]).to_dict()
ehr_inp["P_solar"] = {(k[1], k[2]):ehr_inp["P_solar"][k] for k in ehr_inp["P_solar"].keys()}


ehr_inp["Discount_rate"] = 0.050

ehr_inp["Network_efficiency"] = {"Heat": 0.90, "Elec": 1.00}
ehr_inp["Network_length"] = 200
ehr_inp["Network_lifetime"] = 40
ehr_inp["Network_inv_cost_per_m"] = 800

ehr_inp["Roof_area"] = 1260
floorAreas : list = [22.3, 25300, 37650, 38000]
ehr_inp["Floor_area"] = {k:v for k,v in zip(ehr_inp["Energy_system_location"],
                                            floorAreas)}

# Generation technologies
# Linear_conv_costs, Fixed_conv_costs, Lifetime_tech
gen_tech = {
    "PV" : [300, 5750, 20],
    "ST" : [1590, 7630, 20],
    "ASHP" : [1530, 6830, 20],
    "GSHP" : [2170, 9070, 20],
    "Gas_Boiler" : [640, 11920, 20],
    "Bio_Boiler" : [1150, 24940, 20],
    "Oil_Boiler" : [540, 15890, 20],
    "CHP" : [3100, 43450, 20],
}

ehr_inp["Linear_conv_costs"] = {key: gen_tech[key][0] for key in gen_tech.keys()}
ehr_inp["Fixed_conv_costs"] = {key: gen_tech[key][1] for key in gen_tech.keys()}
ehr_inp["Lifetime_tech"] = {key: gen_tech[key][2] for key in gen_tech.keys()}
ehr_inp["Network_loses_per_m"] = {"Oil" : .234,
                                  "Heat" : .234}
ehr_inp["Export_prices"] = {"Elec": 0.120}


stL, oilBL, bioBL, gBL = pvL,pvL,pvL, pvL
helpList4 = (pvL, stL, ashpL, gshpL, gBL, bioBL, oilBL, chpL)

# totalYears = ehr_inp["Calendar_years"][0]


pvN = pv
st, oilB, bioB, gB = pvN,pvN,pvN, pvN
helpList3 = (pvN, st, ashp, gshp, gB, bioB, oilB, chp)


ehr_inp["Import_prices"] = {"Elec": 0.256, 
                            "NatGas": 0.113, 
                            "Oil": 0.106, 
                            "Biomass": 0.100}


# helpList3 = (gshp, ashp, chp, pv)

helpList = (elec_,
            nat_,
            oil_,
            bio_)


ehr_inp["Carbon_factors_import"] = {"Elec": 0.0095, "NatGas": 0.198, 
                                    "Oil": 0.265, "Biomass": 0.0}

elec2, nat2, oil2 = co2_, co2_, co2_
helpList2 = (co2_,elec2,nat2,oil2)


ehr_inp["Alpha"], ehr_inp["Beta"], \
    ehr_inp["Gamma"], ehr_inp["Delta"] \
        = .073, 32.2, 6.49, 168.4


ehr_inp["Conv_factor"] = {
    ("PV", "Elec"): 0.15,
    # ("PV", "Heat"   ): 0.15,
    # ("PV", "NatGas" ): 0.15,
    # ("PV", "Oil"    ): 0.15,
    # ("PV", "Biomass"): 0.15,

    ("ST", "Heat"): 0.35,
    # ("ST", "Elec"): 0.35,
    # ("ST", "NatGas"): 0.35,
    # ("ST", "Oil"): 0.35,
    # ("ST", "Biomass"): 0.35,

    ("ASHP", "Heat"): 3.0,
    # ("ASHP", "Elec"   ): 3.0,
    # ("ASHP", "NatGas" ): 3.0,
    # ("ASHP", "Oil"    ): 3.0,
    # ("ASHP", "Biomass"): 3.0,

    ("GSHP", "Heat"): 4.0,
    # ("GSHP", "Elec"   ): 4.0,
    # ("GSHP", "NatGas" ): 4.0,
    # ("GSHP", "Oil"    ): 4.0,
    # ("GSHP", "Biomass"): 4.0,

    ("Gas_Boiler", "Heat"): 0.9,
    # ("Gas_Boiler", "Elec"   ): 0.9,
    # ("Gas_Boiler", "NatGas" ): 0.9,
    # ("Gas_Boiler", "Oil"    ): 0.9,
    # ("Gas_Boiler", "Biomass"): 0.9,

    ("Bio_Boiler", "Heat"): 0.9,
    # ("Bio_Boiler", "Elec"   ): 0.9,
    # ("Bio_Boiler", "NatGas" ): 0.9,
    # ("Bio_Boiler", "Oil"    ): 0.9,
    # ("Bio_Boiler", "Biomass"): 0.9,

    ("Oil_Boiler", "Heat"): 0.9,
    # ("Oil_Boiler", "Elec"   ): 0.9,
    # ("Oil_Boiler", "NatGas" ): 0.9,
    # ("Oil_Boiler", "Oil"    ): 0.9,
    # ("Oil_Boiler", "Biomass"): 0.9,

    ("CHP", "Heat"): 0.6,
    # ("CHP", "Elec"   ): 0.6,
    # ("CHP", "NatGas" ): 0.6,
    # ("CHP", "Oil"    ): 0.6,
    # ("CHP", "Biomass"): 0.6,

}

# # ADDING INVESTMENT STAGES IN CONV_FACTOR
# ehr_inp["Conv_factor"] = {
#     (k,inv_) : ehr_inp["Conv_factor"][k] \
#         for k in ehr_inp["Conv_factor"].keys() \
#             for inv_ in ehr_inp["Investment_stages"]
#     }



chpC = [.55 for _ in range(len(pvC))]
bioC = [.85 for _ in range(len(pvC))]
gbC =  [.9 for _ in range(len(pvC))]

stC, obC = pvC, ashpC
help5 = (pvC, stC, ashpC, gshpC, gbC, bioC, obC, chpC)



ehr_inp["Minimum_part_load"] = {
    "ASHP": 0.0,
    "GSHP": 0.0,
    "Gas_Boiler": 0.0,
    "Bio_Boiler": 0.0,
    "Oil_Boiler": 0.0,
    "CHP": 0.0,
}

# Energy storage technologies
# ---------------------------
# Linear_stor_costs, Fixed_stor_costs, Storage_max_charge, Storage_max_discharge, Storage_standing_losses, Storage_charging_eff,
# Storage_discharging_eff, Storage_max_cap, Lifetime_stor
stor_tech = {
    "Thermal_storage_tank": [12.5, 1685, 0.25, 0.25, 0.01, 0.90, 0.90, 10**8, 20],
    "Battery": [2000, 0, 0.25, 0.25, 0.001, 0.90, 0.90, 10**8, 20],
}

ehr_inp["Linear_stor_costs"] = {key: stor_tech[key][0] for key in stor_tech.keys()}

# ehr_inp["Linear_stor_costs"] = {
#     (list(ehr_inp["Linear_stor_costs"].keys())[k], kY) : v \
#     for k in range(len(ehr_inp["Linear_stor_costs"])) for kY,v in\
#     zip(totalYears,
#         bat)
#     }

ehr_inp["Fixed_stor_costs"] = {key: stor_tech[key][1] for key in stor_tech.keys()}
ehr_inp["Storage_max_charge"] = {key: stor_tech[key][2] for key in stor_tech.keys()}
ehr_inp["Storage_max_discharge"] = {key: stor_tech[key][3] for key in stor_tech.keys()}
ehr_inp["Storage_standing_losses"] = {key: stor_tech[key][4] for key in stor_tech.keys()}
ehr_inp["Storage_charging_eff"] = {key: stor_tech[key][5] for key in stor_tech.keys()}
ehr_inp["Storage_discharging_eff"] = {key: stor_tech[key][6] for key in stor_tech.keys()}
ehr_inp["Storage_max_cap"] = {key: stor_tech[key][7] for key in stor_tech.keys()}
ehr_inp["Lifetime_stor"] = {key: stor_tech[key][8] for key in stor_tech.keys()}

ehr_inp["Storage_tech_coupling"] = {
    ("Thermal_storage_tank", "Heat"): 1.0,
    ("Thermal_storage_tank", "Elec"): 1.0,
    ("Thermal_storage_tank", "NatGas"): 1.0,
    ("Thermal_storage_tank", "Oil"): 1.0,
    ("Thermal_storage_tank", "Biomass"): 1.0,
    ("Battery", "Heat"): 1.0,
    ("Battery", "Elec"): 1.0,
    ("Battery", "NatGas"): 1.0,
    ("Battery", "Oil"): 1.0,
    ("Battery", "Biomass"): 1.0,
}

# Retrofits
ehr_inp["Retrofit_inv_costs"] = 1
ehr_inp["Lifetime_retrofit"] = 40
# ehr_inp["Retrofit_inv_costs"] = {"Noretrofit": 0, "Wall": 250000, "Fullretrofit": 450000}
# ehr_inp["Lifetime_retrofit"] = {"Noretrofit": 40, "Wall": 40, "Fullretrofit": 40}

yearDegChDis, yearlyConvDeg = [0, .02], \
    [.02, .02, .01, .01, .02, .005, .005, .005]
# yearlyConvDeg = [k*100 for k in yearlyConvDeg]
# yearDegChDis = [k*100 for k in yearDegChDis]

ehr_inp["Yearly_degradation_coefficient"] = {k:v for k,v in zip(ehr_inp["Conversion_tech"],
                                                                yearlyConvDeg)}
ehr_inp["Yearly_degradation_coefficient_chdc"] = {k:v for k,v in zip(ehr_inp["Storage_tech"],
                                                                     yearDegChDis)}



calYears = ehr_inp["Calendar_years"]
invSt = ehr_inp["Investment_stages"]
linearConvC = ehr_inp["Linear_conv_costs"]
linearStorC = ehr_inp["Linear_stor_costs"]
fixedConvC = ehr_inp["Fixed_conv_costs"]
expPrices = ehr_inp["Export_prices"]
impPrices = ehr_inp["Import_prices"]
carbImport = ehr_inp["Carbon_factors_import"]
impPrices = ehr_inp["Import_prices"]


#%% Create and solve the model
# ============================
import EnergyHubRetrofit_Paper as ehr

for inv in range(numInvestmentStages):

    # totalYears = calYears[inv]
    ehr_inp["Calendar_years"] = sum(ehr_inp["Calendar_years"], [])
    totalYears = ehr_inp["Calendar_years"]
    # print("totalYears ", totalYears)

    ehr_inp["Linear_conv_costs"] = {
        (list(linearConvC.keys())[k], kY) : v \
        for k in range(len(linearConvC)) for kY,v in\
        zip(totalYears,
            helpList4[k])
        }
    ehr_inp["Fixed_conv_costs"] = {
        (list(fixedConvC.keys())[k], kY) : v \
        for k in range(len(fixedConvC)) for kY,v in\
        zip(totalYears,
            helpList3[k])
        }
    ehr_inp["Export_prices"] = {
        (list(expPrices.keys())[k], kY) : v \
        for k in range(len(expPrices)) for kY,v in\
        zip(totalYears,
            exportComp_)
        }
    ehr_inp["Import_prices"] = {
        (list(impPrices.keys())[k], kY) : v \
        for k in range(len(impPrices)) for kY,v in\
        zip(totalYears,
            helpList[k])
        }
    ehr_inp["Carbon_factors_import"] = {
        (list(carbImport.keys())[k], kY) : v \
        for k in range(len(carbImport)) for kY,v in\
        zip(totalYears,
            helpList2[k])
        }
    ehr_inp["Linear_stor_costs"] = {
        (list(linearStorC.keys())[k], kY) : v \
        for k in range(len(linearStorC)) for kY,v in\
        zip(totalYears,
            bat)
        }
    # ehr_inp["Conv_factor"] = {
    #      (list(ehr_inp["Conv_factor"].keys())[k][0],
    #       ehr_inp["Energy_carriers"][i],
    #       kY) : v for k in range(len(ehr_inp["Conv_factor"])) \
    #      for i in range(len(ehr_inp["Energy_carriers"])) for kY,v in\
    #      zip(totalYears,
    #          help5[k])
    #      }
    # ehr_inp["Conv_factor"] = {
    #     (list(ehr_inp["Conv_factor"].keys())[k][0], kY) : v \
    #     for k in range(len(ehr_inp["Conv_factor"])) for kY,v in\
    #     zip(totalYears,
    #         help5[k])
    #     }

    # ehr_inp["Investment_stages"] = invSt[inv]
    # print("Investment_stages ", ehr_inp["Investment_stages"])
    # ehr_inp["Calendar_years"] = calYears[inv]

    print("TARGET YEARS -> {}\nINVESTMENT STAGES -> {}".format(
                                                ehr_inp["Calendar_years"],
                                                ehr_inp["Investment_stages"]))
    ehr_inp["Biomass"] = {k : 201.157 for k in ehr_inp["Calendar_years"]}
    mod = ehr.EnergyHubRetrofit(ehr_inp, 
                                invStage = inv, 
                                optim_mode=1) # Initialize the model
    mod.create_model()  # Create the model
    mod.solve() # Solve the model
    if inv == 0:break # INCLUDES ALL INVESTMENT STAGES
                      # AS A LIST (i1,i2,i3,i4)

# mod = ehr.EnergyHubRetrofit(ehr_inp, 1, 1, 1) # Initialize the model
# mod.create_model()  # Create the model
# mod.solve() # Solve the model