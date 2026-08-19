import os
import csv
import math
import pythoncom
import clr

from scipy.stats import qmc


# ============================================================
# INITIALIZE COM
# ============================================================

pythoncom.CoInitialize()


# ============================================================
# DWSIM PATH
# ============================================================

DWSIM_PATH = r"C:\Users\Rupali Waghmare\AppData\Local\DWSIM"


# ============================================================
# LOAD DWSIM DLLs
# ============================================================

DLLS = [
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


for dll in DLLS:

    path = os.path.join(
        DWSIM_PATH,
        dll
    )

    print("Loading:", path)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"DWSIM DLL not found:\n{path}"
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
#
# IMPORTANT:
# Script is assumed to be inside:
#
# DWSIM_Task3_Surrogate_Model/
#     sampling/
#
# Therefore ".." gives the project root.
# ============================================================

SCRIPT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        SCRIPT_DIR,
        ".."
    )
)


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR = os.path.join(
    PROJECT_ROOT,
    "data",
    "01_validation_runs"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# OUTPUT FILES
# ============================================================

CONVERGED_CSV = os.path.join(
    OUTPUT_DIR,
    "dataset_2560_converged.csv"
)

NOT_CONVERGED_CSV = os.path.join(
    OUTPUT_DIR,
    "dataset_2560_not_converged.csv"
)


# ============================================================
# SAMPLING SETTINGS
# ============================================================

FIRST_BATCH = 2048

SECOND_BATCH = 512

TOTAL_POINTS = (
        FIRST_BATCH +
        SECOND_BATCH
)

SEED = 42


# ============================================================
# FEED
# ============================================================

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
# CSV COLUMNS
# ============================================================

CSV_COLUMNS = [

    "sobol_index",
    "batch",

    "pressure_atm",
    "requested_vapor_fraction",

    "benzene_feed_fraction",
    "toluene_feed_fraction",

    "stages",

    "feed_stage",
    "feed_stage_fraction",

    "reflux_ratio",
    "bottoms_fraction",

    "feed_flow_kmol_h",

    "feed_temperature_C",

    "x_D_benzene",
    "x_B_benzene",

    "Q_C",
    "Q_R",

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
# HELPER
# ============================================================

def scale(
        value,
        minimum,
        maximum
):

    return (
            minimum
            +
            value *
            (
                    maximum -
                    minimum
            )
    )


def is_finite(value):

    try:

        return math.isfinite(
            float(value)
        )

    except:

        return False


# ============================================================
# SOBOL GENERATION
# ============================================================

print()
print("=" * 75)
print("GENERATING SOBOL DESIGN")
print("=" * 75)

print(
    f"First batch  : {FIRST_BATCH}"
)

print(
    f"Second batch : {SECOND_BATCH}"
)

print(
    f"Total points : {TOTAL_POINTS}"
)

print(
    f"Seed         : {SEED}"
)

print(
    "Sobol dimension: 7"
)

print()


# ------------------------------------------------------------
# IMPORTANT
#
# Generate 4096 = 2^12 points.
#
# Then take:
#
#   0:2048   -> first 2048
#   2048:2560 -> next 512
#
# This keeps both batches part of ONE continuous Sobol
# sequence.
# ------------------------------------------------------------

sampler = qmc.Sobol(
    d=7,
    scramble=True,
    seed=SEED
)


sobol_all = sampler.random_base2(
    m=12
)


sobol_points = sobol_all[
    :TOTAL_POINTS
]


print(
    "Sobol points generated."
)

print(
    f"Using first {TOTAL_POINTS} points "
    f"from 4096-point Sobol sequence."
)


# ============================================================
# CSV FILES
# ============================================================

converged_file = open(
    CONVERGED_CSV,
    "w",
    newline="",
    encoding="utf-8"
)

not_converged_file = open(
    NOT_CONVERGED_CSV,
    "w",
    newline="",
    encoding="utf-8"
)


converged_writer = csv.DictWriter(
    converged_file,
    fieldnames=CSV_COLUMNS
)

not_converged_writer = csv.DictWriter(
    not_converged_file,
    fieldnames=CSV_COLUMNS
)


converged_writer.writeheader()

not_converged_writer.writeheader()


# ============================================================
# COUNTERS
# ============================================================

converged_count = 0

not_converged_count = 0


# ============================================================
# MAIN LOOP
# ============================================================

for index in range(TOTAL_POINTS):

    point = sobol_points[index]


    # ========================================================
    # BATCH
    # ========================================================

    if index < FIRST_BATCH:

        batch = "2048"

    else:

        batch = "512"


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
    # BENZENE
    # ========================================================

    benzene_fraction = scale(
        point[2],
        BENZENE_MIN,
        BENZENE_MAX
    )


    # ========================================================
    # DERIVED TOLUENE
    # ========================================================

    toluene_fraction = (
            1.0 -
            benzene_fraction
    )


    # ========================================================
    # INPUT 4
    # STAGES
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
    # FEED STAGE FRACTION
    # ========================================================

    feed_stage_fraction = scale(
        point[4],
        FEED_STAGE_MIN,
        FEED_STAGE_MAX
    )


    # ========================================================
    # ACTUAL FEED STAGE
    # ========================================================

    feed_stage = int(
        round(
            stages *
            feed_stage_fraction
        )
    )


    feed_stage = max(
        1,
        min(
            stages - 1,
            feed_stage
        )
    )


    actual_feed_stage_fraction = (
            feed_stage /
            stages
    )


    # ========================================================
    # INPUT 6
    # REFLUX
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
    # PRINT CASE
    # ========================================================

    print()
    print("=" * 75)

    print(
        f"CASE {index + 1}/{TOTAL_POINTS}"
    )

    print(
        f"Batch             : {batch}"
    )

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

        # ----------------------------------------------------
        # AUTOMATION
        # ----------------------------------------------------

        interf = Automation3()


        # ----------------------------------------------------
        # FLOWSHEET
        # ----------------------------------------------------

        sim = interf.CreateFlowsheet()


        # ----------------------------------------------------
        # COMPOUNDS
        # ----------------------------------------------------

        benzene = (
            sim.AvailableCompounds[
                "Benzene"
            ]
        )

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


        # ----------------------------------------------------
        # PROPERTY PACKAGE
        # ----------------------------------------------------

        pp = (
            sim.CreateAndAddPropertyPackage(
                "Peng-Robinson (PR)"
            )
        )


        # ----------------------------------------------------
        # OBJECTS
        # ----------------------------------------------------

        feed_obj = sim.AddObject(
            ObjectType.MaterialStream,
            100,
            250,
            "Feed"
        )


        distillate_obj = sim.AddObject(
            ObjectType.MaterialStream,
            500,
            100,
            "Distillate"
        )


        bottoms_obj = sim.AddObject(
            ObjectType.MaterialStream,
            500,
            400,
            "Bottoms"
        )


        column_obj = sim.AddObject(
            ObjectType.DistillationColumn,
            300,
            250,
            "DC1"
        )


        condenser_obj = sim.AddObject(
            ObjectType.EnergyStream,
            500,
            50,
            "CondenserDuty"
        )


        reboiler_obj = sim.AddObject(
            ObjectType.EnergyStream,
            500,
            500,
            "ReboilerDuty"
        )


        # ----------------------------------------------------
        # OBJECT REFERENCES
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # PROPERTY PACKAGE
        # ----------------------------------------------------

        feed.PropertyPackage = pp

        column.PropertyPackage = pp


        # ----------------------------------------------------
        # PRESSURE
        # ----------------------------------------------------

        pressure_pa = (
                pressure_atm *
                ATM_TO_PA
        )


        feed.SetPressure(
            float(pressure_pa)
        )


        # ----------------------------------------------------
        # FEED FLOW
        # ----------------------------------------------------

        feed_mol_s = (
                FEED_FLOW_KMOL_H *
                1000.0 /
                3600.0
        )


        feed.SetMolarFlow(
            float(feed_mol_s)
        )


        # ----------------------------------------------------
        # FEED COMPOSITION
        # ----------------------------------------------------

        feed.SetOverallMolarComposition(
            [
                float(benzene_fraction),
                float(toluene_fraction)
            ]
        )


        # ----------------------------------------------------
        # FLASH SPECIFICATION
        # ----------------------------------------------------

        print()

        print(
            "Flash specification: ",
            end=""
        )


        flash_result = feed.SetFlashSpec(
            "PVF"
        )


        print(
            flash_result
        )


        # ----------------------------------------------------
        # VAPOR FRACTION
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # COLUMN STAGES
        # ----------------------------------------------------

        column.SetNumberOfStages(
            stages
        )


        # ----------------------------------------------------
        # CONNECT FEED
        # ----------------------------------------------------

        column.ConnectFeed(
            feed,
            feed_stage
        )


        # ----------------------------------------------------
        # CONNECT DISTILLATE
        # ----------------------------------------------------

        column.ConnectDistillate(
            distillate
        )


        # ----------------------------------------------------
        # CONNECT BOTTOMS
        # ----------------------------------------------------

        column.ConnectBottoms(
            bottoms
        )


        # ----------------------------------------------------
        # CONNECT DUTIES
        # ----------------------------------------------------

        column.ConnectCondenserDuty(
            condenser
        )

        column.ConnectReboilerDuty(
            reboiler
        )


        # ----------------------------------------------------
        # COLUMN PRESSURE
        # ----------------------------------------------------

        column.SetTopPressure(
            float(pressure_pa)
        )


        # ----------------------------------------------------
        # INITIALIZE ALL STAGE PRESSURES
        # ----------------------------------------------------

        try:

            for stage in column.Stages:

                stage.P = float(
                    pressure_pa
                )

        except:

            pass


        # ----------------------------------------------------
        # CONDENSER SPECIFICATION
        # ----------------------------------------------------

        column.SetCondenserSpec(
            "Reflux Ratio",
            float(reflux_ratio),
            ""
        )


        # ----------------------------------------------------
        # BOTTOMS FLOW
        # ----------------------------------------------------

        bottoms_flow = (
                FEED_FLOW_KMOL_H *
                bottoms_fraction
        )


        column.SetReboilerSpec(
            "Product Molar Flow Rate",
            float(bottoms_flow),
            "kmol/h"
        )


        # ----------------------------------------------------
        # RUN DWSIM
        # ----------------------------------------------------

        print()

        print(
            "Running DWSIM..."
        )


        interf.CalculateFlowsheet4(
            sim
        )


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # COLUMN ERROR
        # ----------------------------------------------------

        try:

            column_error = str(
                column.ErrorMessage
            )

        except:

            column_error = ""


        # ----------------------------------------------------
        # FEED TEMPERATURE
        #
        # IMPORTANT:
        # Temperature is DERIVED by DWSIM.
        # It is NOT a Sobol input.
        # ----------------------------------------------------

        try:

            temperature_K = float(
                feed.GetTemperature()
            )

            feed_temperature_C = (
                    temperature_K -
                    273.15
            )

        except Exception as e:

            raise RuntimeError(
                "Could not obtain derived "
                f"feed temperature: {e}"
            )


        print()

        print(
            f"Derived feed temperature : "
            f"{feed_temperature_C:.8f} °C"
        )


        # ----------------------------------------------------
        # DISTILLATE COMPOSITION
        # ----------------------------------------------------

        try:

            distillate_composition = (
                distillate.GetOverallComposition()
            )

            x_D = float(
                distillate_composition[0]
            )

        except Exception as e:

            raise RuntimeError(
                "Could not obtain "
                f"x_D: {e}"
            )


        # ----------------------------------------------------
        # BOTTOMS COMPOSITION
        # ----------------------------------------------------

        try:

            bottoms_composition = (
                bottoms.GetOverallComposition()
            )

            x_B = float(
                bottoms_composition[0]
            )

        except Exception as e:

            raise RuntimeError(
                "Could not obtain "
                f"x_B: {e}"
            )


        # ----------------------------------------------------
        # CONDENSER DUTY
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # REBOILER DUTY
        # ----------------------------------------------------

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
        # VALIDATION 1
        # ====================================================

        if not dwsim_solved:

            raise RuntimeError(
                "DWSIM did not converge."
            )


        # ====================================================
        # VALIDATION 2
        # ====================================================

        if not column_calculated:

            raise RuntimeError(
                "Column was not calculated."
            )


        # ====================================================
        # VALIDATION 3
        # ====================================================

        output_values_valid = (

                is_finite(
                    feed_temperature_C
                )

                and

                is_finite(x_D)

                and

                is_finite(x_B)

                and

                is_finite(Q_C)

                and

                is_finite(Q_R)
        )


        if not output_values_valid:

            raise RuntimeError(
                "One or more outputs are "
                "NaN or infinite."
            )


        # ====================================================
        # VALIDATION 4
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
                "Derived feed temperature "
                "is outside the broad "
                "validity range."
            )


        # ====================================================
        # EVERYTHING VALID
        # ====================================================

        case_valid = True

        converged_count += 1


        print()

        print(
            f"x_D benzene : {x_D:.10f}"
        )

        print(
            f"x_B benzene : {x_B:.10f}"
        )

        print(
            f"Q_C         : {Q_C:.10f}"
        )

        print(
            f"Q_R         : {Q_R:.10f}"
        )

        print()

        print(
            "VALID DWSIM RESULT"
        )

        print(
            "All validation checks passed."
        )


    # ========================================================
    # FAILURE
    # ========================================================

    except Exception as e:

        error_message = str(e)

        not_converged_count += 1

        print()

        print(
            "CASE ERROR:"
        )

        print(
            error_message
        )


    # ========================================================
    # RESULT ROW
    # ========================================================

    row = {

        "sobol_index":
            index + 1,

        "batch":
            batch,

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
    }


    # ========================================================
    # WRITE IMMEDIATELY
    #
    # This is important:
    # Every case is written immediately.
    # ========================================================

    if case_valid:

        converged_writer.writerow(
            row
        )

        converged_file.flush()

    else:

        not_converged_writer.writerow(
            row
        )

        not_converged_file.flush()


    # ========================================================
    # PROGRESS
    # ========================================================

    if (
            (index + 1) % 50 == 0
            or
            index + 1 == TOTAL_POINTS
    ):

        print()
        print(
            "-" * 75
        )

        print(
            f"PROGRESS: "
            f"{index + 1}/{TOTAL_POINTS}"
        )

        print(
            f"Converged     : "
            f"{converged_count}"
        )

        print(
            f"Not converged : "
            f"{not_converged_count}"
        )

        print(
            "-" * 75
        )


# ============================================================
# CLOSE CSV FILES
# ============================================================

converged_file.close()

not_converged_file.close()


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print()
print("=" * 75)
print("SOBOL + DWSIM GENERATION COMPLETE")
print("=" * 75)

print()

print(
    f"Total Sobol points : "
    f"{TOTAL_POINTS}"
)

print(
    f"First batch        : "
    f"{FIRST_BATCH}"
)

print(
    f"Additional batch   : "
    f"{SECOND_BATCH}"
)

print()

print(
    f"Converged          : "
    f"{converged_count}"
)

print(
    f"Not converged      : "
    f"{not_converged_count}"
)

print()

print(
    "CONVERGED CSV:"
)

print(
    CONVERGED_CSV
)

print()

print(
    "NOT-CONVERGED CSV:"
)

print(
    NOT_CONVERGED_CSV
)

print()

print("=" * 75)
print("DONE")
print("=" * 75)