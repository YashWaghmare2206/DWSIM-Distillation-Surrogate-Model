import os
import csv
import math
import gc
import pythoncom
import clr

pythoncom.CoInitialize()


# ============================================================
# DWSIM INSTALLATION
# ============================================================

dwsimpath = r"C:\Users\Rupali Waghmare\AppData\Local\DWSIM"


# ============================================================
# PROJECT PATHS
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
    "data",
    "01_validation_runs"
)

os.makedirs(data_dir, exist_ok=True)

output_csv = os.path.join(
    data_dir,
    "dwsim_sobol_phase1_32_final.csv"
)

rejected_csv = os.path.join(
    data_dir,
    "dwsim_sobol_phase1_rejected_final.csv"
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

    print("Loading:", path)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"DLL not found:\n{path}"
        )

    clr.AddReference(path)


print("\nDWSIM DLLs loaded successfully.")


# ============================================================
# DWSIM IMPORTS
# ============================================================

from DWSIM.Automation import Automation3
from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType

from scipy.stats import qmc


# ============================================================
# EXPERIMENT SETTINGS
# ============================================================

# Phase-1 validation batch
N_SAMPLES = 32

# Fixed feed flow according to the plan
FEED_FLOW_KMOL_H = 100.0

# Pressure conversion
ATM_TO_PA = 101325.0

# Reproducible Sobol sequence
SEED = 42


# ============================================================
# VALIDATION TOLERANCES
# ============================================================

# Composition must remain physically valid
COMPOSITION_TOL = 1e-6

# Total/benzene material-balance tolerance
#
# We use 5e-5 because the previous 32-case test showed
# only very small numerical discrepancies in the benzene
# balance.
#
# We still record the EXACT errors in the CSV.
#
MASS_BALANCE_REL_TOL = 5e-5

MASS_BALANCE_ABS_TOL = 1e-6


# ============================================================
# FINAL 7-D SAMPLING SPACE
# ============================================================
#
# 1. Pressure             = 1.0 - 2.0 atm
# 2. Vapor fraction       = 0.0 - 0.30
# 3. Benzene feed         = 0.30 - 0.70
# 4. Number of stages     = 10 - 30
# 5. Feed-stage fraction  = 0.30 - 0.70
# 6. Reflux ratio         = 1.2 - 4.5
# 7. Bottoms fraction     = 0.40 - 0.60
#
# Feed flow = FIXED 100 kmol/h
#
# Temperature = NOT independently sampled.
# DWSIM determines the thermodynamic state.
# ============================================================


# ============================================================
# SOBOL SAMPLER
# ============================================================

sampler = qmc.Sobol(
    d=7,
    scramble=True,
    seed=SEED
)

# 2^5 = 32 Sobol points
sobol_points = sampler.random_base2(
    m=5
)


print("\n")
print("=" * 80)
print("PHASE 1 — SOBOL VALIDATION")
print("=" * 80)

print(
    "Number of samples:",
    N_SAMPLES
)

print(
    "Dimensions:",
    7
)

print(
    "Sobol seed:",
    SEED
)

print(
    "\nSampling ranges:"
)

print(
    "Pressure:",
    "1.0 - 2.0 atm"
)

print(
    "Vapor fraction:",
    "0.0 - 0.30"
)

print(
    "Benzene feed:",
    "0.30 - 0.70"
)

print(
    "Stages:",
    "10 - 30"
)

print(
    "Feed-stage fraction:",
    "0.30 - 0.70"
)

print(
    "Reflux ratio:",
    "1.2 - 4.5"
)

print(
    "Bottoms fraction:",
    "0.40 - 0.60"
)

print(
    "Feed flow:",
    "100 kmol/h FIXED"
)


# ============================================================
# SCALE SOBOL VALUE
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
            (maximum - minimum)
    )


# ============================================================
# CONVERT SOBOL POINT TO ENGINEERING INPUTS
# ============================================================

def make_inputs(point):

    # --------------------------------------------------------
    # 1. Pressure
    # --------------------------------------------------------

    pressure_atm = scale(
        point[0],
        1.0,
        2.0
    )


    # --------------------------------------------------------
    # 2. Vapor fraction
    # --------------------------------------------------------

    vapor_fraction = scale(
        point[1],
        0.0,
        0.30
    )


    # --------------------------------------------------------
    # 3. Benzene feed fraction
    # --------------------------------------------------------

    benzene_feed = scale(
        point[2],
        0.30,
        0.70
    )

    toluene_feed = (
            1.0 -
            benzene_feed
    )


    # --------------------------------------------------------
    # 4. Number of stages
    # --------------------------------------------------------

    stages = int(
        round(
            scale(
                point[3],
                10,
                30
            )
        )
    )

    stages = max(
        10,
        min(
            30,
            stages
        )
    )


    # --------------------------------------------------------
    # 5. Feed-stage fraction
    # --------------------------------------------------------

    feed_stage_fraction = scale(
        point[4],
        0.30,
        0.70
    )

    feed_stage = int(
        round(
            feed_stage_fraction *
            stages
        )
    )

    # Feed stage must be inside the column
    feed_stage = max(
        1,
        min(
            stages - 1,
            feed_stage
        )
    )


    # --------------------------------------------------------
    # 6. Reflux ratio
    # --------------------------------------------------------

    reflux_ratio = scale(
        point[5],
        1.2,
        4.5
    )


    # --------------------------------------------------------
    # 7. Bottoms flow fraction
    # --------------------------------------------------------

    bottoms_fraction = scale(
        point[6],
        0.40,
        0.60
    )


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

        "feed_stage_fraction":
            feed_stage_fraction,

        "feed_stage":
            feed_stage,

        "reflux_ratio":
            reflux_ratio,

        "bottoms_fraction":
            bottoms_fraction,

        "feed_flow_kmol_h":
            FEED_FLOW_KMOL_H
    }


# ============================================================
# DWSIM AUTOMATION
# ============================================================

interf = Automation3()


# ============================================================
# CREATE EMPTY DWSIM FLOWSHEET
# ============================================================

def create_simulation():

    sim = interf.CreateFlowsheet()


    # --------------------------------------------------------
    # Compounds
    # --------------------------------------------------------

    benzene = sim.AvailableCompounds[
        "Benzene"
    ]

    toluene = sim.AvailableCompounds[
        "Toluene"
    ]


    sim.SelectedCompounds.Add(
        benzene.Name,
        benzene
    )

    sim.SelectedCompounds.Add(
        toluene.Name,
        toluene
    )


    # --------------------------------------------------------
    # Peng-Robinson
    # --------------------------------------------------------

    pp = sim.CreateAndAddPropertyPackage(
        "Peng-Robinson (PR)"
    )


    # --------------------------------------------------------
    # Feed
    # --------------------------------------------------------

    feed_obj = sim.AddObject(
        ObjectType.MaterialStream,
        100,
        250,
        "Feed"
    )


    # --------------------------------------------------------
    # Distillate
    # --------------------------------------------------------

    distillate_obj = sim.AddObject(
        ObjectType.MaterialStream,
        500,
        100,
        "Distillate"
    )


    # --------------------------------------------------------
    # Bottoms
    # --------------------------------------------------------

    bottoms_obj = sim.AddObject(
        ObjectType.MaterialStream,
        500,
        400,
        "Bottoms"
    )


    # --------------------------------------------------------
    # Distillation column
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
    # Actual objects
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Assign property package
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
# FINITE NUMBER CHECK
# ============================================================

def is_finite(value):

    try:

        return math.isfinite(
            float(value)
        )

    except:

        return False


# ============================================================
# MATERIAL BALANCE VALIDATION
# ============================================================

def balance_valid(
        calculated,
        expected
):

    tolerance = max(
        MASS_BALANCE_ABS_TOL,
        MASS_BALANCE_REL_TOL *
        max(
            abs(expected),
            1.0
        )
    )

    return (
            abs(
                calculated - expected
            )
            <= tolerance
    )


# ============================================================
# RUN ONE DWSIM CASE
# ============================================================

def run_case(inputs):

    (
        sim,
        feed,
        distillate,
        bottoms,
        column,
        condenser,
        reboiler
    ) = create_simulation()


    try:

        # ====================================================
        # INPUTS
        # ====================================================

        pressure_atm = inputs[
            "pressure_atm"
        ]

        vapor_fraction = inputs[
            "vapor_fraction"
        ]

        benzene_feed = inputs[
            "benzene_feed"
        ]

        toluene_feed = inputs[
            "toluene_feed"
        ]

        stages = inputs[
            "stages"
        ]

        feed_stage = inputs[
            "feed_stage"
        ]

        reflux_ratio = inputs[
            "reflux_ratio"
        ]

        bottoms_fraction = inputs[
            "bottoms_fraction"
        ]

        feed_flow_kmol_h = inputs[
            "feed_flow_kmol_h"
        ]


        # ====================================================
        # FEED CONFIGURATION
        # ====================================================

        feed.SetPressure(
            f"{pressure_atm} atm"
        )

        feed.SetMolarFlow(
            f"{feed_flow_kmol_h} kmol/h"
        )

        feed.SetOverallMolarComposition(
            [
                benzene_feed,
                toluene_feed
            ]
        )

        feed.SetFlashSpec(
            "PVF"
        )


        # ====================================================
        # COLUMN CONFIGURATION
        # ====================================================

        column.SetNumberOfStages(
            stages
        )


        # ====================================================
        # CONNECT STREAMS
        # ====================================================

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


        # ====================================================
        # COLUMN PRESSURE
        # ====================================================

        pressure_pa = (
                pressure_atm *
                ATM_TO_PA
        )

        column.SetTopPressure(
            float(pressure_pa)
        )


        # Initialize all stages
        for stage in column.Stages:

            stage.P = float(
                pressure_pa
            )


        # ====================================================
        # CONDENSER
        # ====================================================

        column.SetCondenserSpec(
            "Reflux Ratio",
            float(reflux_ratio),
            ""
        )


        # ====================================================
        # REBOILER
        # ====================================================

        bottoms_flow_kmol_h = (
                feed_flow_kmol_h *
                bottoms_fraction
        )

        column.SetReboilerSpec(
            "Product Molar Flow Rate",
            float(
                bottoms_flow_kmol_h
            ),
            "kmol/h"
        )


        # ====================================================
        # RUN DWSIM
        # ====================================================

        interf.CalculateFlowsheet4(
            sim
        )


        # ====================================================
        # CONVERGENCE CHECK
        # ====================================================

        if not sim.Solved:

            return (
                None,
                "DWSIM flowsheet did not converge"
            )


        # ====================================================
        # COLUMN CHECK
        # ====================================================

        if not column.Calculated:

            return (
                None,
                "Column was not calculated"
            )


        # ====================================================
        # ERROR MESSAGE CHECK
        # ====================================================

        try:

            error_message = str(
                column.ErrorMessage
            )

        except:

            error_message = ""


        if error_message.strip():

            return (
                None,
                "Column error: " +
                error_message
            )


        # ====================================================
        # DWSIM FLOW VALUES
        #
        # DWSIM returns mol/s.
        #
        # 1 mol/s = 3.6 kmol/h
        # ====================================================

        F_mol_s = float(
            feed.GetMolarFlow()
        )

        D_mol_s = float(
            distillate.GetMolarFlow()
        )

        B_mol_s = float(
            bottoms.GetMolarFlow()
        )


        F_kmol_h = (
                F_mol_s * 3.6
        )

        D_kmol_h = (
                D_mol_s * 3.6
        )

        B_kmol_h = (
                B_mol_s * 3.6
        )


        # ====================================================
        # COMPOSITIONS
        # ====================================================

        feed_comp = (
            feed.GetOverallComposition()
        )

        distillate_comp = (
            distillate.GetOverallComposition()
        )

        bottoms_comp = (
            bottoms.GetOverallComposition()
        )


        zF = float(
            feed_comp[0]
        )

        xD = float(
            distillate_comp[0]
        )

        xB = float(
            bottoms_comp[0]
        )


        # ====================================================
        # ENERGY DUTIES
        # ====================================================

        Q_C = float(
            column.CondenserDuty
        )

        Q_R = float(
            column.ReboilerDuty
        )


        # ====================================================
        # FINITE CHECK
        # ====================================================

        values = [

            F_mol_s,
            D_mol_s,
            B_mol_s,

            F_kmol_h,
            D_kmol_h,
            B_kmol_h,

            zF,
            xD,
            xB,

            Q_C,
            Q_R
        ]


        if not all(
                is_finite(v)
                for v in values
        ):

            return (
                None,
                "Non-finite DWSIM result"
            )


        # ====================================================
        # FLOW CHECK
        # ====================================================

        if F_kmol_h <= 0:

            return (
                None,
                "Invalid feed flow"
            )

        if D_kmol_h < 0:

            return (
                None,
                "Negative distillate flow"
            )

        if B_kmol_h < 0:

            return (
                None,
                "Negative bottoms flow"
            )


        # ====================================================
        # COMPOSITION RANGE CHECK
        # ====================================================

        for x in [
            zF,
            xD,
            xB
        ]:

            if (
                    x < -COMPOSITION_TOL
                    or
                    x > 1.0 +
                    COMPOSITION_TOL
            ):

                return (
                    None,
                    "Composition outside [0,1]"
                )


        # ====================================================
        # COMPOSITION SUM CHECK
        # ====================================================

        feed_sum = sum(
            float(x)
            for x in feed_comp
        )

        distillate_sum = sum(
            float(x)
            for x in distillate_comp
        )

        bottoms_sum = sum(
            float(x)
            for x in bottoms_comp
        )


        if abs(
                feed_sum - 1.0
        ) > COMPOSITION_TOL:

            return (
                None,
                "Feed composition does not sum to 1"
            )


        if abs(
                distillate_sum - 1.0
        ) > COMPOSITION_TOL:

            return (
                None,
                "Distillate composition does not sum to 1"
            )


        if abs(
                bottoms_sum - 1.0
        ) > COMPOSITION_TOL:

            return (
                None,
                "Bottoms composition does not sum to 1"
            )


        # ====================================================
        # TOTAL MATERIAL BALANCE
        #
        # F = D + B
        # ====================================================

        total_balance_error = abs(
            F_kmol_h
            -
            D_kmol_h
            -
            B_kmol_h
        )

        total_balance_relative_error = (
                total_balance_error
                /
                max(
                    abs(F_kmol_h),
                    1e-12
                )
        )


        # ====================================================
        # BENZENE BALANCE
        #
        # F*zF = D*xD + B*xB
        # ====================================================

        benzene_in = (
                F_kmol_h *
                zF
        )

        benzene_out = (
                D_kmol_h *
                xD
                +
                B_kmol_h *
                xB
        )

        benzene_balance_error = abs(
            benzene_in -
            benzene_out
        )

        benzene_relative_error = (
                benzene_balance_error
                /
                max(
                    abs(benzene_in),
                    1e-12
                )
        )


        # ====================================================
        # DETAILED BALANCE OUTPUT
        # ====================================================

        print("\nBALANCE CHECK")

        print(
            f"Feed       : "
            f"{F_kmol_h:.10f} kmol/h"
        )

        print(
            f"Distillate : "
            f"{D_kmol_h:.10f} kmol/h"
        )

        print(
            f"Bottoms    : "
            f"{B_kmol_h:.10f} kmol/h"
        )

        print(
            f"Total error: "
            f"{total_balance_error:.12e}"
        )

        print(
            f"Benzene in : "
            f"{benzene_in:.10f}"
        )

        print(
            f"Benzene out: "
            f"{benzene_out:.10f}"
        )

        print(
            f"Benzene err: "
            f"{benzene_balance_error:.12e}"
        )

        print(
            f"Benzene rel: "
            f"{benzene_relative_error:.12e}"
        )


        # ====================================================
        # TOTAL BALANCE VALIDATION
        # ====================================================

        if not balance_valid(
                D_kmol_h + B_kmol_h,
                F_kmol_h
        ):

            return (
                None,
                (
                    "Total material balance failed | "
                    f"absolute="
                    f"{total_balance_error:.12e} | "
                    f"relative="
                    f"{total_balance_relative_error:.12e}"
                )
            )


        # ====================================================
        # BENZENE BALANCE VALIDATION
        # ====================================================

        if not balance_valid(
                benzene_out,
                benzene_in
        ):

            return (
                None,
                (
                    "Benzene balance failed | "
                    f"absolute="
                    f"{benzene_balance_error:.12e} | "
                    f"relative="
                    f"{benzene_relative_error:.12e}"
                )
            )


        # ====================================================
        # VALID RESULT
        # ====================================================

        result = {

            # ------------------------------------------------
            # INPUTS
            # ------------------------------------------------

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
                inputs[
                    "feed_stage_fraction"
                ],

            "reflux_ratio":
                reflux_ratio,

            "bottoms_fraction":
                bottoms_fraction,

            "feed_flow_kmol_h":
                feed_flow_kmol_h,


            # ------------------------------------------------
            # DWSIM OUTPUTS
            # ------------------------------------------------

            "x_D":
                xD,

            "x_B":
                xB,

            "Q_C":
                Q_C,

            "Q_R":
                Q_R,


            # ------------------------------------------------
            # STREAM FLOWS
            # ------------------------------------------------

            "dwsim_feed_flow_mol_s":
                F_mol_s,

            "dwsim_feed_flow_kmol_h":
                F_kmol_h,

            "distillate_flow_kmol_h":
                D_kmol_h,

            "bottoms_flow_kmol_h":
                B_kmol_h,


            # ------------------------------------------------
            # VALIDATION
            # ------------------------------------------------

            "total_balance_error_kmol_h":
                total_balance_error,

            "total_balance_relative_error":
                total_balance_relative_error,

            "benzene_in_kmol_h":
                benzene_in,

            "benzene_out_kmol_h":
                benzene_out,

            "benzene_balance_error_kmol_h":
                benzene_balance_error,

            "benzene_relative_error":
                benzene_relative_error,

            "converged":
                True
        }


        return (
            result,
            None
        )


    except Exception as e:

        return (
            None,
            str(e)
        )


    finally:

        gc.collect()


# ============================================================
# RUN SOBOL CASES
# ============================================================

valid_rows = []

rejected_rows = []


for index, point in enumerate(
        sobol_points,
        start=1
):

    inputs = make_inputs(
        point
    )


    print("\n")
    print("=" * 80)
    print(
        f"CASE {index}/{N_SAMPLES}"
    )
    print("=" * 80)


    print(
        f"Pressure       : "
        f"{inputs['pressure_atm']:.6f} atm"
    )

    print(
        f"Vapor fraction : "
        f"{inputs['vapor_fraction']:.6f}"
    )

    print(
        f"Benzene feed   : "
        f"{inputs['benzene_feed']:.6f}"
    )

    print(
        f"Toluene feed   : "
        f"{inputs['toluene_feed']:.6f}"
    )

    print(
        f"Stages         : "
        f"{inputs['stages']}"
    )

    print(
        f"Feed stage     : "
        f"{inputs['feed_stage']}"
    )

    print(
        f"Feed-stage q   : "
        f"{inputs['feed_stage_fraction']:.6f}"
    )

    print(
        f"Reflux ratio   : "
        f"{inputs['reflux_ratio']:.6f}"
    )

    print(
        f"Bottoms frac.  : "
        f"{inputs['bottoms_fraction']:.6f}"
    )

    print(
        f"Feed flow      : "
        f"{inputs['feed_flow_kmol_h']:.6f} kmol/h"
    )


    # --------------------------------------------------------
    # Run DWSIM
    # --------------------------------------------------------

    result, reason = run_case(
        inputs
    )


    # --------------------------------------------------------
    # Valid
    # --------------------------------------------------------

    if result is not None:

        valid_rows.append(
            result
        )

        print("\nSTATUS: ✅ VALID")

        print(
            f"x_D = {result['x_D']:.8f}"
        )

        print(
            f"x_B = {result['x_B']:.8f}"
        )

        print(
            f"Q_C = {result['Q_C']:.8f}"
        )

        print(
            f"Q_R = {result['Q_R']:.8f}"
        )


    # --------------------------------------------------------
    # Rejected
    # --------------------------------------------------------

    else:

        rejected_rows.append({

            **inputs,

            "rejection_reason":
                reason
        })


        print(
            "\nSTATUS: ❌ REJECTED"
        )

        print(
            "Reason:",
            reason
        )


    gc.collect()


# ============================================================
# SAVE VALID DATA
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
    "feed_flow_kmol_h",

    "x_D",
    "x_B",
    "Q_C",
    "Q_R",

    "dwsim_feed_flow_mol_s",
    "dwsim_feed_flow_kmol_h",
    "distillate_flow_kmol_h",
    "bottoms_flow_kmol_h",

    "total_balance_error_kmol_h",
    "total_balance_relative_error",

    "benzene_in_kmol_h",
    "benzene_out_kmol_h",
    "benzene_balance_error_kmol_h",
    "benzene_relative_error",

    "converged"
]


with open(
        output_csv,
        "w",
        newline="",
        encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(
        valid_rows
    )


# ============================================================
# SAVE REJECTED DATA
# ============================================================

if rejected_rows:

    rejected_fields = [

        "pressure_atm",
        "vapor_fraction",
        "benzene_feed",
        "toluene_feed",
        "stages",
        "feed_stage",
        "feed_stage_fraction",
        "reflux_ratio",
        "bottoms_fraction",
        "feed_flow_kmol_h",
        "rejection_reason"
    ]


    with open(
            rejected_csv,
            "w",
            newline="",
            encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=rejected_fields
        )

        writer.writeheader()

        writer.writerows(
            rejected_rows
        )


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n")
print("=" * 80)
print("PHASE 1 COMPLETE")
print("=" * 80)

print(
    "Total Sobol cases:",
    N_SAMPLES
)

print(
    "Valid cases:",
    len(valid_rows)
)

print(
    "Rejected cases:",
    len(rejected_rows)
)

print(
    "Valid percentage:",
    f"{100 * len(valid_rows) / N_SAMPLES:.2f}%"
)


# ============================================================
# VALID RESULTS SUMMARY
# ============================================================

if valid_rows:

    print("\n")
    print("=" * 80)
    print("VALID DATA SUMMARY")
    print("=" * 80)


    print(
        "x_D range:",
        min(
            r["x_D"]
            for r in valid_rows
        ),
        "to",
        max(
            r["x_D"]
            for r in valid_rows
        )
    )


    print(
        "x_B range:",
        min(
            r["x_B"]
            for r in valid_rows
        ),
        "to",
        max(
            r["x_B"]
            for r in valid_rows
        )
    )


    print(
        "Q_C range:",
        min(
            r["Q_C"]
            for r in valid_rows
        ),
        "to",
        max(
            r["Q_C"]
            for r in valid_rows
        )
    )


    print(
        "Q_R range:",
        min(
            r["Q_R"]
            for r in valid_rows
        ),
        "to",
        max(
            r["Q_R"]
            for r in valid_rows
        )
    )


    print(
        "\nMaximum total balance error:",
        max(
            r[
                "total_balance_error_kmol_h"
            ]
            for r in valid_rows
        )
    )


    print(
        "Maximum benzene balance error:",
        max(
            r[
                "benzene_balance_error_kmol_h"
            ]
            for r in valid_rows
        )
    )


    print(
        "Maximum benzene relative error:",
        max(
            r[
                "benzene_relative_error"
            ]
            for r in valid_rows
        )
    )


# ============================================================
# FILE LOCATIONS
# ============================================================

print("\n")
print("=" * 80)
print("OUTPUT FILES")
print("=" * 80)

print(
    "Valid:",
    output_csv
)

if rejected_rows:

    print(
        "Rejected:",
        rejected_csv
    )


print("\nDONE.")