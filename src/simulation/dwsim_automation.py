import os
import csv
import random
import pythoncom
import clr

pythoncom.CoInitialize()


# ============================================================
# DWSIM INSTALLATION
# ============================================================

dwsimpath = r"C:\Users\Rupali Waghmare\AppData\Local\DWSIM"


# ============================================================
# PROJECT PATH
# ============================================================

project_root = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

data_dir = os.path.join(
    project_root,
    "data"
)

os.makedirs(
    data_dir,
    exist_ok=True
)

csv_path = os.path.join(
    data_dir,
    "dwsim_10_samples.csv"
)


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

    if not os.path.exists(path):

        raise FileNotFoundError(
            f"DLL not found:\n{path}"
        )

    print("Loading:", path)

    clr.AddReference(path)


print("\nDWSIM DLLs loaded successfully.")


# ============================================================
# IMPORT DWSIM
# ============================================================

from DWSIM.Automation import Automation3
from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType


# ============================================================
# RANDOM SEED
# ============================================================

random.seed(42)


# ============================================================
# DATASET SETTINGS
# ============================================================

TARGET_ROWS = 10

MAX_ATTEMPTS = 50


# ============================================================
# INPUT RANGES
# ============================================================

PRESSURE_MIN = 1.0
PRESSURE_MAX = 3.0

VAPOR_FRACTION_MIN = 0.10
VAPOR_FRACTION_MAX = 0.30

BENZENE_MIN = 0.30
BENZENE_MAX = 0.70

STAGES_MIN = 15
STAGES_MAX = 25

FEED_STAGE_FRACTION_MIN = 0.40
FEED_STAGE_FRACTION_MAX = 0.60

REFLUX_MIN = 1.5
REFLUX_MAX = 4.0

BOTTOMS_FRACTION_MIN = 0.40
BOTTOMS_FRACTION_MAX = 0.60

FEED_FLOW_MIN = 80.0
FEED_FLOW_MAX = 120.0


# ============================================================
# AUTOMATION MANAGER
# ============================================================

interf = Automation3()


# ============================================================
# RESULT STORAGE
# ============================================================

results = []


# ============================================================
# CREATE ONE DWSIM SIMULATION
# ============================================================

def create_simulation():

    # --------------------------------------------------------
    # Create flowsheet
    # --------------------------------------------------------

    sim = interf.CreateFlowsheet()


    # --------------------------------------------------------
    # Compounds
    # --------------------------------------------------------

    benzene = sim.AvailableCompounds["Benzene"]

    toluene = sim.AvailableCompounds["Toluene"]


    sim.SelectedCompounds.Add(
        benzene.Name,
        benzene
    )

    sim.SelectedCompounds.Add(
        toluene.Name,
        toluene
    )


    # --------------------------------------------------------
    # Property package
    # --------------------------------------------------------

    pp = sim.CreateAndAddPropertyPackage(
        "Peng-Robinson (PR)"
    )


    # --------------------------------------------------------
    # Material streams
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Column
    # --------------------------------------------------------

    column_obj = sim.AddObject(
        ObjectType.DistillationColumn,
        300,
        250,
        "DC1"
    )


    # --------------------------------------------------------
    # Energy streams
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Get actual objects
    # --------------------------------------------------------

    feed = feed_obj.GetAsObject()

    distillate = distillate_obj.GetAsObject()

    bottoms = bottoms_obj.GetAsObject()

    column = column_obj.GetAsObject()

    condenser = condenser_obj.GetAsObject()

    reboiler = reboiler_obj.GetAsObject()


    # --------------------------------------------------------
    # Property package
    # --------------------------------------------------------

    column.PropertyPackage = pp


    return (
        sim,
        feed,
        distillate,
        bottoms,
        column,
        condenser,
        reboiler
    )


# ============================================================
# GENERATE ONE RANDOM CASE
# ============================================================

def generate_inputs():

    feed_pressure = random.uniform(
        PRESSURE_MIN,
        PRESSURE_MAX
    )

    feed_vapor_fraction = random.uniform(
        VAPOR_FRACTION_MIN,
        VAPOR_FRACTION_MAX
    )

    benzene_fraction = random.uniform(
        BENZENE_MIN,
        BENZENE_MAX
    )

    toluene_fraction = (
            1.0 - benzene_fraction
    )

    number_of_stages = random.randint(
        STAGES_MIN,
        STAGES_MAX
    )

    feed_stage_fraction = random.uniform(
        FEED_STAGE_FRACTION_MIN,
        FEED_STAGE_FRACTION_MAX
    )

    reflux_ratio = random.uniform(
        REFLUX_MIN,
        REFLUX_MAX
    )

    bottoms_fraction = random.uniform(
        BOTTOMS_FRACTION_MIN,
        BOTTOMS_FRACTION_MAX
    )

    feed_flow = random.uniform(
        FEED_FLOW_MIN,
        FEED_FLOW_MAX
    )


    # --------------------------------------------------------
    # Calculate feed stage
    # --------------------------------------------------------

    feed_stage = round(
        feed_stage_fraction *
        number_of_stages
    )

    feed_stage = max(
        1,
        min(
            feed_stage,
            number_of_stages - 1
        )
    )


    return {
        "pressure_atm": feed_pressure,
        "vapor_fraction": feed_vapor_fraction,
        "benzene_feed": benzene_fraction,
        "toluene_feed": toluene_fraction,
        "stages": number_of_stages,
        "feed_stage": feed_stage,
        "feed_stage_fraction": feed_stage_fraction,
        "reflux_ratio": reflux_ratio,
        "bottoms_fraction": bottoms_fraction,
        "feed_flow": feed_flow
    }


# ============================================================
# RUN ONE SIMULATION
# ============================================================

def run_simulation(inputs):

    # --------------------------------------------------------
    # Create new simulation
    # --------------------------------------------------------

    (
        sim,
        feed,
        distillate,
        bottoms,
        column,
        condenser,
        reboiler
    ) = create_simulation()


    # --------------------------------------------------------
    # Extract inputs
    # --------------------------------------------------------

    pressure_atm = inputs["pressure_atm"]

    vapor_fraction = inputs["vapor_fraction"]

    benzene_feed = inputs["benzene_feed"]

    toluene_feed = inputs["toluene_feed"]

    stages = inputs["stages"]

    feed_stage = inputs["feed_stage"]

    reflux_ratio = inputs["reflux_ratio"]

    bottoms_fraction = inputs["bottoms_fraction"]

    feed_flow = inputs["feed_flow"]


    # ========================================================
    # FEED
    # ========================================================

    feed.SetPressure(
        f"{pressure_atm} atm"
    )

    feed.SetMolarFlow(
        f"{feed_flow} kmol/h"
    )

    feed.SetOverallMolarComposition(
        [
            benzene_feed,
            toluene_feed
        ]
    )

    # Pressure + Vapor Fraction flash
    feed.SetFlashSpec(
        "PVF"
    )


    # ========================================================
    # COLUMN STAGES
    # ========================================================

    column.SetNumberOfStages(
        stages
    )


    # ========================================================
    # CONNECT STREAMS
    # ========================================================

    column.ConnectFeed(
        feed,
        feed_stage
    )

    column.ConnectDistillate(
        distillate
    )

    column.ConnectBottoms(
        bottoms
    )

    column.ConnectCondenserDuty(
        condenser
    )

    column.ConnectReboilerDuty(
        reboiler
    )


    # ========================================================
    # COLUMN PRESSURE
    # ========================================================

    ATM_TO_PA = 101325.0

    column_pressure_pa = (
            pressure_atm *
            ATM_TO_PA
    )

    column.SetTopPressure(
        float(column_pressure_pa)
    )


    # Initialize all stage pressures

    for stage in column.Stages:

        stage.P = float(
            column_pressure_pa
        )


    # ========================================================
    # CONDENSER SPECIFICATION
    # ========================================================

    column.SetCondenserSpec(
        "Reflux Ratio",
        float(reflux_ratio),
        ""
    )


    # ========================================================
    # REBOILER SPECIFICATION
    # ========================================================

    bottoms_flow = (
            feed_flow *
            bottoms_fraction
    )

    column.SetReboilerSpec(
        "Product Molar Flow Rate",
        float(bottoms_flow),
        "kmol/h"
    )


    # ========================================================
    # RUN DWSIM
    # ========================================================

    errors = interf.CalculateFlowsheet4(
        sim
    )


    # ========================================================
    # CHECK CONVERGENCE
    # ========================================================

    if not sim.Solved:

        print(
            "   ❌ Simulation did not converge."
        )

        return None


    # ========================================================
    # EXTRACT OUTPUTS
    # ========================================================

    try:

        x_D = float(
            distillate.GetOverallComposition()[0]
        )

        x_B = float(
            bottoms.GetOverallComposition()[0]
        )

        Q_C = float(
            column.CondenserDuty
        )

        Q_R = float(
            column.ReboilerDuty
        )

    except Exception as e:

        print(
            "   ❌ Could not extract outputs:",
            e
        )

        return None


    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "pressure_atm":
            pressure_atm,

        "vapor_fraction":
            vapor_fraction,

        "benzene_feed":
            benzene_feed,

        "toluene_feed":
            toluene_feed,

        "stages":
            stages,

        "feed_stage":
            feed_stage,

        "feed_stage_fraction":
            inputs["feed_stage_fraction"],

        "reflux_ratio":
            reflux_ratio,

        "bottoms_fraction":
            bottoms_fraction,

        "feed_flow":
            feed_flow,

        "x_D":
            x_D,

        "x_B":
            x_B,

        "Q_C":
            Q_C,

        "Q_R":
            Q_R
    }


# ============================================================
# GENERATE DATA
# ============================================================

print("\n")
print("=" * 80)
print("DWSIM DATA GENERATION")
print("=" * 80)

print(
    "Target valid rows:",
    TARGET_ROWS
)

print(
    "Maximum attempts:",
    MAX_ATTEMPTS
)


attempt = 0


while (
        len(results) < TARGET_ROWS
        and
        attempt < MAX_ATTEMPTS
):

    attempt += 1

    print("\n")
    print("-" * 80)

    print(
        f"ATTEMPT {attempt}"
    )

    print(
        f"VALID ROWS: {len(results)}/{TARGET_ROWS}"
    )


    # --------------------------------------------------------
    # Generate random inputs
    # --------------------------------------------------------

    inputs = generate_inputs()


    print(
        "\nInputs:"
    )

    print(
        "Pressure       :",
        round(
            inputs["pressure_atm"],
            4
        ),
        "atm"
    )

    print(
        "Vapor fraction :",
        round(
            inputs["vapor_fraction"],
            4
        )
    )

    print(
        "Benzene feed   :",
        round(
            inputs["benzene_feed"],
            4
        )
    )

    print(
        "Stages         :",
        inputs["stages"]
    )

    print(
        "Feed stage     :",
        inputs["feed_stage"]
    )

    print(
        "Reflux ratio   :",
        round(
            inputs["reflux_ratio"],
            4
        )
    )

    print(
        "Bottoms frac.  :",
        round(
            inputs["bottoms_fraction"],
            4
        )
    )

    print(
        "Feed flow      :",
        round(
            inputs["feed_flow"],
            4
        ),
        "kmol/h"
    )


    # --------------------------------------------------------
    # Run simulation
    # --------------------------------------------------------

    try:

        result = run_simulation(
            inputs
        )

    except Exception as e:

        print(
            "\n❌ Simulation error:"
        )

        print(
            e
        )

        result = None


    # --------------------------------------------------------
    # Store successful result
    # --------------------------------------------------------

    if result is not None:

        results.append(
            result
        )

        print(
            "\n✅ VALID RESULT"
        )

        print(
            "x_D:",
            result["x_D"]
        )

        print(
            "x_B:",
            result["x_B"]
        )

        print(
            "Q_C:",
            result["Q_C"]
        )

        print(
            "Q_R:",
            result["Q_R"]
        )


# ============================================================
# CHECK GENERATION
# ============================================================

print("\n")
print("=" * 80)
print("GENERATION COMPLETE")
print("=" * 80)

print(
    "Valid rows generated:",
    len(results)
)

print(
    "Attempts used:",
    attempt
)


if len(results) < TARGET_ROWS:

    raise RuntimeError(
        f"Only {len(results)} valid rows were generated "
        f"after {MAX_ATTEMPTS} attempts."
    )


# ============================================================
# SAVE CSV
# ============================================================

fieldnames = [
    "pressure_atm",
    "vapor_fraction",
    "benzene_feed",
    "toluene_feed",
    "stages",
    "feed_stage",
    "feed_stage_fraction",
    "reflux_ratio",
    "bottoms_fraction",
    "feed_flow",
    "x_D",
    "x_B",
    "Q_C",
    "Q_R"
]


with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(
        results
    )


# ============================================================
# PRINT DATASET
# ============================================================

print("\n")
print("=" * 80)
print("10 SAMPLE DATASET")
print("=" * 80)

for i, row in enumerate(
        results,
        start=1
):

    print(
        f"\nRow {i}:"
    )

    print(
        "  P       =",
        round(
            row["pressure_atm"],
            4
        ),
        "atm"
    )

    print(
        "  VF      =",
        round(
            row["vapor_fraction"],
            4
        )
    )

    print(
        "  xB_feed =",
        round(
            row["benzene_feed"],
            4
        )
    )

    print(
        "  stages  =",
        row["stages"]
    )

    print(
        "  feed    =",
        row["feed_stage"]
    )

    print(
        "  reflux  =",
        round(
            row["reflux_ratio"],
            4
        )
    )

    print(
        "  x_D     =",
        round(
            row["x_D"],
            6
        )
    )

    print(
        "  x_B     =",
        round(
            row["x_B"],
            6
        )
    )

    print(
        "  Q_C     =",
        round(
            row["Q_C"],
            4
        )
    )

    print(
        "  Q_R     =",
        round(
            row["Q_R"],
            4
        )
    )


# ============================================================
# FINAL
# ============================================================

print("\n")
print("=" * 80)
print("CSV SAVED")
print("=" * 80)

print(
    csv_path
)

print(
    "\nSuccessfully generated exactly",
    len(results),
    "valid DWSIM rows."
)

print("\nDONE.")