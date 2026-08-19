import os
import csv
import math
import pythoncom
import clr

from scipy.stats import qmc

pythoncom.CoInitialize()


# ============================================================
# DWSIM INSTALLATION
# ============================================================

dwsimpath = r"C:\Users\Rupali Waghmare\AppData\Local\DWSIM"


# ============================================================
# LOAD DWSIM DLLs
# ============================================================

dlls = [
    "CapeOpen.dll",
    "DWSIM.Automation.dll",
    "DWSIM.Interfaces.dll",
    "DWSIM.GlobalSettings.dll",
    "DWSIM.SharedClasses.dll",
    "DWSIM.Thermodynamics.dll",
    "DWSIM.Thermodynamics.ThermoC.dll",
    "DWSIM.UnitOperations.dll",
    "DWSIM.Inspector.dll",
    "System.Buffers.dll",
]

for dll in dlls:

    path = os.path.join(
        dwsimpath,
        dll
    )

    print("Loading:", path)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"DLL not found:\n{path}"
        )

    clr.AddReference(path)


print()
print("DWSIM DLLs loaded.")


# ============================================================
# DWSIM IMPORTS
# ============================================================

from DWSIM.Automation import Automation3
from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType


# ============================================================
# PROJECT PATH
# ============================================================

project_root = os.path.dirname(
    os.path.abspath(__file__)
)

output_dir = os.path.join(
    project_root,
    "data",
    "01_validation_runs"
)

os.makedirs(
    output_dir,
    exist_ok=True
)

output_csv = os.path.join(
    output_dir,
    "dataset_256_dwsim.csv"
)


# ============================================================
# DATASET SETTINGS
# ============================================================

N = 256

SEED = 42

FEED_FLOW_KMOL_H = 100.0

ATM_TO_PA = 101325.0


# ============================================================
# INPUT RANGES
# ============================================================

PRESSURE_MIN = 1.0
PRESSURE_MAX = 2.0

VAPOR_MIN = 0.00
VAPOR_MAX = 0.30

BENZENE_MIN = 0.30
BENZENE_MAX = 0.70

STAGES_MIN = 10
STAGES_MAX = 30

FEED_STAGE_MIN = 0.30
FEED_STAGE_MAX = 0.70

REFLUX_MIN = 1.2
REFLUX_MAX = 4.5

BOTTOMS_MIN = 0.40
BOTTOMS_MAX = 0.60


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def scale(
        x,
        minimum,
        maximum
):

    return (
            minimum
            +
            x * (maximum - minimum)
    )


def finite(value):

    try:

        return math.isfinite(
            float(value)
        )

    except:

        return False


# ============================================================
# SOBOL SAMPLING
# ============================================================

print()
print("=" * 75)
print("GENERATING SOBOL DESIGN")
print("=" * 75)

print(
    f"Dimensions : 7"
)

print(
    f"Samples    : {N}"
)

print(
    f"Seed       : {SEED}"
)

print(
    "Sampling   : Sobol"
)

print(
    "Power      : 2^8 = 256"
)


sampler = qmc.Sobol(
    d=7,
    scramble=True,
    seed=SEED
)


# 256 = 2^8
sobol_points = sampler.random_base2(
    m=8
)


print(
    "Sobol sampling generated."
)


# ============================================================
# CSV COLUMNS
# ============================================================

csv_columns = [

    # -------------------------
    # Seven sampled inputs
    # -------------------------

    "pressure_atm",

    "requested_vapor_fraction",

    "benzene_feed_fraction",

    "toluene_feed_fraction",

    "stages",

    "feed_stage",

    "feed_stage_fraction",

    "reflux_ratio",

    "bottoms_fraction",

    # -------------------------
    # Feed information
    # -------------------------

    "feed_flow_kmol_h",

    "feed_temperature_C",

    # -------------------------
    # DWSIM outputs
    # -------------------------

    "x_D_benzene",

    "x_B_benzene",

    "Q_C",

    "Q_R",

    # -------------------------
    # Validation
    # -------------------------

    "dwsim_solved",

    "column_calculated",

    "column_error",

    "output_values_valid",

    "composition_valid",

    "temperature_valid",

    "case_valid",

    "error_message",
]


# ============================================================
# RESULTS
# ============================================================

results = []

successful_cases = 0

failed_cases = 0


# ============================================================
# MAIN LOOP
# ============================================================

for case_index in range(N):

    print()
    print()
    print("=" * 75)
    print(
        f"CASE {case_index + 1}/{N}"
    )
    print("=" * 75)


    # ========================================================
    # SOBOL POINT
    # ========================================================

    point = sobol_points[
        case_index
    ]


    # ========================================================
    # INPUT 1
    # PRESSURE
    # ========================================================

    pressure_atm = scale(
        point[0],
        PRESSURE_MIN,
        PRESSURE_MAX
    )


    # ========================================================
    # INPUT 2
    # VAPOR FRACTION
    # ========================================================

    requested_vf = scale(
        point[1],
        VAPOR_MIN,
        VAPOR_MAX
    )


    # ========================================================
    # INPUT 3
    # BENZENE FRACTION
    # ========================================================

    benzene_fraction = scale(
        point[2],
        BENZENE_MIN,
        BENZENE_MAX
    )


    # ========================================================
    # DERIVED:
    # TOLUENE FRACTION
    # ========================================================

    toluene_fraction = (
            1.0 -
            benzene_fraction
    )


    # ========================================================
    # INPUT 4
    # NUMBER OF STAGES
    # ========================================================

    stages = int(
        round(
            scale(
                point[3],
                STAGES_MIN,
                STAGES_MAX
            )
        )
    )


    stages = max(
        STAGES_MIN,
        min(
            STAGES_MAX,
            stages
        )
    )


    # ========================================================
    # INPUT 5
    # FEED-STAGE FRACTION
    # ========================================================

    feed_stage_fraction = scale(
        point[4],
        FEED_STAGE_MIN,
        FEED_STAGE_MAX
    )


    # Convert to actual integer stage.

    feed_stage = int(
        round(
            stages *
            feed_stage_fraction
        )
    )


    # Make sure feed stage is valid.

    feed_stage = max(
        1,
        min(
            stages - 1,
            feed_stage
        )
    )


    # Actual fraction after integer conversion.

    actual_feed_stage_fraction = (
            feed_stage /
            stages
    )


    # ========================================================
    # INPUT 6
    # REFLUX RATIO
    # ========================================================

    reflux_ratio = scale(
        point[5],
        REFLUX_MIN,
        REFLUX_MAX
    )


    # ========================================================
    # INPUT 7
    # BOTTOMS FRACTION
    # ========================================================

    bottoms_fraction = scale(
        point[6],
        BOTTOMS_MIN,
        BOTTOMS_MAX
    )


    # ========================================================
    # PRINT INPUTS
    # ========================================================

    print(
        f"Pressure          : "
        f"{pressure_atm:.8f} atm"
    )

    print(
        f"Requested VF      : "
        f"{requested_vf:.8f}"
    )

    print(
        f"Benzene feed      : "
        f"{benzene_fraction:.8f}"
    )

    print(
        f"Toluene feed      : "
        f"{toluene_fraction:.8f}"
    )

    print(
        f"Stages            : "
        f"{stages}"
    )

    print(
        f"Feed stage        : "
        f"{feed_stage}"
    )

    print(
        f"Feed-stage frac.  : "
        f"{actual_feed_stage_fraction:.8f}"
    )

    print(
        f"Reflux ratio      : "
        f"{reflux_ratio:.8f}"
    )

    print(
        f"Bottoms fraction  : "
        f"{bottoms_fraction:.8f}"
    )


    # ========================================================
    # DEFAULT OUTPUTS
    # ========================================================

    feed_temperature_C = float("nan")

    x_D = float("nan")

    x_B = float("nan")

    Q_C = float("nan")

    Q_R = float("nan")

    dwsim_solved = False

    column_calculated = False

    column_error = ""

    output_values_valid = False

    composition_valid = False

    temperature_valid = False

    case_valid = False

    error_message = ""


    # ========================================================
    # RUN DWSIM
    # ========================================================

    try:

        # ====================================================
        # AUTOMATION
        # ====================================================

        interf = Automation3()


        # ====================================================
        # CREATE EMPTY FLOWSHEET
        # ====================================================

        sim = interf.CreateFlowsheet()


        # ====================================================
        # ADD BENZENE
        # ====================================================

        benzene = (
            sim.AvailableCompounds[
                "Benzene"
            ]
        )


        # ====================================================
        # ADD TOLUENE
        # ====================================================

        toluene = (
            sim.AvailableCompounds[
                "Toluene"
            ]
        )


        sim.SelectedCompounds.Add(
            benzene.Name,
            benzene
        )

        sim.SelectedCompounds.Add(
            toluene.Name,
            toluene
        )


        # ====================================================
        # PROPERTY PACKAGE
        # ====================================================

        pp = (
            sim.CreateAndAddPropertyPackage(
                "Peng-Robinson (PR)"
            )
        )


        # ====================================================
        # CREATE FEED
        # ====================================================

        feed_obj = sim.AddObject(
            ObjectType.MaterialStream,
            100,
            250,
            "Feed"
        )


        # ====================================================
        # CREATE DISTILLATE
        # ====================================================

        distillate_obj = sim.AddObject(
            ObjectType.MaterialStream,
            500,
            100,
            "Distillate"
        )


        # ====================================================
        # CREATE BOTTOMS
        # ====================================================

        bottoms_obj = sim.AddObject(
            ObjectType.MaterialStream,
            500,
            400,
            "Bottoms"
        )


        # ====================================================
        # CREATE COLUMN
        # ====================================================

        column_obj = sim.AddObject(
            ObjectType.DistillationColumn,
            300,
            250,
            "DC1"
        )


        # ====================================================
        # CREATE CONDENSER DUTY
        # ====================================================

        condenser_obj = sim.AddObject(
            ObjectType.EnergyStream,
            500,
            50,
            "CondenserDuty"
        )


        # ====================================================
        # CREATE REBOILER DUTY
        # ====================================================

        reboiler_obj = sim.AddObject(
            ObjectType.EnergyStream,
            500,
            500,
            "ReboilerDuty"
        )


        # ====================================================
        # GET REAL OBJECTS
        # ====================================================

        feed = feed_obj.GetAsObject()

        distillate = (
            distillate_obj.GetAsObject()
        )

        bottoms = (
            bottoms_obj.GetAsObject()
        )

        column = (
            column_obj.GetAsObject()
        )

        condenser = (
            condenser_obj.GetAsObject()
        )

        reboiler = (
            reboiler_obj.GetAsObject()
        )


        # ====================================================
        # PROPERTY PACKAGE ASSIGNMENT
        # ====================================================

        feed.PropertyPackage = pp

        column.PropertyPackage = pp


        # ====================================================
        # PRESSURE
        # ====================================================

        pressure_pa = (
                pressure_atm *
                ATM_TO_PA
        )


        feed.SetPressure(
            float(pressure_pa)
        )


        # ====================================================
        # FEED FLOW
        # ====================================================

        feed_mol_s = (
                FEED_FLOW_KMOL_H
                *
                1000.0
                /
                3600.0
        )


        feed.SetMolarFlow(
            float(feed_mol_s)
        )


        # ====================================================
        # FEED COMPOSITION
        # ====================================================

        feed.SetOverallMolarComposition(
            [
                float(benzene_fraction),
                float(toluene_fraction)
            ]
        )


        # ====================================================
        # FLASH SPECIFICATION
        # ====================================================

        print()

        print(
            "Flash specification: ",
            end=""
        )


        flash_result = (
            feed.SetFlashSpec(
                "PVF"
            )
        )


        print(
            flash_result
        )


        # ====================================================
        # VAPOR FRACTION
        # ====================================================

        try:

            feed.SetPropertyValue(
                "Vapor Fraction",
                float(requested_vf),
                None
            )

        except:

            feed.SetPropertyValue(
                "PROP_MS_4",
                float(requested_vf),
                None
            )


        print(
            "Vapor fraction specification set."
        )


        # ====================================================
        # COLUMN STAGES
        # ====================================================

        column.SetNumberOfStages(
            stages
        )


        # ====================================================
        # CONNECT FEED
        # ====================================================

        column.ConnectFeed(
            feed,
            feed_stage
        )


        # ====================================================
        # CONNECT DISTILLATE
        # ====================================================

        column.ConnectDistillate(
            distillate
        )


        # ====================================================
        # CONNECT BOTTOMS
        # ====================================================

        column.ConnectBottoms(
            bottoms
        )


        # ====================================================
        # CONNECT CONDENSER DUTY
        # ====================================================

        column.ConnectCondenserDuty(
            condenser
        )


        # ====================================================
        # CONNECT REBOILER DUTY
        # ====================================================

        column.ConnectReboilerDuty(
            reboiler
        )


        # ====================================================
        # COLUMN PRESSURE
        # ====================================================

        column.SetTopPressure(
            float(pressure_pa)
        )


        # ====================================================
        # INITIALIZE STAGE PRESSURES
        # ====================================================

        try:

            for stage in column.Stages:

                stage.P = float(
                    pressure_pa
                )

        except:

            pass


        # ====================================================
        # CONDENSER SPECIFICATION
        # ====================================================

        column.SetCondenserSpec(
            "Reflux Ratio",
            float(reflux_ratio),
            ""
        )


        # ====================================================
        # BOTTOMS FLOW
        # ====================================================

        bottoms_flow = (
                FEED_FLOW_KMOL_H
                *
                bottoms_fraction
        )


        column.SetReboilerSpec(
            "Product Molar Flow Rate",
            float(bottoms_flow),
            "kmol/h"
        )


        # ====================================================
        # RUN DWSIM
        # ====================================================

        print()

        print(
            "Running DWSIM..."
        )


        interf.CalculateFlowsheet4(
            sim
        )


        # ====================================================
        # SOLUTION STATUS
        # ====================================================

        dwsim_solved = bool(
            sim.Solved
        )


        column_calculated = bool(
            column.Calculated
        )


        print()

        print(
            "Solved:",
            dwsim_solved
        )

        print(
            "Column calculated:",
            column_calculated
        )


        # ====================================================
        # COLUMN ERROR
        # ====================================================

        try:

            column_error = str(
                column.ErrorMessage
            )

        except:

            column_error = ""


        # ====================================================
        # FEED TEMPERATURE
        # ====================================================

        try:

            temperature_K = float(
                feed.GetTemperature()
            )


            feed_temperature_C = (
                    temperature_K -
                    273.15
            )

        except Exception as e:

            print()

            print(
                "Temperature read error:",
                e
            )

            feed_temperature_C = (
                float("nan")
            )


        print()

        print(
            f"Derived feed temperature : "
            f"{feed_temperature_C:.8f} °C"
        )


        # ====================================================
        # DISTILLATE COMPOSITION
        # ====================================================

        try:

            distillate_composition = (
                distillate.GetOverallComposition()
            )


            x_D = float(
                distillate_composition[0]
            )

        except Exception as e:

            print()

            print(
                "Distillate composition "
                "read error:"
            )

            print(e)

            x_D = float("nan")


        # ====================================================
        # BOTTOMS COMPOSITION
        # ====================================================

        try:

            bottoms_composition = (
                bottoms.GetOverallComposition()
            )


            x_B = float(
                bottoms_composition[0]
            )

        except Exception as e:

            print()

            print(
                "Bottoms composition "
                "read error:"
            )

            print(e)

            x_B = float("nan")


        # ====================================================
        # CONDENSER DUTY
        # ====================================================

        try:

            Q_C = float(
                condenser.GetEnergyFlow()
            )

        except:

            try:

                Q_C = float(
                    condenser.EnergyFlow
                )

            except:

                Q_C = float("nan")


        # ====================================================
        # REBOILER DUTY
        # ====================================================

        try:

            Q_R = float(
                reboiler.GetEnergyFlow()
            )

        except:

            try:

                Q_R = float(
                    reboiler.EnergyFlow
                )

            except:

                Q_R = float("nan")


        # ====================================================
        # PRINT OUTPUTS
        # ====================================================

        print()

        if finite(x_D):

            print(
                f"x_D benzene : "
                f"{x_D:.10f}"
            )

        else:

            print(
                "x_D benzene : NaN"
            )


        if finite(x_B):

            print(
                f"x_B benzene : "
                f"{x_B:.10f}"
            )

        else:

            print(
                "x_B benzene : NaN"
            )


        if finite(Q_C):

            print(
                f"Q_C         : "
                f"{Q_C:.10f}"
            )

        else:

            print(
                "Q_C         : NaN"
            )


        if finite(Q_R):

            print(
                f"Q_R         : "
                f"{Q_R:.10f}"
            )

        else:

            print(
                "Q_R         : NaN"
            )


        # ====================================================
        # VALIDATION 1
        # DWSIM CONVERGENCE
        # ====================================================

        if not dwsim_solved:

            raise RuntimeError(
                "DWSIM did not converge."
            )


        # ====================================================
        # VALIDATION 2
        # COLUMN CALCULATION
        # ====================================================

        if not column_calculated:

            raise RuntimeError(
                "Column was not calculated."
            )


        # ====================================================
        # VALIDATION 3
        # FINITE OUTPUTS
        # ====================================================

        output_values_valid = (
                finite(feed_temperature_C)
                and
                finite(x_D)
                and
                finite(x_B)
                and
                finite(Q_C)
                and
                finite(Q_R)
        )


        if not output_values_valid:

            raise RuntimeError(
                "One or more outputs are "
                "NaN or infinite."
            )


        # ====================================================
        # VALIDATION 4
        # COMPOSITION
        # ====================================================

        composition_valid = (
                0.0 <= x_D <= 1.0
                and
                0.0 <= x_B <= 1.0
        )


        if not composition_valid:

            raise RuntimeError(
                "Product composition is "
                "outside [0,1]."
            )


        # ====================================================
        # VALIDATION 5
        # TEMPERATURE
        # ====================================================

        temperature_valid = (
                -100.0
                <
                feed_temperature_C
                <
                500.0
        )


        if not temperature_valid:

            raise RuntimeError(
                "Feed temperature is "
                "outside the broad "
                "numerical validation range."
            )


        # ====================================================
        # CASE VALID
        # ====================================================

        case_valid = True

        successful_cases += 1


        print()

        print(
            "VALID DWSIM RESULT"
        )

        print(
            "All validation checks passed."
        )


    # ========================================================
    # CASE ERROR
    # ========================================================

    except Exception as e:

        failed_cases += 1

        error_message = str(e)

        print()

        print(
            "CASE ERROR:"
        )

        print(
            error_message
        )


    # ========================================================
    # SAVE CASE
    # ========================================================

    results.append({

        "pressure_atm":
            pressure_atm,

        "requested_vapor_fraction":
            requested_vf,

        "benzene_feed_fraction":
            benzene_fraction,

        "toluene_feed_fraction":
            toluene_fraction,

        "stages":
            stages,

        "feed_stage":
            feed_stage,

        "feed_stage_fraction":
            actual_feed_stage_fraction,

        "reflux_ratio":
            reflux_ratio,

        "bottoms_fraction":
            bottoms_fraction,

        "feed_flow_kmol_h":
            FEED_FLOW_KMOL_H,

        "feed_temperature_C":
            feed_temperature_C,

        "x_D_benzene":
            x_D,

        "x_B_benzene":
            x_B,

        "Q_C":
            Q_C,

        "Q_R":
            Q_R,

        "dwsim_solved":
            dwsim_solved,

        "column_calculated":
            column_calculated,

        "column_error":
            column_error,

        "output_values_valid":
            output_values_valid,

        "composition_valid":
            composition_valid,

        "temperature_valid":
            temperature_valid,

        "case_valid":
            case_valid,

        "error_message":
            error_message,
    })


# ============================================================
# WRITE CSV
# ============================================================

print()
print(
    "=" * 75
)

print(
    "WRITING CSV"
)

print(
    "=" * 75
)


with open(
        output_csv,
        "w",
        newline="",
        encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=csv_columns
    )

    writer.writeheader()

    writer.writerows(
        results
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print()
print("=" * 75)
print("256-CASE TEST COMPLETE")
print("=" * 75)

print(
    f"Requested cases : {N}"
)

print(
    f"Valid cases     : "
    f"{successful_cases}"
)

print(
    f"Failed cases    : "
    f"{failed_cases}"
)

print(
    f"DWSIM completed cases: "
    f"{successful_cases} / {N}"
)

print()

print(
    "CSV generated:"
)

print(
    output_csv
)

print()
print("=" * 75)
print("DONE")
print("=" * 75)