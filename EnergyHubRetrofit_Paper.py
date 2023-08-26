# -*- coding: utf-8 -*-
"""
Single energy hub - single stage model for the optimal design of a multi-energy system including building retrofit options
Author: Georgios Mavromatidis (ETH Zurich, gmavroma@ethz.ch)
"""

import pyomo
import pyomo.opt
import pyomo.environ as pe

# import pandas as pd
import numpy as np


# -*- coding: utf-8 -*-
"""
Single energy hub - single stage model for the optimal design of a multi-energy system including building retrofit options
Author: Georgios Mavromatidis (ETH Zurich, gmavroma@ethz.ch)
"""

import pyomo
import pyomo.opt
import pyomo.environ as pe

# import pandas as pd
import numpy as np


class EnergyHubRetrofit:
    """This class implements a standard energy hub model for the optimal design and operation of distributed multi-energy systems"""

    def __init__(self, eh_input_dict, invStage : int, temp_res=1, optim_mode=3, num_of_pareto_points=5):
        """
        __init__ function to read in the input data and begin the model creation process

        Inputs to the function:
        -----------------------
            * eh_input_dict: dictionary that holds all the values for the model parameters
            * temp_res (default = 1): 1: typical days optimization, 2: full horizon optimization (8760 hours), 3: typical days with continuous storage state-of-charge
            * optim_mode (default = 3): 1: for cost minimization, 2: for carbon minimization, 3: for multi-objective optimization
            * num_of_pareto_points (default = 5): In case optim_mode is set to 3, then this specifies the number of Pareto points
        """

        self.inp = eh_input_dict
        self.invStage = invStage
        self.temp_res = temp_res
        self.optim_mode = optim_mode
        if self.optim_mode == 1 or self.optim_mode == 2:
            self.num_of_pfp = 0
            print(
                "Warning: Number of Pareto front points specified is ignored. Single-objective optimization will be performed."
            )
        else:
            self.num_of_pfp = num_of_pareto_points

    def create_model(self):
        """Create the Pyomo energy hub model given the input data specified in the self.InputFile"""

        self.m = pe.ConcreteModel()

        # ============================================
        # Temporal dimensions and model sets (TABLE 1)
        # ============================================
        self.m.Calendar_years = pe.Set(
            initialize=self.inp["Calendar_years"],
            ordered=True,
            doc="Set for each calendar day of a full year | Index: y",
        )
        self.m.Days = pe.Set(
            initialize=self.inp["Days"],
            ordered=True,
            doc="The number of days considered in each year of the model | Index: d",
        )
        self.m.Time_steps = pe.Set(
            initialize=self.inp["Time_steps"],
            ordered=True,
            doc="Time steps considered in the model | Index: t",
        )
        self.m.Investment_stages = pe.Set(
            initialize=self.inp["Investment_stages"],
            ordered=True,
            doc="Investment stages | Index: w",
        )
        self.m.Energy_system_location = pe.Set(
            initialize=self.inp["Energy_system_location"],
            ordered=True,
            doc="Energy_system_location | Index: l",
        )

        # Energy carriers
        # ---------------
        self.m.Energy_carriers = pe.Set(
            initialize=self.inp["Energy_carriers"],
            doc="The set of all energy carriers considered in the model | Index : ec",
        )
        self.m.Energy_carriers_imp = pe.Set(
            initialize=self.inp["Energy_carriers_imp"],
            within=self.m.Energy_carriers,
            doc="The set of energy carriers for which imports are possible | Index : eci",
        )
        self.m.Energy_carriers_exp = pe.Set(
            initialize=self.inp["Energy_carriers_exp"],
            within=self.m.Energy_carriers,
            doc="The set of energy carriers for which exports are possible | Index : ece",
        )
        self.m.Energy_carriers_exc = pe.Set(
            initialize=self.inp["Energy_carriers_exc"],
            within=self.m.Energy_carriers,
            doc="The set of energy carriers that can be exchanged between energy system location | Index : ecx",
        )
        self.m.Energy_carriers_dem = pe.Set(
            initialize=self.inp["Energy_carriers_dem"],
            within=self.m.Energy_carriers,
            doc="The set of energy carriers for which end-user demands are defined | Index : ecd",
        )

        # Technologies
        # ------------
        self.m.Conversion_tech = pe.Set(
            initialize=self.inp["Conversion_tech"],
            doc="The energy conversion technologies of each energy hub candidate site | Index : conv_tech",
        )
        self.m.Solar_tech = pe.Set(
            initialize=self.inp["Solar_tech"],
            within=self.m.Conversion_tech,
            doc="Subset for solar technologies | Index : sol",
        )
        self.m.Dispatchable_tech = pe.Set(
            initialize=self.inp["Dispatchable_tech"],
            within=self.m.Conversion_tech,
            doc="Subset for dispatchable/controllable technologies | Index : disp",
        )
        self.m.Storage_tech = pe.Set(
            initialize=self.inp["Storage_tech"],
            doc="The set of energy storage technologies for each energy hub candidate site | Index : stor_tech",
        )

        # Retrofitting
        # ------------
        self.m.Retrofit_scenarios = pe.Set(
            initialize=self.inp["Retrofit_scenarios"],
            doc="Retrofit scenarios considered for the building(s) connected to the energy hub",
        )
        self.m.CombLocations = pe.Set(
            initialize=self.inp["combineLocations"],
            doc="Used to generate the possible combinations for the 4 locations."
        )

        #%% Model parameters
        # ================

        # Load parameters
        # ---------------

        self.m.Retrofit_inv_costs = pe.Param(
            self.m.Retrofit_scenarios,
            initialize=self.inp["Retrofit_inv_costs"],
            doc="Investment cost for each of the considered retrofit scenarios",
        )
        if self.temp_res == 1 or self.temp_res == 3:
            self.m.Number_of_days = pe.Param(
                # self.m.Retrofit_scenarios,
                self.m.Days,
                default=1,
                initialize=self.inp["Number_of_days"],
                doc="The number of days that each time step of typical day corresponds to",
            )
        else:
            self.m.Number_of_days = pe.Param(
                # self.m.Retrofit_scenarios,
                self.m.Days,
                default=1,
                initialize=1,
                doc="Parameter equal to 1 for each time step, because full horizon optimization is performed (temp_res == 2)",
            )
        if self.temp_res == 3:
            self.m.C_to_T = pe.Param(
                self.m.Retrofit_scenarios,
                # self.m.Calendar_days,
                initialize=self.inp["C_to_T"],
                within=self.m.Days,
                doc="Parameter to match each calendar day of a full year to a typical day for optimization",
            )

        # ===============================
        # Technical parameters (TABLE A2)
        # ===============================
            # Energy conversion technologies
        self.m.Conv_factor = pe.Param(
            self.m.Conversion_tech,
            self.m.Energy_carriers,
            self.m.Investment_stages,
            # self.m.Calendar_years,
            default=0,
            initialize=self.inp["Conv_factor"],
            doc="The conversion factors of the technologies c and energy carrier ec installed in stage w",
        )
        self.m.Lifetime_tech = pe.Param(
            self.m.Conversion_tech,
            initialize=self.inp["Lifetime_tech"],
            doc="Lifetime of energy generation technologies",
        )
        self.m.Lifetime_stor = pe.Param(
            self.m.Storage_tech,
            initialize=self.inp["Lifetime_stor"],
            doc="Lifetime of energy storage technologies",
        )
        self.m.Yearly_degradation_coefficient = pe.Param(
            self.m.Conversion_tech,
            # self.m.Energy_carriers,
            default=0,
            initialize=self.inp["Yearly_degradation_coefficient"],
            doc="Yearly degradation coefficient for the conversion factor technology c and energy carrier ec",
        )

        def Total_degradation_coefficient_rule(m, conv_tech, w, y): #A1
            if (y >= w) and (y <= w + m.Lifetime_tech[conv_tech] - 1):
                return (1 - m.Yearly_degradation_coefficient[conv_tech]
                            ) ** (y - w)
            else:
                return 1

        self.m.Total_degradation_coefficient = pe.Param(
            self.m.Conversion_tech,
            # self.m.Energy_carriers,
            self.m.Investment_stages,
            self.m.Calendar_years,
            # default=1,
            initialize=Total_degradation_coefficient_rule,
            doc="Total deg coeff for the conv factor technology c and energy carrier ec depending on w and the y",
        )

        self.m.Minimum_part_load = pe.Param(
            self.m.Dispatchable_tech,
            default=0,
            initialize=self.inp["Minimum_part_load"],
            doc="Minimum allowable part-load during the operation of dispatchable technologies",
        )

        # Energy storage technologies
        self.m.Storage_tech_coupling = pe.Param(
            self.m.Storage_tech,
            self.m.Energy_carriers,
            initialize=self.inp["Storage_tech_coupling"],
            default=0,
            doc="Storage technology coupling parameters describing the energy carrier ec stored in storage technology s",
        )
        self.m.Storage_charging_eff = pe.Param(
            self.m.Storage_tech,
            initialize=self.inp["Storage_charging_eff"],
            doc="Charging efficiency of storage technology s",
        )
        self.m.Storage_discharging_eff = pe.Param(
            self.m.Storage_tech,
            initialize=self.inp["Storage_discharging_eff"],
            doc="Discharging efficiency of storage technology s",
        )
        self.m.Storage_standing_losses = pe.Param(
            self.m.Storage_tech,
            initialize=self.inp["Storage_standing_losses"],
            doc="Standing losses for the storage technologies",
        )
        self.m.Storage_max_charge = pe.Param(
            self.m.Storage_tech,
            initialize=self.inp["Storage_max_charge"],
            doc="Maximum charging rate in % of the total capacity for the storage technologies",
        )
        self.m.Storage_max_discharge = pe.Param(
            self.m.Storage_tech,
            initialize=self.inp["Storage_max_discharge"],
            doc="Maximum discharging rate in % of the total capacity for the storage technologies",
        )
        self.m.Yearly_degradation_coefficient_chdc = pe.Param(
            self.m.Storage_tech,
            initialize=self.inp["Storage_max_discharge"],
            doc="Yearly deg coeff for the charging and discharging efficiencies of storage technology s",
        )

        def Total_degradation_coefficient_chdc_rule(m, stor_tech, w, y): #A2
            if (y >= w) and (y <= w + m.Lifetime_stor[stor_tech] - 1):
                return (1 - m.Yearly_degradation_coefficient_chdc[stor_tech]
                        ) ** (y - w)
            else:
                return 1

        self.m.Total_degradation_coefficient_chdc = pe.Param(
            self.m.Storage_tech,
            self.m.Investment_stages,
            self.m.Calendar_years,
            initialize=Total_degradation_coefficient_chdc_rule,
            doc="Total deg coeff for the charging and discharging efficiencies of s depending on the w and the y",
        )
        self.m.Lifetime_stor = pe.Param(
            self.m.Storage_tech,
            initialize=self.inp["Lifetime_stor"],
            doc="Lifetime of energy storage technologies",
        )
        self.m.Storage_max_cap = pe.Param(
            self.m.Storage_tech,
            initialize=self.inp["Storage_max_cap"],
            doc="Maximum allowable energy storage capacity per technology type",
        )
        self.m.Lifetime_retrofit = pe.Param(
            # self.m.Retrofit_scenarios,
            initialize=self.inp["Lifetime_retrofit"],
            doc="Lifetime considered for each retrofit scenario",
        )

        # Energy network
        self.m.Network_loses_per_m = pe.Param(
            self.m.Energy_carriers_exc,
            initialize=self.inp["Network_loses_per_m"],
            doc="Loses per m of network connection transferring energy carrier ecx",
        )
        self.m.Alpha = pe.Param(
            initialize=self.inp["Alpha"],
            doc="Empirical param for the calc of the pipe diameter for thermal net connections between locs [mm/kWh]",
        )
        self.m.Beta = pe.Param(
            initialize=self.inp["Beta"],
            doc="Empirical param for the calc of the pipe diameter for thermal net connections between locs [mm]",
        )
        self.m.Gamma = pe.Param(
            initialize=self.inp["Gamma"],
            doc="Empirical param for the calc of the pipe inv cost/m for thermal net connections between locs [CHF/m/mm]",
        )
        self.m.Delta = pe.Param(
            initialize=self.inp["Delta"],
            doc="Empirical param for the calc of the pipe inv cost/m for thermal net connections between locs [CHF/m]",
        )

        # ------------------------------from original, not in paper
        #self.m.Network_efficiency = pe.Param(
        #    self.m.Energy_carriers_dem,
        #    default=1,
        #    initialize=self.inp["Network_efficiency"],
        #    doc="The efficiency of the energy networks used by the energy hub",
        #)
        #self.m.Network_length = pe.Param(
        #    initialize=self.inp["Network_length"],
        #    doc="The length of the thermal network for the energy hub",
        #)
        self.m.Network_lifetime = pe.Param(
           initialize=self.inp["Network_lifetime"],
           doc="The lifetime of the thermal network used by the energy hub",
        )

        # Miscellaneous technical parameters
        self.m.enDem = pe.Param(
            self.m.Energy_carriers_dem,
            # self.m.Energy_system_location,
            # self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            default=0,
            initialize=self.inp["Energy_demand"],
            doc="Time-varying energy demand patterns for the energy hub",
        )
        self.m.Biomass = pe.Param(
            self.m.Calendar_years,
            initialize=self.inp["Biomass"],
            doc="The available bioenergy in the form of biomass per unit of building floor area in year y",
        )
        self.m.P_solar = pe.Param(
            # self.m.Retrofit_scenarios,
            self.m.Energy_system_location,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            initialize=self.inp["P_solar"],
            doc="Incoming solar radiation patterns(kWh/m2) at location l in year y day d time steps t for solar techno",
        )
        self.m.Floor_area = pe.Param(
            self.m.Energy_system_location,
            initialize=self.inp["Floor_area"],
            doc="Total building floor area across all energy system location in year y",
        )
        self.m.Roof_area = pe.Param(
            # self.m.Energy_system_location,
            # self.m.Calendar_years,
            initialize=self.inp["Roof_area"],
            doc="Total building roof area across at location l in year y for the installation of solar technologies",
        )
        self.m.Distance_area = pe.Param(
            # self.m.Energy_system_location,
            self.m.CombLocations,
            initialize=self.inp["Distance_area"],
            doc="Distance between energy system location l and l'",
        )
        self.m.Amount_Calendar_days = pe.Param(
            # self.m.Calendar_years,
            # self.m.Days,
            initialize=self.inp["Amount_of_calendar_days"],
            doc="Number of calendar days represented by each representative day d in year y",
        )

        # ==============================
        # Economic parameters (TABLE A3)
        # ==============================
        self.m.Import_prices = pe.Param(
            self.m.Energy_carriers_imp,
            self.m.Calendar_years,
            initialize=self.inp["Import_prices"],
            default=0,
            doc="Prices for importing energy carriers eci in year y from the grid",
        )
        self.m.Export_prices = pe.Param(
            self.m.Energy_carriers_exp,
            self.m.Calendar_years,
            initialize=self.inp["Export_prices"],
            default=0,
            doc="Feed-in tariffs for exporting energy carriers ece in year y back to the grid",
        )
        self.m.Fixed_conv_costs = pe.Param(
            self.m.Conversion_tech,
            self.m.Calendar_years,
            # self.m.Investment_stages,
            initialize=self.inp["Fixed_conv_costs"],
            doc="Fixed cost for installation of conv technology c in investment stage w",
        )
        self.m.Linear_conv_costs = pe.Param(
            self.m.Conversion_tech,
            self.m.Calendar_years,
            # self.m.Investment_stages,
            initialize=self.inp["Linear_conv_costs"],
            doc="Linear capacity dependent cost for the installation of conv tech c in investment stage w",
        )
        self.m.Fixed_stor_costs = pe.Param(
            self.m.Storage_tech,
            self.m.Investment_stages,
            initialize=self.inp["Fixed_stor_costs"],
            doc="Fixed cost for the installation of storage technology s in investment stag w",
        )
        self.m.Linear_stor_costs = pe.Param(
            self.m.Storage_tech,
            self.m.Calendar_years,
            # self.m.Investment_stages,
            initialize=self.inp["Linear_stor_costs"],
            doc="Linear capacity dependent cost for the installation of storage technology s in investment stage w",
        )
        self.m.Omc_cost = pe.Param(
            self.m.Conversion_tech,
            initialize=self.inp["Omc_cost"],
            doc="Par used to calculate annual maintenance cost for conv techno c as a fraction of its total inv cost",
        )
        self.m.Oms_cost = pe.Param(
            self.m.Storage_tech,
            initialize=self.inp["Oms_cost"],
            doc="Par used to calculate annual maintenance cost for storage techno s as a fraction of its total inv cost",
        )
        self.m.Discount_rate = pe.Param(
            initialize=self.inp["Discount_rate"],
            doc="The interest rate used for the CRF calculation",
        )

        def Salvage_conversion_rule(m, conv_tech, w): #A3
            maxCal = max(k for k in m.Calendar_years)
            # if w >= maxCal + 1 - m.Lifetime_tech[conv_tech]:
            return (1 - (1 + m.Discount_rate) ** \
                    (maxCal + 1 - w - m.Lifetime_tech[conv_tech]
                    ) / (1 - (1 + m.Discount_rate) ** \
                          - m.Lifetime_tech[conv_tech]
                        )
                    )
        self.m.Salvage_conversion = pe.Param(
            self.m.Conversion_tech,
            self.m.Investment_stages,
            initialize=Salvage_conversion_rule,
            doc="Salvage % of initial inv cost for conv tech c that was installed in stage w and hasn't reached the end of its lifetime",
        )

        def Salvage_storage_rule(m, stor_tech, w): #A4
            maxCal = max(k for k in m.Calendar_years)
            # if w >= maxCal + 1 - m.Lifetime_stor[stor_tech]:
            return (1 - (1 + m.Discount_rate) ** (maxCal + 1 - w - m.Lifetime_stor[stor_tech]
                                                    ) / 1 - (1 + m.Discount_rate) ** - m.Lifetime_stor[stor_tech]
                    )
        self.m.Salvage_storage = pe.Param(
            self.m.Storage_tech,
            self.m.Investment_stages,
            initialize=Salvage_storage_rule,
            doc="Salvage % of initial inv cost for stor tech s that was installed in stage w and hasn't reached the end of its lifetime",
        )



        # CRF RULE
        #-------------------------------
        def CRF_tech_rule(m, conv_tech):
            return (
                m.Discount_rate
                * (1 + m.Discount_rate) ** m.Lifetime_tech[conv_tech]
            ) / ((1 + m.Discount_rate) ** m.Lifetime_tech[conv_tech] - 1)

        self.m.CRF_tech = pe.Param(
            self.m.Conversion_tech,
            initialize=CRF_tech_rule,
            doc="Capital Recovery Factor (CRF) used to annualise the investment cost of generation technologies",
        )

        def CRF_stor_rule(m, stor_tech):
            return (
                m.Discount_rate
                * (1 + m.Discount_rate) ** m.Lifetime_stor[stor_tech]
            ) / ((1 + m.Discount_rate) ** m.Lifetime_stor[stor_tech] - 1)

        self.m.CRF_stor = pe.Param(
            self.m.Storage_tech,
            initialize=CRF_stor_rule,
            doc="Capital Recovery Factor (CRF) used to annualise the investment cost of storage technologies",
        )

        def CRF_network_rule(m):
            return (
                m.Discount_rate
                * (1 + m.Discount_rate) ** m.Network_lifetime
            ) / ((1 + m.Discount_rate) ** m.Network_lifetime - 1)

        self.m.CRF_network = pe.Param(
            initialize=CRF_network_rule,
            doc="Capital Recovery Factor (CRF) used to annualise the investment cost of the networks used by the energy hub",
        )

        def CRF_retrofit_rule(m):
            return (
                m.Discount_rate
                * (1 + m.Discount_rate) ** m.Lifetime_retrofit
            ) / ((1 + m.Discount_rate) ** m.Lifetime_retrofit - 1)

        self.m.CRF_retrofit = pe.Param(
            self.m.Retrofit_scenarios,
            initialize=CRF_retrofit_rule,
            doc="Capital Recovery Factor (CRF) used to annualise the investment cost of the considered retrofit scenarios",
        )

        # Environmental & misc parameters
        # -------------------------------
        self.m.Carbon_factors_import = pe.Param(
            self.m.Energy_carriers_imp,
            self.m.Calendar_years,
            initialize=self.inp["Carbon_factors_import"],
            doc="Carbon emission factor for imported energy carrier eci in year y",
        )
        self.m.epsilon = pe.Param(
            initialize=10 ** 8,
            mutable=True,
            doc="Epsilon value used for the multi-objective epsilon-constrained optimization",
        )

        self.m.BigM = pe.Param(default=10 ** 6, doc="Big M: Sufficiently large value")

        # ==========================
        # Model variables (TABLE A5)
        # ==========================

        # Energy system operation
        self.m.P_conv = pe.Var(
            self.m.Conversion_tech,
            self.m.Energy_system_location,
            self.m.Investment_stages,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            within=pe.NonNegativeReals,
            doc="Input energy to conv tech c at energy loc l, in inv stage w operating in year y, day d and time step t",
        )
        self.m.P_import = pe.Var(
            self.m.Energy_carriers_imp,
            self.m.Energy_system_location,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            within=pe.NonNegativeReals,
            doc="Imported energy carrier eci at energy loc l, in year y, day d and time step t",
        )
        self.m.P_export = pe.Var(
            self.m.Energy_carriers_exp,
            self.m.Energy_system_location,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            within=pe.NonNegativeReals,
            doc="Exported energy carrier ece at energy loc l, in year y, day d and time step t",
        )
        self.m.P_exchange = pe.Var(
            self.m.Energy_carriers_exc,
            self.m.CombLocations,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            within=pe.NonNegativeReals,
            doc="Exchanged of energy carrier exc from location l to loc l', in year y, day d, and time step t",
        )
        self.m.Qin = pe.Var(
            self.m.Storage_tech,
            self.m.Energy_system_location,
            self.m.Investment_stages,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            within=pe.NonNegativeReals,
            doc="Charging energy for storage tech s at en loc l, in inv stage w, operating year y, day d & time steps t",
        )
        self.m.Qout = pe.Var(
            self.m.Storage_tech,
            self.m.Energy_system_location,
            self.m.Investment_stages,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            within=pe.NonNegativeReals,
            doc="Discharging energy for stor tech s at en loc l, in inv stage w, operating year y, day d & time steps t",
        )
        if self.temp_res != 3:
            self.m.SoC = pe.Var(
                self.m.Storage_tech,
                self.m.Energy_system_location,
                self.m.Investment_stages,
                self.m.Calendar_years,
                self.m.Days,
                self.m.Time_steps,
                within=pe.NonNegativeReals,
                doc="Storage state of charge",
            )
        else:
            self.m.SoC = pe.Var(
                self.m.Storage_tech,
                self.m.Energy_system_location,
                self.m.Investment_stages,
                self.m.Calendar_years,
                self.m.Days,
                self.m.Time_steps,
                within=pe.NonNegativeReals,
                doc="Storage state of charge",
            )

        # Energy system design
        self.m.Conv_cap = pe.Var(
            self.m.Conversion_tech,
            self.m.Energy_system_location,
            self.m.Investment_stages,
            within=pe.NonNegativeReals,
            doc="Installed new capacity of conv tech c at loc l in investment stage w",
        )
        self.m.Storage_cap = pe.Var(
            self.m.Storage_tech,
            self.m.Energy_system_location,
            self.m.Investment_stages,
            within=pe.NonNegativeReals,
            doc="Installed new capacity of storage tech s at loc l in investment stage w",
        )
        self.m.y_conv = pe.Var(
            self.m.Conversion_tech,
            self.m.Energy_system_location,
            self.m.Investment_stages,
            within=pe.Binary,
            doc="Binary variable denoting the installation (=1) of energy conversion tech c at loc l in inv stage w",
        )
        self.m.y_stor = pe.Var(
            self.m.Storage_tech,
            self.m.Energy_system_location,
            self.m.Investment_stages,
            within=pe.Binary,
            doc="Binary variable denoting the installation (=1) of energy storage technology at loc l in inv stage w",
        )
        self.m.dm = pe.Var(
            self.m.CombLocations,
            within=pe.NonNegativeReals,
            doc="Pipe diameter for thermal connections between energy system loc l, l2",
        )
        self.m.LC = pe.Var(
            self.m.CombLocations,
            within=pe.NonNegativeReals,
            doc="Interconnection cost to exchange energy carrier ecx between l and l2",
        )
        self.m.y_net = pe.Var(
            self.m.Energy_carriers_exc,
            self.m.CombLocations,
            self.m.Investment_stages,
            within=pe.Binary,
            doc="Binary var denoting the initial connection to exchange energy carrier ecx between loc in inv stg w",
        )

        # Energy system cost and emission performance
        self.m.Total_cost = pe.Var(
            within=pe.NonNegativeReals,
            doc="Total cost for the investment and the operation of the energy hub",
        )
        self.m.Total_carbon = pe.Var(
            within=pe.NonNegativeReals,
            doc="Total carbon emissions due to the operation of the energy hub",
        )
        self.m.Import_cost = pe.Var(
            self.m.Energy_system_location,
            self.m.Calendar_years,
            within=pe.NonNegativeReals,
            doc="Total cost due to energy carrier imports at loc l, in year y"
        )
        self.m.Maintenance_cost = pe.Var(
            self.m.Energy_system_location,
            self.m.Calendar_years,
            within=pe.NonNegativeReals,
            doc="Total maint cost for all conv and stor tech installed at loc l in year y",
        )
        self.m.Export_profit = pe.Var(
            self.m.Energy_system_location,
            self.m.Calendar_years,
            within=pe.NonNegativeReals,
            doc="Total income due to exported electricity at loc l in year y",
        )
        self.m.Salvage_value = pe.Var(
            within=pe.NonNegativeReals,
            doc="Salvage value of all conv and storage tech at location l not reaching the end of their lifetime",
        )

        self.m.Investment_cost = pe.Var(
            within=pe.NonNegativeReals,
            doc="Investment cost of all energy technologies in the energy hub",
        )
        self.m.Operating_cost = pe.Var(
            # self.m.Energy_system_location,
            # self.m.Calendar_years,
            within=pe.NonNegativeReals,
            doc="Total cost due to energy carrier imports at loc l in year y",
        )
        self.m.y_retrofit = pe.Var(
            self.m.Retrofit_scenarios,
            within=pe.Binary,
            doc="Binary variable denoting the retrofit state to be selected",
        )
        self.m.y_on = pe.Var(
            self.m.Dispatchable_tech,
            self.m.Days,
            self.m.Time_steps,
            within=pe.Binary,
            doc="Binary variable indicating the on (=1) or off (=0) state of a dispatchable technology",
        )


        # self.m.z1 = pe.Var(
        #     self.m.Energy_carriers_imp,
        #     self.m.Retrofit_scenarios,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     doc="Variable to represent the product: P_import[ec_imp, d, t] * y_retrofit[ret]",
        # )
        # self.m.z2 = pe.Var(
        #     self.m.Energy_carriers_exp,
        #     # self.m.Retrofit_scenarios,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     doc="Variable to represent the product: P_export[ec_exp, d, t] * y_retrofit[ret]",
        # )
        # self.m.z3 = pe.Var(
        #     self.m.Solar_tech,
        #     self.m.Retrofit_scenarios,
        #     doc="Variable to represent the product: Conv_cap[sol] * y_retrofit[ret]",
        # )
        # self.m.z4 = pe.Var(
        #     self.m.Storage_tech,
        #     self.m.Retrofit_scenarios,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     doc="Variable to represent the product Qin[stor_tech, d, t] * y_retrofit[ret] | Useful only when temp_res = 3 and the C_to_T parameter is used",
        # )
        # self.m.z5 = pe.Var(
        #     self.m.Storage_tech,
        #     self.m.Retrofit_scenarios,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     doc="Variable to represent the product Qout[stor_tech, d, t] * y_retrofit[ret] | Useful only when temp_res = 3 and the C_to_T parameter is used",
        # )

        #%% Model constraints
        def splitCombs(combinations):
            split_ = combinations.split("_")
            keep_ = split_[0] + "_"
            split_ = split_[1]
            key1, key2 = keep_ + split_[0] + split_[1], \
            keep_ + split_[1] + split_[0]
            return key1, key2

        ## CHECKED
        # Energy demand balances
        def Load_balance_rule(m, ec, ecx, ecExp, ecDem, ecImp, l, y, d, t): #A13
            return m.P_import[ecImp, l, y, d, t] \
                + sum(
                m.P_conv[conv_tech, l, w, y, d, t] * \
                    m.Conv_factor[conv_tech, ec, w] * \
                        m.Total_degradation_coefficient[conv_tech, w, y]
                for conv_tech in m.Conversion_tech
                for w in m.Investment_stages
            ) + sum(
                m.Storage_tech_coupling[stor_tech, ec]
                * (m.Qout[stor_tech, l, w, y, d, t] - m.Qin[stor_tech, l, w, y, d, t])
                for stor_tech in m.Storage_tech
                for w in m.Investment_stages
            ) + sum(
                m.P_exchange[ecx, splitCombs(combs)[1], y, d, t]\
                    * (1 - (m.Network_loses_per_m[ecx] * m.Distance_area[splitCombs(combs)[1]])
                       ) - m.P_exchange[ecx, splitCombs(combs)[0], y, d, t]
                    for combs in m.CombLocations
            ) - m.P_export[ecExp, l, y, d, t]  \
                == m.enDem[ecDem, d, t]

        self.m.Load_balance = pe.Constraint(
            self.m.Energy_carriers,
            self.m.Energy_carriers_exc,
            self.m.Energy_carriers_exp,
            self.m.Energy_carriers_dem,
            self.m.Energy_carriers_imp,
            # self.m.CombLocations,
            self.m.Energy_system_location,
            # self.m.Investment_stages,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            rule=Load_balance_rule,
            doc="Energy balance for the energy hub including conversion, storage, losses, exchange and export flows",
        )

        ## CHECKED
        def Capacity_constraint_rule(m, disp, ec, l, w, y, d, t): #A14
            if m.Conv_factor[disp, ec, w] > 0:
                return (
                    m.P_conv[disp, l, w, y, d, t] * \
                        m.Conv_factor[disp, ec, w] * \
                            m.Total_degradation_coefficient[disp, w, y] <= \
                            m.Conv_cap[disp, l, w]
                )
            else:
                return pe.Constraint.Skip
        self.m.Capacity_constraint = pe.Constraint(
            self.m.Dispatchable_tech,
            self.m.Energy_carriers,
            self.m.Energy_system_location,
            self.m.Investment_stages,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            rule=Capacity_constraint_rule,
            doc="Constraint preventing capacity violation for the generation technologies of the energy hub",
        )

        ## CHECKED
        def Solar_input_rule(m, sol, l, w, y, d, t): #A15
            return m.P_conv[sol, l, w, y, d, t] == m.P_solar[l, y, d, t] \
                * m.Conv_cap[sol, l, w]
            # return m.P_conv[sol, l, w, y, d, t] == sum(
            #     m.P_solar[d, t] * m.z3[sol, ret] for ret in m.Retrofit_scenarios
            # )
        self.m.Solar_input = pe.Constraint(
            self.m.Solar_tech,
            self.m.Energy_system_location,
            self.m.Investment_stages,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            rule=Solar_input_rule,
            doc="Constraint connecting the solar radiation per m2 with the area of solar PV technologies",
        )

        ## CHECKED
        def Roof_area_non_violation_rule(m, l): #A16
            # for w in m.Investment_stages
            return sum(m.Conv_cap[sol, l, w] for sol in m.Solar_tech
                                             for w in m.Investment_stages
                       ) \
                <= m.Roof_area
        self.m.Roof_area_non_violation = pe.Constraint(
            self.m.Energy_system_location,
            # self.m.Investment_stages,
            rule=Roof_area_non_violation_rule,
            doc="Non violation of the maximum roof area for solar installations",
        )

        ## CHECKED
        def Annual_consumption_of_biomass_rule(m, l, y): #A17
            return sum(m.P_import[ecImp, l, y, d, t] \
                    * m.Amount_Calendar_days
                    for ecImp in m.Energy_carriers_imp
                    for d in m.Days
                    for t in m.Time_steps
                    if ecImp == "Biomass") \
                        <= (m.Biomass[y] * m.Floor_area[l])
        self.m.Annual_consumption_of_biomass = pe.Constraint(
            self.m.Energy_system_location,
            self.m.Calendar_years,
            # self.m.Days,
            # self.m.Time_steps,
            rule=Annual_consumption_of_biomass_rule,
            doc="limits the total annual consumption of biomass across all sites to account for biomass availability",
        )

        ## CHECKED
        def Big_M_constraint_conversion(m, conv_tech, l, w): #18
            return m.Conv_cap[conv_tech, l, w] \
                <= (m.BigM * m.y_conv[conv_tech, l, w])
        self.m.Big_M_constraint_conversion_def = pe.Constraint(
            self.m.Conversion_tech,
            self.m.Energy_system_location,
            self.m.Investment_stages,
            rule=Big_M_constraint_conversion,
            doc="Big-M const that forces binary variable 𝑌 to be equal to 1, if the variable 𝑁𝐶𝐴𝑃 gets a non-0 value",
        )

        ## CHECKED (only for temp_res == 1)
        def Storage_balance_rule(m, stor_tech, l, w, y, d, t): #A19&A20
            if self.temp_res == 1:
                if t != 1:
                    return m.SoC[stor_tech, l, w, y, d, t] \
                        == (1 - m.Storage_standing_losses[stor_tech]) \
                        * m.SoC[stor_tech, l, w, y, d, t - 1] \
                        + m.Storage_charging_eff[stor_tech] * \
                            m.Total_degradation_coefficient_chdc[stor_tech, w, y] * \
                                m.Qin[stor_tech, l, w, y, d, t] \
                        - (1 / (m.Storage_discharging_eff[stor_tech] * \
                           m.Total_degradation_coefficient_chdc[stor_tech, w, y]
                                )
                          ) \
                        * m.Qout[stor_tech, l, w, y, d, t]
                    
                else:
                    return (
                        m.SoC[stor_tech, l, w, y, d, t]
                        == (1 - m.Storage_standing_losses[stor_tech])
                        * m.SoC[stor_tech, l, w, y, d, t + max(m.Time_steps) - 1]
                        + m.Storage_charging_eff[stor_tech] * \
                            m.Total_degradation_coefficient_chdc[stor_tech, w, y] * \
                                m.Qin[stor_tech, l, w, y, d, t]
                        - (1 / (m.Storage_discharging_eff[stor_tech] * \
                           m.Total_degradation_coefficient_chdc[stor_tech, w, y]))
                        * m.Qout[stor_tech, l, w, y, d, t]
                    )
            elif self.temp_res == 2:
                if t != 1:
                    return (
                        m.SoC[stor_tech, l, w, y, d, t]
                        == (1 - m.Storage_standing_losses[stor_tech])
                        * m.SoC[stor_tech, l, w, y, d, t - 1]
                        + m.Storage_charging_eff[stor_tech] * m.Qin[stor_tech, l, w, y, d, t]
                        - (1 / m.Storage_discharging_eff[stor_tech])
                        * m.Qout[stor_tech, l, w, y, d, t]
                    )
                else:
                    if d != 1:
                        return (
                            m.SoC[stor_tech, l, w, y, d, t]
                            == (1 - m.Storage_standing_losses[stor_tech])
                            * m.SoC[stor_tech, l, w, y, d - 1, t + max(m.Time_steps) - 1]
                            + m.Storage_charging_eff[stor_tech] * m.Qin[stor_tech, l, w, y, d, t]
                            - (1 / m.Storage_discharging_eff[stor_tech])
                            * m.Qout[stor_tech, l, w, y, d, t]
                        )
                    else:
                        return (
                            m.SoC[stor_tech, l, w, y, d, t]
                            == (1 - m.Storage_standing_losses[stor_tech])
                            * m.SoC[stor_tech, l, w, y, d + 364, t + max(m.Time_steps) - 1]
                            + m.Storage_charging_eff[stor_tech] * m.Qin[stor_tech, l, w, y, d, t]
                            - (1 / m.Storage_discharging_eff[stor_tech])
                            * m.Qout[stor_tech, l, w, y, d, t]
                        )
            elif self.temp_res == 3:
                if t != 1:
                    return (
                        m.SoC[stor_tech, l, w, y, d, t]
                        == (1 - m.Storage_standing_losses[stor_tech])
                        * m.SoC[stor_tech, l, w, y, d, t - 1]
                        + m.Storage_charging_eff[stor_tech] * m.Total_degradation_coefficient_chdc[stor_tech, w, y]* sum(
                        # m.Qin[stor_tech, m.C_to_T[ret, d], t] * m.y_retrofit[ret]
                        m.z4[stor_tech, ret, m.C_to_T[ret, d], t]
                        for ret in m.Retrofit_scenarios
                        )
                        - (1 / m.Storage_discharging_eff[stor_tech] * m.Total_degradation_coefficient_chdc[stor_tech, w, y])
                        * sum(
                        # m.Qout[stor_tech, m.C_to_T[ret, d], t] * m.y_retrofit[ret]
                        m.z5[stor_tech, ret, m.C_to_T[ret, d], t]
                        for ret in m.Retrofit_scenarios
                        )
                    )
                else:
                    if d != 1:
                        return (
                            m.SoC[stor_tech, l, w, y, d, t]
                            == (1 - m.Storage_standing_losses[stor_tech])
                            * m.SoC[stor_tech, l, w, y, d - 1, t + max(m.Time_steps) - 1]
                            + m.Storage_charging_eff[stor_tech] * m.Total_degradation_coefficient_chdc[stor_tech, w, y] * sum(
                            # m.Qin[stor_tech, m.C_to_T[ret, d], t] * m.y_retrofit[ret]
                            m.z4[stor_tech, ret, m.C_to_T[ret, d], t]
                            for ret in m.Retrofit_scenarios
                            )
                            - (1 / m.Storage_discharging_eff[stor_tech] * m.Total_degradation_coefficient_chdc[stor_tech, w, y])
                            * sum(
                            # m.Qout[stor_tech, m.C_to_T[ret, d], t] * m.y_retrofit[ret]
                            m.z5[stor_tech, ret, m.C_to_T[ret, d], t]
                            for ret in m.Retrofit_scenarios
                            )
                        )
                    else:
                        return (
                            m.SoC[stor_tech, l, w, y, d, t]
                            == (1 - m.Storage_standing_losses[stor_tech])
                            * m.SoC[stor_tech, l, w, y, d + max(m.Calendar_years) - 1, t + max(m.Time_steps) - 1]
                            + m.Storage_charging_eff[stor_tech] * m.Total_degradation_coefficient_chdc[stor_tech, w, y] * sum(
                            # m.Qin[stor_tech, m.C_to_T[ret, d], t] * m.y_retrofit[ret]
                            m.z4[stor_tech, ret, m.C_to_T[ret, d], t]
                            for ret in m.Retrofit_scenarios
                            )
                            - (1 / m.Storage_discharging_eff[stor_tech] * m.Total_degradation_coefficient_chdc[stor_tech, w, y])
                            * sum(
                            # m.Qout[stor_tech, m.C_to_T[ret, d], t] * m.y_retrofit[ret]
                            m.z5[stor_tech, ret, m.C_to_T[ret, d], t]
                            for ret in m.Retrofit_scenarios
                            )
                        )
        self.m.Storage_balance = pe.Constraint(
            self.m.Storage_tech,
            self.m.Energy_system_location,
            self.m.Investment_stages,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            rule=Storage_balance_rule,
            doc="Energy balance for the storage modules considering incoming and outgoing energy flows",
        )

        ## CHECKED
        def Storage_charg_rate_constr_rule(m, stor_tech, l, w, y, d, t): #A21
            return (
                m.Qin[stor_tech, l, w, y, d, t]
                <= m.Storage_max_charge[stor_tech] * \
                    m.Storage_cap[stor_tech, l, w]
            )
        self.m.Storage_charg_rate_constr = pe.Constraint(
            self.m.Storage_tech,
            self.m.Energy_system_location,
            self.m.Investment_stages,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            rule=Storage_charg_rate_constr_rule,
            doc="Constraint for the maximum allowable charging rate of the storage technologies",
        )

        ## CHECKED
        def Storage_discharg_rate_constr_rule(m, stor_tech, l, w, y, d, t): #A22
            return (
                m.Qout[stor_tech, l, w, y, d, t]
                <= m.Storage_max_discharge[stor_tech] * \
                    m.Storage_cap[stor_tech, l, w]
            )
        self.m.Storage_discharg_rate_constr = pe.Constraint(
            self.m.Storage_tech,
            self.m.Energy_system_location,
            self.m.Investment_stages,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            rule=Storage_discharg_rate_constr_rule,
            doc="Constraint for the maximum allowable discharging rate of the storage technologies",
        )

        ## CHECKED
        def Storage_cap_constr_rule(m, stor_tech, l, w, y, d, t): #A23
            return m.SoC[stor_tech, l, w, y, d, t] \
                <= m.Storage_cap[stor_tech, l, w]

        if self.temp_res == 1 or self.temp_res == 2 :
            self.m.Storage_cap_constr = pe.Constraint(
                self.m.Storage_tech,
                self.m.Energy_system_location,
                self.m.Investment_stages,
                self.m.Calendar_years,
                self.m.Days,
                self.m.Time_steps,
                rule=Storage_cap_constr_rule,
                doc="Constraint for non-violation of the capacity of the storage",
            )
        elif self.temp_res == 3:
            self.m.Storage_cap_constr = pe.Constraint(
                self.m.Storage_tech,
                self.m.Energy_system_location,
                self.m.Investment_stages,
                self.m.Calendar_years,
                self.m.Days,
                self.m.Time_steps,
                rule=Storage_cap_constr_rule,
                doc="Constraint for non-violation of the capacity of the storage",
            )

        ## CHECKED
        def Big_M_constraint_storage(m, stor_tech, l, w): #A24
            return (m.Storage_cap[stor_tech, l, w]) \
                <= (m.BigM * m.y_stor[stor_tech, l, w])
        self.m.Big_M_constraint_storage_def = pe.Constraint(
            self.m.Storage_tech,
            self.m.Energy_system_location,
            self.m.Investment_stages,
            rule=Big_M_constraint_storage,
            doc="Big-M const that forces binary variable 𝑌 to be equal to 1, if the variable 𝑁𝐶𝐴𝑃 gets a non-0 value",
        )

        ## CHECKED
        def Network_connection_rule(m, ecx, combs): #A25
             return sum(m.y_net[ecx, splitCombs(combs)[0], w]
                        for w in m.Investment_stages
                        ) <= 1
        self.m.Network_connection = pe.Constraint(
             self.m.Energy_carriers_exc,
             self.m.CombLocations,
             rule=Network_connection_rule,
             doc="Constraint for the initial connection (occur once during the project horizon)",
        )

        def splitCombs(combinations):
            split_ = combinations.split("_")
            keep_ = split_[0] + "_"
            split_ = split_[1]
            key1, key2 = keep_ + split_[0] + split_[1], \
            keep_ + split_[1] + split_[0]
            return key1, key2

        def bidirectionalRule(m, ecx, combs, w):
            return m.y_net[ecx, splitCombs(combs)[0], w] \
                == m.y_net[ecx, splitCombs(combs)[1], w]

        self.m.bidirectionalC = pe.Constraint(
             self.m.Energy_carriers_exc,
             self.m.CombLocations,
             self.m.Investment_stages,
             rule=bidirectionalRule,
             doc="Constraint for the initial connection (occur once during the project horizon)",
        )

        # def extraRuleNet(m, ecx, combs):
        #     return sum(m.y_net[ecx, combs, w] for w in m.Investment_stages) >= 0
        # self.m.extraRuleNetDef = pe.Constraint(
        #     self.m.Energy_carriers_exc,
        #     self.m.CombLocations,
        #     rule=extraRuleNet,
        #     doc="Constraint for the initial connection (occur once during the project horizon)",
        # )

        ## CHECKED
        def Big_M_constraint_network(m, ecx, combs, y, d, t): #A27
            return m.P_exchange[ecx, splitCombs(combs)[0], y, d, t] <= \
                m.BigM * sum(
                            m.y_net[ecx, splitCombs(combs)[0], w] 
                            for w in m.Investment_stages
                            )
        self.m.Big_M_constraint_network_def = pe.Constraint(
            self.m.Energy_carriers_exc,
            self.m.CombLocations,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            rule=Big_M_constraint_network,
            doc="Const that allows energy to be exch between 2 loc only if a connection between them already exists",
        )

        ## CHECKED
        def Pipe_diameter(m, ecx, combs, y, d, t): #A28
            return m.dm[splitCombs(combs)[0]] >= m.Alpha * \
                m.P_exchange[ecx, splitCombs(combs)[0], y, d, t] \
                    + m.Beta * sum(m.y_net[ecx, splitCombs(combs)[0], w] 
                                   for w in m.Investment_stages
                                   )
        self.m.Pipe_diameter = pe.Constraint(
            self.m.Energy_carriers_exc,
            self.m.CombLocations,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            rule=Pipe_diameter,
            doc="Const that is used to calculate pipe diameter for the thermal interconnection between two locs",
        )

        def bidirectionalPipeRule(m, combs):
            return m.dm[splitCombs(combs)[0]] \
                == m.dm[splitCombs(combs)[1]]

        self.m.bidirectionalPipeC = pe.Constraint(
             self.m.CombLocations,
             rule=bidirectionalPipeRule,
             doc="Constraint for the initial connection (occur once during the project horizon)",
        )

        ## CHECKED
        def Piping_cost_per_m(m, ecx, combs): #A30
            return m.LC[splitCombs(combs)[0]] == \
                m.Gamma * m.dm[splitCombs(combs)[0]] + \
                    m.Delta * sum(m.y_net[ecx, splitCombs(combs)[0], w] 
                                  for w in m.Investment_stages
                              )
        self.m.Piping_cost_per_m = pe.Constraint(
            self.m.Energy_carriers_exc,
            self.m.CombLocations,
            rule=Piping_cost_per_m,
            doc="Const that is used to calculate the piping cost per m of network connection as a function of diameter",
        )

        # ---------------------
        # OBJECTIVE DEFINITIONS
        # ---------------------


        self.m.invTech = pe.Var(
            self.m.Energy_system_location,
            self.m.Investment_stages,
            within=pe.NonNegativeReals,
            doc="Installed new capacity of storage tech s at loc l in investment stage w",
        )
        self.m.invNet = pe.Var(
            self.m.Energy_system_location,
            self.m.Investment_stages,
            within=pe.NonNegativeReals,
            doc="Installed new capacity of storage tech s at loc l in investment stage w",
        )

        def invTechRule(m, l, w):
            return m.invTech[l,w] == sum(
                (
                    m.Fixed_conv_costs[conv_tech, w] * m.y_conv[conv_tech, l, w]
                    + m.Linear_conv_costs[conv_tech, w] * m.Conv_cap[conv_tech, l, w]
                )
                for conv_tech in m.Conversion_tech
            ) + sum(
                    (
                        m.Fixed_stor_costs[stor_tech, w] * m.y_stor[stor_tech, l, w]
                        + m.Linear_stor_costs[stor_tech, w] * m.Storage_cap[stor_tech, l, w]
                    )
                    for stor_tech in m.Storage_tech
                    )

        def invNetRule(m, l, w):
            return m.invNet[l,w] == \
                sum(m.y_net[ecx, splitCombs(combs)[0], w] 
                    * m.LC[splitCombs(combs)[0]] 
                    * .5 
                    * m.Distance_area[splitCombs(combs)[0]]
                    for ecx in m.Energy_carriers_exc
                    for combs in m.CombLocations
                    )

        self.m.invNetC = pe.Constraint(
            self.m.Energy_system_location,
            self.m.Investment_stages,
            rule=invNetRule,
            doc="Input energy to conv tech c at energy loc l, in inv stage w operating in year y, day d and time step t",
        )
        self.m.invTechC = pe.Constraint(
            self.m.Energy_system_location,
            self.m.Investment_stages,
            rule=invTechRule,
            doc="Input energy to conv tech c at energy loc l, in inv stage w operating in year y, day d and time step t",
        )

        def Investment_cost_rule(m): #A7+A8
            return m.Investment_cost == \
                sum(
                    (m.invTech[l,w] ) * \
                    (1 / (1 + m.Discount_rate) ** (w - 1))
                    for l in m.Energy_system_location
                    for w in m.Investment_stages
                    )


            # return m.Investment_cost == sum(
            #     (
            #         m.Fixed_conv_costs[conv_tech, w] * m.y_conv[conv_tech, l, w]
            #         + m.Linear_conv_costs[conv_tech, w] * m.Conv_cap[conv_tech, l, w]
            #     )
            #     for conv_tech in m.Conversion_tech
            #     # for y in m.Calendar_years
            # ) + sum(
            #     (
            #         m.Fixed_stor_costs[stor_tech, w] * m.y_stor[stor_tech, l, w]
            #         + m.Linear_stor_costs[stor_tech, w] * m.Storage_cap[stor_tech, l, w]
            #     )
            #     for stor_tech in m.Storage_tech
            #     # for y in m.Calendar_years
            # ) \
            #     + (m.y_net[ecx, combs, w] * m.LC[combs] * .5 * m.Distance_area[combs]
            # ) \
            #     * (1 / (1 + m.Discount_rate) ** (m.Investment_stages - 1))
            #     # m.y_net[ecx, combs, w] * m.LC[combs] * .5 * m.Distance_area[combs]
            #     # + m.Network_inv_cost_per_m * m.Network_length * m.CRF_network




        self.m.Investment_cost_def = pe.Constraint(
            # self.m.Energy_carriers_exc,
            # self.m.CombLocations,
            # self.m.Energy_system_location,
            # self.m.Investment_stages,
            rule=Investment_cost_rule,
            doc="Definition of the investment cost component of the total energy system cost",
        )

        def Import_cost_rule(m, l, y):  #A9
            return m.Import_cost[l, y] == sum(
                (m.Import_prices[ec_imp, y] * \
                 m.Number_of_days[d] * \
                 m.P_import[ec_imp, l, y, d, t])
                for ec_imp in m.Energy_carriers_imp
                # for l in m.Energy_system_location
                # for y in m.Calendar_years
                for d in m.Days
                for t in m.Time_steps
            )

        self.m.Import_cost_def = pe.Constraint(
            self.m.Energy_system_location,
            self.m.Calendar_years,
            rule=Import_cost_rule,
            doc="import cost Rule Def",
        )

        def Maintenance_cost_rule(m, l, y): #A10
            return m.Maintenance_cost[l, y] == sum((
                (
                    m.Linear_conv_costs[conv_tech, w] * m.Conv_cap[conv_tech, l, w]\
                        + m.Fixed_conv_costs[conv_tech, w] * m.y_conv[conv_tech, l, w]
                )) * m.Omc_cost[conv_tech]\
                    for conv_tech in m.Conversion_tech
                    for w in m.Investment_stages
                    # for y in m.Calendar_years
            ) + sum((
                (
                    m.Linear_stor_costs[stor_tech, w] * m.Storage_cap[stor_tech, l, w]\
                        + m.Fixed_stor_costs[stor_tech, w] * m.y_stor[stor_tech, l, w]
                )) * m.Oms_cost[stor_tech]\
                for stor_tech in m.Storage_tech
                for w in m.Investment_stages
                # for y in m.Calendar_years
            )
        self.m.Maintenance_cost_def = pe.Constraint(
            self.m.Energy_system_location,
            self.m.Calendar_years,
            rule=Maintenance_cost_rule,
            doc="Maintenance cost",
        )

        def exportRule(m, ec_exp, l, y, d, t):
            return m.P_export[ec_exp, l, y, d, t] >= 0
        self.m.exportRuleDef = pe.Constraint(
            self.m.Energy_carriers_exp,
            self.m.Energy_system_location,
            self.m.Calendar_years,
            self.m.Days,
            self.m.Time_steps,
            rule=exportRule,
            doc="exportRule",
        )

        def Export_profit_rule(m, l, y): #A11
            return m.Export_profit[l, y] == sum(
                m.Export_prices[ec_exp, y] * \
                    m.Number_of_days[d] * \
                        m.P_export[ec_exp, l, y, d, t] # m.z2[ec_exp, ret, d, t]
                for ec_exp in m.Energy_carriers_exp
                # for l in m.Energy_system_location
                # for y in m.Calendar_years
                # for ret in m.Retrofit_scenarios
                for d in m.Days
                for t in m.Time_steps
            )
        self.m.Export_profit_def = pe.Constraint(
            self.m.Energy_system_location,
            self.m.Calendar_years,
            rule=Export_profit_rule,
            doc="Definition of the income due to electricity exports component of the total energy system cost",
        )

        def Operating_cost_rule(m): #A9+A10-A11
            # return m.Operating_cost[l, y] == m.Import_cost[l,y] + \
            #     m.Maintenance_cost[l,y] - \
            #         m.Export_profit[l,y]
            return m.Operating_cost == \
                sum(
                    (m.Import_cost[l,y] + m.Maintenance_cost[l,y] \
                        - m.Export_profit[l,y]) * \
                    (1 / (1 + m.Discount_rate) ** (y))
                    for l in m.Energy_system_location
                    for y in m.Calendar_years
                    )
        self.m.Operating_cost_def = pe.Constraint(
            # self.m.Energy_system_location,
            # self.m.Calendar_years,
            rule=Operating_cost_rule,
            doc="Definition of the operating cost component of the total energy system cost",
        )
 

        self.m.Individual_salvage_value = pe.Var(
            self.m.Energy_system_location,
            within=pe.NonNegativeReals,
            doc="Total income due to exported electricity at loc l in year y",
        )

        def Individual_salvage_value_rule(m, l): #A12
            return m.Individual_salvage_value[l] == sum((
                (
                    m.Linear_conv_costs[conv_tech, w] * m.Conv_cap[conv_tech, l, w]\
                        + m.Fixed_conv_costs[conv_tech, w] * m.y_conv[conv_tech, l, w]
                )) * m.Salvage_conversion[conv_tech, w] \
                    for conv_tech in m.Conversion_tech
                    for w in m.Investment_stages
                    # for y in m.Calendar_years
            ) + sum((
                (
                    m.Linear_stor_costs[stor_tech, w] * m.Storage_cap[stor_tech, l, w]\
                        + m.Fixed_stor_costs[stor_tech, w] * m.y_stor[stor_tech, l, w]
                )) * m.Salvage_storage[stor_tech, w] \
                for stor_tech in m.Storage_tech
                for w in m.Investment_stages
                # for y in m.Calendar_years
            )
        self.m.Individual_salvage_value_def = pe.Constraint(
            self.m.Energy_system_location,
            # self.m.Investment_stages,
            rule=Individual_salvage_value_rule,
            doc="Individual salvage value terms",
        )

        def Salvage_value_rule(m):
            return m.Salvage_value == sum(
                (m.Individual_salvage_value[l] * \
                 (1/(1 + m.Discount_rate) ** max(m.Calendar_years)+1))
                for l in m.Energy_system_location
                )

        self.m.Salvage_value_def = pe.Constraint(
            # self.m.Energy_system_location,
            # self.m.Investment_stages,
            rule=Salvage_value_rule,
            doc="Salvage value terms",
        )

        # Additional constraints
        # def expRule(m):
        #     return (m.Export_profit >= m.Maintenance_cost[l,y])
        # self.m.expRuleDef = pe.Constraint(
        #     rule=expRule,
        #     doc="expRule",
        # )
        # def salRules(m):
        #     return (m.Salvage_value <= m.Operating_cost)
        # self.m.salRuleDef = pe.Constraint(
        #     rule=salRules,
        #     doc="salRules",
        # )
        # def salRules3(m):
        #     return (m.Salvage_value <= m.Investment_cost)
        # self.m.salRuleDef3 = pe.Constraint(
        #     rule=salRules3,
        #     doc="salRules3",
        # )
        # def salRules(m):
        #     return (m.Salvage_value <= m.Total_cost)
        # self.m.salRuleDef = pe.Constraint(
        #     rule=salRules,
        #     doc="salRules",
        # )
        # def opRules(m):
        #     return (m.Operating_cost <= m.Total_cost)
        # self.m.opRulesDef = pe.Constraint(
        #     rule=opRules,
        #     doc="opRules",
        # )
        # def invRules(m):
        #     return (m.Investment_cost <= m.Total_cost)
        # self.m.invRulesDef = pe.Constraint(
        #     rule=invRules,
        #     doc="invRules",
        # )

        # ---------------
        # MAIN OBJECTIVES
        # ---------------

        def Total_cost_rule(m): #A5
            return m.Total_cost == \
                m.Investment_cost + m.Operating_cost - m.Salvage_value

        self.m.Total_cost_def = pe.Constraint(
            rule=Total_cost_rule,
            doc="Definition of the total cost model objective function",
        )

        def Total_carbon_rule(m): #A6
            return m.Total_carbon == sum(
                m.Carbon_factors_import[ec_imp, y]
                * m.Number_of_days[d]
                * m.P_import[ec_imp, l, y, d, t] # MAYBE CHANGE TO m.P_import[ec_imp, l, y, d, t]
                for ec_imp in m.Energy_carriers_imp
                for l in m.Energy_system_location
                for y in m.Calendar_years
                # for ret in m.Retrofit_scenarios
                for d in m.Days
                for t in m.Time_steps
            )
        self.m.Total_carbon_def = pe.Constraint(
            rule=Total_carbon_rule,
            doc="Definition of the total carbon emissions model objective function",
        )

        # Carbon constraint
        def Carbon_constraint_rule(m):
            return m.Total_carbon <= m.epsilon
        self.m.Carbon_constraint = pe.Constraint(
            rule=Carbon_constraint_rule,
            doc="Constraint setting an upper limit to the total carbon emissions of the system",
        )

        # def z1_rule_1(m, ec_imp, ret, d, t):
        #     return m.z1[ec_imp, ret, d, t] >= 0
        # self.m.z1_rule_1_constr = pe.Constraint(
        #     self.m.Energy_carriers_imp,
        #     self.m.Retrofit_scenarios,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z1_rule_1,
        #     doc="Auxiliary constraint for variable z1",
        # )
        # def z1_rule_2(m, ec_imp, ret, d, t):
        #     return m.z1[ec_imp, ret, d, t] <= m.BigM * m.y_retrofit[ret]
        # self.m.z1_rule_2_constr = pe.Constraint(
        #     self.m.Energy_carriers_imp,
        #     self.m.Retrofit_scenarios,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z1_rule_2,
        #     doc="Auxiliary constraint for variable z1",
        # )
        # def z1_rule_3(m, ec_imp, ret, l, y, d, t):
        #     return m.P_import[ec_imp, l, y, d, t] - m.z1[ec_imp, ret, d, t] >= 0
        # self.m.z1_rule_3_constr = pe.Constraint(
        #     self.m.Energy_carriers_imp,
        #     self.m.Retrofit_scenarios,
        #     self.m.Energy_system_location,
        #     self.m.Calendar_years,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z1_rule_3,
        #     doc="Auxiliary constraint for variable z1",
        # )
        # def z1_rule_4(m, ec_imp, ret, l, y, d, t):
        #     return m.P_import[ec_imp, l, y, d, t] - m.z1[ec_imp, ret, d, t] <= m.BigM * (
        #         1 - m.y_retrofit[ret]
        #     )
        # self.m.z1_rule_4_constr = pe.Constraint(
        #     self.m.Energy_carriers_imp,
        #     self.m.Retrofit_scenarios,
        #     self.m.Energy_system_location,
        #     self.m.Calendar_years,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z1_rule_4,
        #     doc="Auxiliary constraint for variable z1",
        # )
        # def z2_rule_1(m, ec_exp, d, t):
        #     return m.z2[ec_exp, d, t] >= 0
        # self.m.z2_rule_1_constr = pe.Constraint(
        #     self.m.Energy_carriers_exp,
        #     # self.m.Retrofit_scenarios,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z2_rule_1,
        #     doc="Auxiliary constraint for variable z2",
        # )
        # def z2_rule_2(m, ec_exp, ret, d, t):
        #     return m.z2[ec_exp, d, t] <= m.BigM * m.y_retrofit[ret]
        # self.m.z2_rule_2_constr = pe.Constraint(
        #     self.m.Energy_carriers_exp,
        #     self.m.Retrofit_scenarios,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z2_rule_2,
        #     doc="Auxiliary constraint for variable z2",
        # )
        # def z2_rule_3(m, ec_exp, l, y, d, t):
        #     return m.P_export[ec_exp, l, y, d, t] \
        #         - m.z2[ec_exp, d, t] >= 0
        # self.m.z2_rule_3_constr = pe.Constraint(
        #     self.m.Energy_carriers_exp,
        #     # self.m.Retrofit_scenarios,
        #     self.m.Energy_system_location,
        #     self.m.Calendar_years,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z2_rule_3,
        #     doc="Auxiliary constraint for variable z2",
        # )
        # def z2_rule_4(m, ec_exp, ret, l, y, d, t):
        #     return m.P_export[ec_exp, l, y, d, t] - m.z2[ec_exp, d, t] <= m.BigM * (
        #         1 - m.y_retrofit[ret]
        #     )
        # self.m.z2_rule_4_constr = pe.Constraint(
        #     self.m.Energy_carriers_exp,
        #     self.m.Retrofit_scenarios,
        #     self.m.Energy_system_location,
        #     self.m.Calendar_years,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z2_rule_4,
        #     doc="Auxiliary constraint for variable z2",
        # )
        # def z3_rule_1(m, sol, ret):
        #     return m.z3[sol, ret] >= 0
        # self.m.z3_rule_1_constr = pe.Constraint(
        #     self.m.Solar_tech,
        #     self.m.Retrofit_scenarios,
        #     rule=z3_rule_1,
        #     doc="Auxiliary constraint for variable z3",
        # )
        # def z3_rule_2(m, sol, ret):
        #     return m.z3[sol, ret] <= m.BigM * m.y_retrofit[ret]
        # self.m.z3_rule_2_constr = pe.Constraint(
        #     self.m.Solar_tech,
        #     self.m.Retrofit_scenarios,
        #     rule=z3_rule_2,
        #     doc="Auxiliary constraint for variable z3",
        # )
        # def z3_rule_3(m, sol, ret, l, w):
        #     return m.Conv_cap[sol, l, w] - m.z3[sol, ret] >= 0
        # self.m.z3_rule_3_constr = pe.Constraint(
        #     self.m.Solar_tech,
        #     self.m.Retrofit_scenarios,
        #     self.m.Energy_system_location,
        #     self.m.Investment_stages,
        #     rule=z3_rule_3,
        #     doc="Auxiliary constraint for variable z3",
        # )
        # def z3_rule_4(m, sol, ret, l, w):
        #     return m.Conv_cap[sol, l, w] - m.z3[sol, ret] \
        #         <= m.BigM * (1 - m.y_retrofit[ret])
        # self.m.z3_rule_4_constr = pe.Constraint(
        #     self.m.Solar_tech,
        #     self.m.Retrofit_scenarios,
        #     self.m.Energy_system_location,
        #     self.m.Investment_stages,
        #     rule=z3_rule_4,
        #     doc="Auxiliary constraint for variable z3",
        # )
        # def z4_rule_1(m, stor_tech, ret, d, t):
        #     return m.z4[stor_tech, ret, d, t] >= 0
        # self.m.z4_rule_1_constr = pe.Constraint(
        #     self.m.Storage_tech,
        #     self.m.Retrofit_scenarios,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z4_rule_1,
        #     doc="Auxiliary constraint for variable z4",
        # )
        # def z4_rule_2(m, stor_tech, ret, d, t):
        #     return m.z4[stor_tech, ret, d, t] <= m.BigM * m.y_retrofit[ret]
        # self.m.z4_rule_2_constr = pe.Constraint(
        #     self.m.Storage_tech,
        #     self.m.Retrofit_scenarios,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z4_rule_2,
        #     doc="Auxiliary constraint for variable z4",
        # )
        # def z4_rule_3(m, stor_tech, ret, l, w, y, d, t):
        #     return m.Qin[stor_tech, l, w, y, d, t] - \
        #         m.z4[stor_tech, ret, d, t] >= 0
        # self.m.z4_rule_3_constr = pe.Constraint(
        #     self.m.Storage_tech,
        #     self.m.Retrofit_scenarios,
        #     self.m.Energy_system_location,
        #     self.m.Investment_stages,
        #     self.m.Calendar_years,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z4_rule_3,
        #     doc="Auxiliary constraint for variable z4",
        # )
        # def z4_rule_4(m, stor_tech, ret, l, w, y, d, t):
        #     return m.Qin[stor_tech, l, w, y, d, t] - \
        #         m.z4[stor_tech, ret, d, t] <= m.BigM * (
        #         1 - m.y_retrofit[ret]
        #     )
        # self.m.z4_rule_4_constr = pe.Constraint(
        #     self.m.Storage_tech,
        #     self.m.Retrofit_scenarios,
        #     self.m.Energy_system_location,
        #     self.m.Investment_stages,
        #     self.m.Calendar_years,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z4_rule_4,
        #     doc="Auxiliary constraint for variable z4",
        # )
        # def z5_rule_1(m, stor_tech, ret, d, t):
        #     return m.z5[stor_tech, ret, d, t] >= 0
        # self.m.z5_rule_1_constr = pe.Constraint(
        #     self.m.Storage_tech,
        #     self.m.Retrofit_scenarios,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z5_rule_1,
        #     doc="Auxiliary constraint for variable z5",
        # )
        # def z5_rule_2(m, stor_tech, ret, d, t):
        #     return m.z5[stor_tech, ret, d, t] <= m.BigM * m.y_retrofit[ret]
        # self.m.z5_rule_2_constr = pe.Constraint(
        #     self.m.Storage_tech,
        #     self.m.Retrofit_scenarios,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z5_rule_2,
        #     doc="Auxiliary constraint for variable z5",
        # )
        # def z5_rule_3(m, stor_tech, ret, l, w, y, d, t):
        #     return m.Qout[stor_tech, l, w, y, d, t] - m.z5[stor_tech, ret, d, t] >= 0
        # self.m.z5_rule_3_constr = pe.Constraint(
        #     self.m.Storage_tech,
        #     self.m.Retrofit_scenarios,
        #     self.m.Energy_system_location,
        #     self.m.Investment_stages,
        #     self.m.Calendar_years,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z5_rule_3,
        #     doc="Auxiliary constraint for variable z5",
        # )
        # def z5_rule_4(m, stor_tech, ret, l, w, y, d, t):
        #     return m.Qout[stor_tech, l, w, y, d, t] - m.z5[stor_tech, ret, d, t] <= m.BigM * (
        #         1 - m.y_retrofit[ret]
        #     )
        # self.m.z5_rule_4_constr = pe.Constraint(
        #     self.m.Storage_tech,
        #     self.m.Retrofit_scenarios,
        #     self.m.Energy_system_location,
        #     self.m.Investment_stages,
        #     self.m.Calendar_years,
        #     self.m.Days,
        #     self.m.Time_steps,
        #     rule=z5_rule_4,
        #     doc="Auxiliary constraint for variable z5",
        # )



        #%% Objective functions

        # Cost objective
        def cost_obj_rule(m):return m.Total_cost
        self.m.Cost_obj = pe.Objective(rule=cost_obj_rule, sense=pe.minimize)

        # Carbon objective
        def carbon_obj_rule(m):return m.Total_carbon
        self.m.Carbon_obj = pe.Objective(rule=carbon_obj_rule, sense=pe.minimize)

    def solve(self, mip_gap=0.001, time_limit=10 ** 8, results_folder=".\\"):
        """
        Solves the model and outputs model results

        Two types of model outputs are generated:

            1. All the model definitions, constraints, parameter and variable values are given for each objective/Pareto point in the self.results object.
            2. The key objective function, design and operation results are given as follows:
                * obj: Contains the total cost, cost breakdown, and total carbon results. It is a data frame for all optim_mode settings.
                * dsgn: Contains the generation and storage capacities of all candidate technologies. It is a data frame for all optim_mode settings.
                * oper: Contains the generation, export and storage energy flows for all time steps considered. It is a single dataframe when optim_mode is 1 or 2 (single-objective) and a list of dataframes for each Pareto point when optim_mode is set to 3 (multi-objective).
        """

        import Output_functions as of
        import pickle as pkl

        optimizer = pyomo.opt.SolverFactory("gurobi")
        optimizer.options["MIPGap"] = mip_gap
        optimizer.options["TimeLimit"] = time_limit
        targetObjective = "Single Objective (Cost minimization)" \
            if self.optim_mode == 1 else "Single Objective (Carbon minimization)" \
                if self.optim_mode == 2 else \
                    "Multi Objective (Cost & Carbon minimization)"
        print(targetObjective)

        if self.optim_mode == 1:

            # Cost minimization
            all_vars = [None]

            self.m.Carbon_obj.deactivate()
            results = optimizer.solve(
                self.m, tee=True, keepfiles=True, logfile="gur.log"
            )
            # if self.invStage == 0:
            print("SAVING RESULTS...")
            # Save results
            self.m.solutions.store_to(results)
            all_vars[0] = of.get_all_vars(self.m)

            # JSON file with results
            results.write(
                filename=results_folder + "\cost_min_solver_results" + str(self.invStage) + ".json" , format="json"
            )

            # Pickle file with all variable values
            # file = open(results_folder + "\cost_min.p", "wb")
            # pkl.dump(all_vars, file)
            # file.close()

            ## Excel file with all variable values
            # of.write_all_vars_to_excel(all_vars[0],
            #                            results_folder + "\cost_min_" \
            #                             + str(self.invStage))
            print("SAVING OPERATION EXECUTED!")
            # else:pass

        elif self.optim_mode == 2:

            # Carbon minimization
            # ===================
            all_vars = [None]

            self.m.Carbon_obj.activate()
            self.m.Cost_obj.deactivate()
            optimizer.solve(self.m, tee=True, keepfiles=True, logfile="gur.log")
            carb_min = pe.value(self.m.Total_system_carbon) * 1.01

            self.m.epsilon = carb_min
            self.m.Carbon_obj.deactivate()
            self.m.Cost_obj.activate()
            results = optimizer.solve(
                self.m, tee=True, keepfiles=True, logfile="gur.log"
            )

            # Save results
            # ------------
            # self.m.solutions.store_to(results)
            all_vars[0] = of.get_all_vars(self.m)

            # # JSON file with results
            # results.write(
            #     filename=results_folder + "\carb_min_solver_results.json", format="json"
            # )

            # # Pickle file with all variable values
            # file = open(results_folder + "\carb_min.p", "wb")
            # pkl.dump(all_vars, file)
            # file.close()

            # Excel file with all variable values
            of.write_all_vars_to_excel(all_vars[0], results_folder + "\carb_min")

        elif self.optim_mode == 3:

            # Multi-objective optimization
            # ============================
            all_vars = [None] * (self.num_of_pfp + 2)

            # Cost minimization
            # -----------------
            self.m.Carbon_obj.deactivate()
            print("----------\nCOST MINIMIZATION OBJECTIVE BEING EXECUTED!!\n(CARBON OBJECTIVE IS DEACTIVATED)")

            results = optimizer.solve(
                self.m, tee=True, keepfiles=True, logfile="gur.log"
            )
            # carb_max = pe.value(self.m.Total_system_carbon)

            # Save results
            self.m.solutions.store_to(results)
            all_vars[0] = of.get_all_vars(self.m)

            # JSON file with results
            results.write(
                filename=results_folder + "\MO_solver_results_1.json", format="json"
            )

            # # Pickle file with all variable values
            # file = open(results_folder + "\multi_obj_1.p", "wb")
            # pkl.dump([all_vars[0]], file)
            # file.close()

            # Excel file with all variable values
            # of.write_all_vars_to_excel(all_vars[0], results_folder + "\multi_obj_1")

            # Carbon minimization
            # -------------------
            self.m.Carbon_obj.activate()
            self.m.Cost_obj.deactivate()
            print("----------\nCARBON MINIMIZATION OBJECTIVE BEING EXECUTED!!\n(COST OBJECTIVE IS DEACTIVATED)")
            optimizer.solve(self.m, tee=True, keepfiles=True, logfile="gur.log")
            # carb_min = pe.value(self.m.Total_system_carbon) * 1.01

            # Pareto points
            # -------------
            if self.num_of_pfp == 0:
                # self.m.epsilon = carb_min
                self.m.Carbon_obj.deactivate()
                self.m.Cost_obj.activate()
                results = optimizer.solve(
                    self.m, tee=True, keepfiles=True, logfile="gur.log"
                )

                # Save results
                # ------------
                # self.m.solutions.store_to(results)
                all_vars[1] = of.get_all_vars(self.m)

                # # JSON file with results
                # results.write(
                #     filename=results_folder + "\MO_solver_results_2.json", format="json"
                # )

                # # Pickle file with all variable values
                # file = open(results_folder + "\multi_obj_2.p", "wb")
                # pkl.dump([all_vars[1]], file)
                # file.close()

                # Excel file with all variable values
                of.write_all_vars_to_excel(all_vars[1], results_folder + "\multi_obj_2")

            else:
                self.m.Carbon_obj.deactivate()
                self.m.Cost_obj.activate()

                # interval = (carb_max - carb_min) / (self.num_of_pfp + 1)
                # steps = list(np.arange(carb_min, carb_max, interval))
                # steps.reverse()
                # print(steps)

                for i in range(1, self.num_of_pfp + 1 + 1):
                    # self.m.epsilon = steps[i - 1]
                    # print(self.m.epsilon.extract_values())
                    results = optimizer.solve(
                        self.m, tee=True, keepfiles=True, logfile="gur.log"
                    )

                    # Save results
                    # ------------
                    # self.m.solutions.store_to(results)
                    all_vars[i] = of.get_all_vars(self.m)

                    # JSON file with results
                    results.write(
                        filename=results_folder
                                 + "\MO_solver_results_"
                                 + str(i + 1)
                                 + ".json",
                        format="json",
                    )

                    # Pickle file with all variable values
                    # file = open(
                    #     results_folder + "\multi_obj_" + str(i + 1) + ".p", "wb"
                    # )
                    # pkl.dump([all_vars[i]], file)
                    # file.close()

                    # # Excel file with all variable values
                    # of.write_all_vars_to_excel(
                    #     all_vars[i], results_folder + "\multi_obj_" + str(i + 1)
                    # )

            # Pickle file with all variable values for all multi-objective runs
            file = open(results_folder + "\multi_obj_all_points.p", "wb")
            pkl.dump(all_vars, file)
            file.close()

if __name__ == "__main__":
    pass









        # # -------------------from original code, not in paper
        # def Minimum_part_load_constr_rule1(m, disp, ec, l, w, y, d, t):
        #     return (
        #         m.P_conv[disp, l, w, y, d, t] * m.Conv_factor[disp, ec, w]
        #         <= m.BigM * m.y_on[disp, d, t]
        #     )
        # self.m.Mininum_part_rule_constr1 = pe.Constraint(
        #     (
        #         (disp, ec, l, w, y, d, t)
        #         for disp in self.m.Dispatchable_tech
        #         for ec in self.m.Energy_carriers
        #         for l in self.m.Energy_system_location
        #         for w in self.m.Investment_stages
        #         for y in self.m.Calendar_years
        #         for d in self.m.Days
        #         for t in self.m.Time_steps
        #         if self.m.Conv_factor[disp, ec, w] > 0
        #     ),
        #     rule=Minimum_part_load_constr_rule1,
        #     doc="Constraint enforcing a minimum load during the operation of a dispatchable energy technology",
        # )

        # def Fixed_cost_constr_rule(m, conv_tech, l, w):
        #     return m.Conv_cap[conv_tech, l, w] \
        #         <= m.BigM * m.y_conv[conv_tech, l, w]
        # self.m.Fixed_cost_constr = pe.Constraint(
        #     self.m.Conversion_tech,
        #     self.m.Energy_system_location,
        #     self.m.Investment_stages,
        #     rule=Fixed_cost_constr_rule,
        #     doc="Constraint for the formulation of the fixed cost in the objective function",
        # )

        # def Max_allowable_storage_cap_rule(m, stor_tech, l, w):
        #     return m.Storage_cap[stor_tech, l, w] \
        #         <= m.Storage_max_cap[stor_tech]
        # self.m.Max_allowable_storage_cap = pe.Constraint(
        #     self.m.Storage_tech,
        #     self.m.Energy_system_location,
        #     self.m.Investment_stages,
        #     rule=Max_allowable_storage_cap_rule,
        #     doc="Constraint enforcing the maximum allowable storage capacity per type of storage technology",
        # )

        # def Fixed_cost_storage_rule(m, stor_tech, l, w):
        #     return m.Storage_cap[stor_tech, l, w] \
        #         <= m.BigM * m.y_stor[stor_tech, l, w]
        # self.m.Fixed_cost_storage = pe.Constraint(
        #     self.m.Storage_tech,
        #     self.m.Energy_system_location,
        #     self.m.Investment_stages,
        #     rule=Fixed_cost_storage_rule,
        #     doc="Constraint for the formulation of the fixed cost in the objective function",
        # )

        # def One_retrofit_state_rule(m):
        #     return sum(m.y_retrofit[ret] for ret in m.Retrofit_scenarios) == 1
        # self.m.One_retrofit_state_def = pe.Constraint(
        #     rule=One_retrofit_state_rule,
        #     doc="Constraint to impose that one retrofit state out of all possible must be selected",
        # )