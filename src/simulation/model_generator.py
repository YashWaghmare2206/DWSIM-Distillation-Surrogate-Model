import os
import pythoncom
import clr

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

    path = os.path.join(dwsimpath, dll)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"DLL not found:\n{path}"
        )

    print("Loading:", path)

    clr.AddReference(path)

print("\nDWSIM DLLs loaded successfully.")


# ============================================================
# IMPORTS
# ============================================================

from DWSIM.Automation import Automation3
from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType


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

flowsheet_dir = os.path.join(
    project_root,
    "dwsim_flowsheets"
)

os.makedirs(
    flowsheet_dir,
    exist_ok=True
)

output_file = os.path.join(
    flowsheet_dir,
    "binary_distillation.dwxmz"
)

print("\nOutput flowsheet:")
print(output_file)


# ============================================================
# CREATE AUTOMATION MANAGER
# ============================================================

interf = Automation3()


# ============================================================
# CREATE EMPTY FLOWSHEET
# ============================================================

sim = interf.CreateFlowsheet()

print("\nEmpty DWSIM flowsheet created.")


# ============================================================
# ADD BENZENE + TOLUENE
# ============================================================

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

print("Benzene and Toluene added.")


# ============================================================
# CREATE PENG-ROBINSON PROPERTY PACKAGE
# ============================================================

pp = sim.CreateAndAddPropertyPackage(
    "Peng-Robinson (PR)"
)

print("Peng-Robinson property package created.")


# ============================================================
# CREATE MATERIAL STREAMS
# ============================================================

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


# ============================================================
# CREATE DISTILLATION COLUMN
# ============================================================

column_obj = sim.AddObject(
    ObjectType.DistillationColumn,
    300,
    250,
    "DC1"
)


# ============================================================
# CREATE ENERGY STREAMS
# ============================================================

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


# ============================================================
# GET ACTUAL OBJECTS
# ============================================================

feed = feed_obj.GetAsObject()
distillate = distillate_obj.GetAsObject()
bottoms = bottoms_obj.GetAsObject()

column = column_obj.GetAsObject()

condenser = condenser_obj.GetAsObject()
reboiler = reboiler_obj.GetAsObject()

print("Objects created.")


# ============================================================
# ASSIGN PROPERTY PACKAGE
# ============================================================

column.PropertyPackage = pp

print("Peng-Robinson assigned to column.")


# ============================================================
# TEST CASE
# ============================================================

feed_pressure = 1.5
feed_vapor_fraction = 0.15

benzene_fraction = 0.50
toluene_fraction = 1.0 - benzene_fraction

number_of_stages = 20
feed_stage_fraction = 0.50

reflux_ratio = 2.5

bottoms_fraction = 0.50

feed_flow = 100.0


print("\n")
print("=" * 70)
print("TEST CASE")
print("=" * 70)

print(
    "Feed pressure       :",
    feed_pressure,
    "atm"
)

print(
    "Feed vapor fraction :",
    feed_vapor_fraction
)

print(
    "Benzene fraction    :",
    benzene_fraction
)

print(
    "Toluene fraction    :",
    toluene_fraction
)

print(
    "Number of stages    :",
    number_of_stages
)

print(
    "Feed-stage fraction :",
    feed_stage_fraction
)

print(
    "Reflux ratio        :",
    reflux_ratio
)

print(
    "Bottoms fraction    :",
    bottoms_fraction
)

print(
    "Feed flow           :",
    feed_flow,
    "kmol/h"
)


# ============================================================
# CALCULATE FEED STAGE
# ============================================================

feed_stage = round(
    feed_stage_fraction * number_of_stages
)

feed_stage = max(
    1,
    min(
        feed_stage,
        number_of_stages - 1
    )
)

print(
    "\nCalculated feed stage:",
    feed_stage
)


# ============================================================
# CONFIGURE FEED
# ============================================================

print("\nConfiguring feed...")


# ------------------------------------------------------------
# Feed pressure
# ------------------------------------------------------------

feed.SetPressure(
    f"{feed_pressure} atm"
)

print("Feed pressure set.")


# ------------------------------------------------------------
# Feed flow
# ------------------------------------------------------------

feed.SetMolarFlow(
    f"{feed_flow} kmol/h"
)

print("Feed flow set.")


# ------------------------------------------------------------
# Feed composition
# ------------------------------------------------------------

feed.SetOverallMolarComposition(
    [
        benzene_fraction,
        toluene_fraction
    ]
)

print("Feed composition set.")


# ============================================================
# PRESSURE + VAPOR FRACTION FLASH
# ============================================================

flash_result = feed.SetFlashSpec(
    "PVF"
)

print(
    "Feed flash specification:",
    flash_result
)


# ============================================================
# CONFIGURE NUMBER OF STAGES
# ============================================================

print("\nConfiguring column...")

column.SetNumberOfStages(
    number_of_stages
)

print(
    "Number of stages:",
    column.NumberOfStages
)


# ============================================================
# CONNECT COLUMN STREAMS
#
# IMPORTANT:
# DWSIM 9.x uses:
#
# ConnectFeed(feed, stage)
#
# ============================================================

print("\nConnecting column streams...")


# ------------------------------------------------------------
# Feed
# ------------------------------------------------------------

column.ConnectFeed(
    feed,
    feed_stage
)

print(
    "Feed connected at stage:",
    feed_stage
)


# ------------------------------------------------------------
# Distillate
# ------------------------------------------------------------

column.ConnectDistillate(
    distillate
)

print(
    "Distillate connected."
)


# ------------------------------------------------------------
# Bottoms
# ------------------------------------------------------------

column.ConnectBottoms(
    bottoms
)

print(
    "Bottoms connected."
)


# ------------------------------------------------------------
# Condenser duty
# ------------------------------------------------------------

column.ConnectCondenserDuty(
    condenser
)

print(
    "Condenser duty connected."
)


# ------------------------------------------------------------
# Reboiler duty
# ------------------------------------------------------------

column.ConnectReboilerDuty(
    reboiler
)

print(
    "Reboiler duty connected."
)


# ============================================================
# COLUMN PRESSURE
#
# DWSIM uses Pa internally.
#
# 1 atm = 101325 Pa
# ============================================================

ATM_TO_PA = 101325.0

column_pressure_pa = (
        feed_pressure * ATM_TO_PA
)

print(
    "\nColumn pressure:",
    column_pressure_pa,
    "Pa"
)


# ------------------------------------------------------------
# Set top pressure
# ------------------------------------------------------------

column.SetTopPressure(
    float(column_pressure_pa)
)

print(
    "Top pressure set."
)


# ------------------------------------------------------------
# Initialize every stage pressure
# ------------------------------------------------------------

try:

    for stage in column.Stages:

        stage.P = float(
            column_pressure_pa
        )

    print(
        "All stage pressures initialized to:",
        column_pressure_pa,
        "Pa"
    )

except Exception as e:

    print(
        "WARNING: Could not initialize all stage pressures:",
        e
    )


# ============================================================
# COLUMN SPECIFICATIONS
# ============================================================

print(
    "\nSetting column specifications..."
)


# ============================================================
# CONDENSER SPECIFICATION
# ============================================================

column.SetCondenserSpec(
    "Reflux Ratio",
    float(reflux_ratio),
    ""
)

print(
    "Condenser specification:",
    reflux_ratio,
    "reflux ratio"
)


# ============================================================
# REBOILER SPECIFICATION
# ============================================================

bottoms_flow = (
        feed_flow *
        bottoms_fraction
)

column.SetReboilerSpec(
    "Product Molar Flow Rate",
    float(bottoms_flow),
    "kmol/h"
)

print(
    "Bottoms flow specification:",
    bottoms_flow,
    "kmol/h"
)


# ============================================================
# COLUMN STATE
# ============================================================

print("\n")
print("=" * 70)
print("COLUMN STATE")
print("=" * 70)

print(
    "Stages       :",
    column.NumberOfStages
)

print(
    "Feed stage   :",
    feed_stage
)

print(
    "Top pressure :",
    feed_pressure,
    "atm"
)

print(
    "Top pressure :",
    column_pressure_pa,
    "Pa"
)

print(
    "Reflux ratio :",
    reflux_ratio
)

print(
    "Bottoms flow :",
    bottoms_flow,
    "kmol/h"
)


# ============================================================
# RUN DWSIM
# ============================================================

print("\n")
print("=" * 70)
print("RUNNING DWSIM")
print("=" * 70)

errors = interf.CalculateFlowsheet4(
    sim
)

print(
    "\nDWSIM calculation finished."
)


# ============================================================
# CALCULATION ERRORS
# ============================================================

if errors is not None:

    print(
        "\nDWSIM returned:"
    )

    try:

        for error in errors:

            print(
                "ERROR:",
                error
            )

    except Exception:

        print(
            errors
        )

else:

    print(
        "No calculation errors returned."
    )


# ============================================================
# CALCULATION STATUS
# ============================================================

print("\n")
print("=" * 70)
print("CALCULATION STATUS")
print("=" * 70)


try:

    solved = sim.Solved

    print(
        "Flowsheet solved:",
        solved
    )

except Exception as e:

    solved = False

    print(
        "Flowsheet solved: ERROR",
        e
    )


try:

    print(
        "Column calculated:",
        column.Calculated
    )

except Exception as e:

    print(
        "Column calculated: ERROR",
        e
    )


try:

    print(
        "Column error:",
        column.ErrorMessage
    )

except Exception as e:

    print(
        "Column error: ERROR",
        e
    )


# ============================================================
# OUTPUTS
# ============================================================

print("\n")
print("=" * 70)
print("OUTPUTS")
print("=" * 70)


# ============================================================
# x_D
# ============================================================

try:

    xd = distillate.GetOverallComposition()[0]

    print(
        "x_D (benzene):",
        xd
    )

except Exception as e:

    xd = None

    print(
        "Could not read x_D:",
        e
    )


# ============================================================
# x_B
# ============================================================

try:

    xb = bottoms.GetOverallComposition()[0]

    print(
        "x_B (benzene):",
        xb
    )

except Exception as e:

    xb = None

    print(
        "Could not read x_B:",
        e
    )


# ============================================================
# Q_C
# ============================================================

try:

    qc = column.CondenserDuty

    print(
        "Q_C:",
        qc
    )

except Exception as e:

    qc = None

    print(
        "Could not read Q_C:",
        e
    )


# ============================================================
# Q_R
# ============================================================

try:

    qr = column.ReboilerDuty

    print(
        "Q_R:",
        qr
    )

except Exception as e:

    qr = None

    print(
        "Could not read Q_R:",
        e
    )


# ============================================================
# VALIDITY CHECK
# ============================================================

print("\n")
print("=" * 70)
print("RESULT VALIDITY")
print("=" * 70)

if solved:

    print(
        "VALID DWSIM RESULT"
    )

    print(
        "The flowsheet converged successfully."
    )

else:

    print(
        "INVALID DWSIM RESULT"
    )

    print(
        "The flowsheet did NOT converge."
    )

    print(
        "Do NOT use x_D, x_B, Q_C or Q_R from this run."
    )


# ============================================================
# SAVE FLOWSHEET
#
# SaveFlowsheet2 uses:
#
# SaveFlowsheet2(flowsheet, filepath)
# ============================================================

print("\n")
print("=" * 70)
print("SAVING FLOWSHEET")
print("=" * 70)

try:

    interf.SaveFlowsheet2(
        sim,
        output_file
    )

    print(
        "Flowsheet saved:"
    )

    print(
        output_file
    )

except Exception as e:

    print(
        "Could not save flowsheet:"
    )

    print(
        e
    )


# ============================================================
# FINISHED
# ============================================================

print("\n")
print("=" * 70)
print("DONE")
print("=" * 70)