
# Surrogate Modeling of a Binary Distillation Column Using DWSIM and Machine Learning

**FOSSEE Autumn 2026 Internship — Screening Task 3**

## Project Description

This project develops a machine-learning surrogate model for a Benzene–Toluene binary distillation column simulated in DWSIM.

Rigorous DWSIM simulations provide detailed process results but require more computational time than a trained machine-learning model. The surrogate model is developed to approximate the DWSIM outputs for repeated prediction, sensitivity analysis and future process-optimization applications.

The four predicted outputs are:

- `x_D_benzene` — distillate benzene mole fraction
- `x_B_benzene` — bottoms benzene mole fraction
- `Q_C` — condenser duty (kW)
- `Q_R` — reboiler duty (kW)

The complete workflow covers:

1. DWSIM flowsheet generation
2. Automated DWSIM simulation
3. Sobol sampling
4. Latin Hypercube Sampling (LHS)
5. Data-quality checking
6. Data preprocessing
7. Exploratory data analysis
8. Machine-learning model training
9. Hyperparameter tuning
10. Independent holdout evaluation
11. Physical-consistency checks
12. Final model selection
13. Sensitivity analysis
14. Feature-importance analysis
15. Result visualization


---

## Problem Statement

The objective is to predict the main product compositions and energy duties of a binary distillation column from its operating conditions.

The surrogate predicts:

- `x_D_benzene`
- `x_B_benzene`
- `Q_C`
- `Q_R`

The model is intended to reproduce DWSIM results over the operating ranges represented in the generated dataset.

The surrogate provides a faster alternative to repeatedly running the rigorous DWSIM simulation when predictions are required for further analysis.


---

## DWSIM and Thermodynamic Model

### Process

- Mixture: **Benzene–Toluene**
- Process: **Binary distillation**
- Simulation software: **DWSIM**
- Thermodynamic property package: **Peng–Robinson**
- Feed flow rate: **100 kmol/h**
- Operating mode: Steady-state

### DWSIM Version

The DWSIM simulations and automation workflow were developed and tested using:

- **DWSIM 9.0.5**
- **Windows 64-bit**
- Installer: `DWSIM_v905_win64_setup.exe`

DWSIM was obtained from:

https://sourceforge.net/projects/dwsim/

DWSIM is required when regenerating the simulation datasets.

### DWSIM Automation

The DWSIM flowsheet is generated and executed programmatically using the DWSIM Automation API through Python/.NET integration.

The main simulation files are:

```text
src/simulation/model_generator.py
src/simulation/dwsim_automation.py
````

The saved DWSIM flowsheet is:

```text
dwsim_flowsheets/binary_distillation.dwxmz
```

---

## Input Variables

Seven variables are sampled for the surrogate dataset.

| Variable                   | Description                                 |         Range |
| -------------------------- | ------------------------------------------- | ------------: |
| `pressure_atm`             | Column/feed pressure                        | 1.0 – 2.0 atm |
| `requested_vapor_fraction` | Feed vapour fraction                        |   0.00 – 0.30 |
| `benzene_feed_fraction`    | Feed benzene mole fraction                  |   0.30 – 0.70 |
| `stages`                   | Number of column stages                     |       10 – 30 |
| `feed_stage_fraction`      | Feed-stage location as a fraction of stages |   0.30 – 0.70 |
| `reflux_ratio`             | Condenser reflux ratio                      |     1.2 – 4.5 |
| `bottoms_fraction`         | Bottoms fraction of feed flow               |   0.40 – 0.60 |

Some DWSIM quantities are derived from these sampled variables.

`feed_stage_fraction` is converted into an absolute feed-stage index based on the number of stages.

`bottoms_fraction` is converted into the absolute bottoms flow:

```text
bottoms_flow_kmol_h = feed_flow_kmol_h × bottoms_fraction
```

The feed flow rate is fixed at:

```text
feed_flow_kmol_h = 100 kmol/h
```

`feed_temperature_C` is obtained from the DWSIM Pressure–Vapour-Fraction (PVF) feed flash and is not independently sampled.

---

## Output Variables

The surrogate predicts four DWSIM outputs:

| Output        | Description                      | Unit          |
| ------------- | -------------------------------- | ------------- |
| `x_D_benzene` | Distillate benzene mole fraction | mole fraction |
| `x_B_benzene` | Bottoms benzene mole fraction    | mole fraction |
| `Q_C`         | Condenser duty                   | kW            |
| `Q_R`         | Reboiler duty                    | kW            |

---

## Dataset Generation

Two sampling methods were used:

1. Sobol sampling for the main training and validation dataset
2. Latin Hypercube Sampling (LHS) for the independent holdout dataset

Each sampled operating condition is passed to the automated DWSIM flowsheet.

The DWSIM simulation is executed, convergence is checked, and the resulting case is stored as either converged or non-converged.

Only valid converged cases are used for the final machine-learning datasets.

### Sobol Dataset

The main Sobol dataset is generated using:

```text
src/sampling/03_generate_2560_sobol.py
```

Requested cases:

```text
2,560
```

Valid converged cases:

```text
2,524
```

The raw data is stored in:

```text
data/02_raw_train_sobol/
```

with:

```text
dataset_2560_converged.csv
dataset_2560_not_converged.csv
```

### LHS Holdout Dataset

The independent LHS dataset is generated using:

```text
src/sampling/04_generate_500_lhs.py
```

Requested cases:

```text
500
```

Valid converged cases:

```text
491
```

The raw data is stored in:

```text
data/03_raw_holdout_lhs/
```

with:

```text
lhs_500_converged.csv
lhs_500_not_converged.csv
```

### Final Dataset Counts

```text
Sobol valid rows: 2,524
LHS valid rows:     491
-------------------------
Total valid rows: 3,015
```

The Sobol dataset is used for model development.

The LHS dataset is kept completely separate and is used for final independent holdout evaluation.

---

## Handling of Non-Converged Simulations

Not every sampled operating condition necessarily produces a successful DWSIM solution.

Converged and non-converged cases are stored separately.

The raw simulation directories therefore contain:

```text
*_converged.csv
*_not_converged.csv
```

Only converged cases are used for the final machine-learning datasets.

This keeps failed simulations available for reference without allowing them to enter the final modelling dataset.

---

# Project Structure

```text
DWSIM-Distillation-Surrogate-Model/
│
├── README.md
├── Results_Summary.txt
├── requirements.txt
│
├── data/
│   ├── 01_validation_runs/
│   │   ├── dataset_256_dwsim.csv
│   │   ├── dwsim_10_samples.csv
│   │   └── test_32_vapor_fraction_checked.csv
│   │
│   ├── 02_raw_train_sobol/
│   │   ├── dataset_2560_converged.csv
│   │   └── dataset_2560_not_converged.csv
│   │
│   ├── 03_raw_holdout_lhs/
│   │   ├── lhs_500_converged.csv
│   │   └── lhs_500_not_converged.csv
│   │
│   ├── 04_processed_dwsim/
│   │   ├── final_ml_dataset.csv
│   │   └── sobol_training_cleaned.csv
│   │
│   ├── 05_tuning_results/
│   │   ├── best_params.json
│   │   └── validation_r2_scores.csv
│   │
│   └── 06_physical_checks/
│       ├── bounds_violation_summary.csv
│       ├── final_model_selection.json
│       ├── holdout_error_metrics.csv
│       └── sample_predictions_vs_actual.csv
│
├── dwsim_flowsheets/
│   └── binary_distillation.dwxmz
│
├── models/
│   └── 01_trained_models_all_5/
│       ├── ann.pkl
│       ├── polynomial_regression.pkl
│       ├── poly_features.pkl
│       ├── random_forest.pkl
│       ├── scaler_X.pkl
│       ├── scaler_y.pkl
│       ├── svr.pkl
│       └── xgboost.pkl
│
├── notebooks/
│   ├── 01_Data_Quality_Check.ipynb
│   ├── 02_Data_Cleaning_Preprocessing.ipynb
│   ├── 03_Visualization_EDA.ipynb
│   ├── 04_Model_Training.ipynb
│   ├── 05_Hyperparameter_Tuning.ipynb
│   ├── 06_Final_Holdout_Evaluation.ipynb
│   ├── 07_Physical_Consistency_Check.ipynb
│   └── 08_Result_Plots.ipynb
│
├── outputs/
│   └── plots/
│       ├── feature_importance_ann.png
│       ├── feature_importance_trees.png
│       │
│       ├── Error Comparison/
│       │   ├── error_comparison_mae.png
│       │   ├── error_comparison_r2.png
│       │   └── error_comparison_rmse.png
│       │
│       ├── Predicted vs Actual/
│       │   ├── predicted_vs_actual_ANN.png
│       │   ├── predicted_vs_actual_PolynomialRegression.png
│       │   ├── predicted_vs_actual_RandomForest.png
│       │   ├── predicted_vs_actual_SVR.png
│       │   └── predicted_vs_actual_XGBoost.png
│       │
│       └── Sensitivity Analysis/
│           ├── sensitivity_feed_composition.png
│           └── sensitivity_reflux_ratio.png
│
└── src/
    ├── sampling/
    │   ├── 01_sobol_validation.py
    │   ├── 02_sobol_intermediate_validation.py
    │   ├── 03_generate_2560_sobol.py
    │   └── 04_generate_500_lhs.py
    │
    ├── simulation/
    │   ├── dwsim_automation.py
    │   └── model_generator.py
    │
    └── sample_predictions.py
```

---

## Machine-Learning Models

Six regression approaches were initially explored:

1. Linear Regression
2. Polynomial Regression
3. Random Forest
4. XGBoost
5. Support Vector Regression (SVR)
6. Artificial Neural Network (ANN)

Linear Regression was used as the initial baseline.

Five models were carried forward for final comparison and tuning:

* Polynomial Regression
* Random Forest
* XGBoost
* SVR
* ANN

The model training workflow is implemented in:

```text
notebooks/04_Model_Training.ipynb
```

---

## Data Preprocessing

The preprocessing workflow includes:

* Data-quality checks
* Missing-value checks
* Data-type validation
* Duplicate checks
* Range validation
* Derived-variable validation
* Feature scaling
* Preparation of model inputs and targets

Processed datasets are stored in:

```text
data/04_processed_dwsim/
```

The preprocessing objects used by the trained models are stored in:

```text
models/01_trained_models_all_5/
```

These include:

```text
scaler_X.pkl
scaler_y.pkl
poly_features.pkl
```

---

## Training and Validation

The Sobol dataset is used for model development.

A 70/30 train-validation split is used with:

```text
random_state = 42
```

The independent LHS dataset is not used during:

* Training
* Validation
* Hyperparameter tuning

This ensures that the LHS dataset remains an independent final holdout.

The overall workflow is:

```text
2,524 Sobol valid rows
        │
        ├── 70% Training
        │
        └── 30% Validation

491 LHS valid rows
        │
        └── Independent Holdout
```

---

## Hyperparameter Tuning

Hyperparameter tuning is performed using:

```text
notebooks/05_Hyperparameter_Tuning.ipynb
```

The results are stored in:

```text
data/05_tuning_results/
├── best_params.json
└── validation_r2_scores.csv
```

The tuned models are then evaluated on the independent LHS holdout dataset.

---

## Final Model Selection

The primary basis for final target-wise model selection is performance on the independent LHS holdout dataset.

Physical-consistency checks are evaluated separately to assess model behaviour and limitations.

### Primary Single-Model Surrogate

**ANN**

ANN provides the strongest overall holdout performance across the four outputs and is the preferred model when one unified surrogate is required.

### Target-Specific Configuration

The final target-specific configuration is:

| Target        | Selected Model        |
| ------------- | --------------------- |
| `x_D_benzene` | ANN                   |
| `x_B_benzene` | ANN                   |
| `Q_C`         | Polynomial Regression |
| `Q_R`         | Polynomial Regression |

This configuration is preferred when per-output prediction accuracy is more important than using one model for all four outputs.

The final selection is stored in:

```text
data/06_physical_checks/final_model_selection.json
```

---

## Independent Holdout Evaluation

The final models are evaluated using the independent 491-row LHS dataset:

```text
data/03_raw_holdout_lhs/lhs_500_converged.csv
```

The final performance metrics are stored in:

```text
data/06_physical_checks/holdout_error_metrics.csv
```

The reported metrics include:

* MAE
* RMSE
* R²

The evaluation plots are stored under:

```text
outputs/plots/
```

---

## Physical Consistency Checks

The final models are checked against basic physical constraints.

The checks include:

* `0 ≤ x_D_benzene ≤ 1`
* `0 ≤ x_B_benzene ≤ 1`
* `x_D_benzene ≥ x_B_benzene`
* Non-negative condenser duty
* Non-negative reboiler duty

The physical-bound results are stored in:

```text
data/06_physical_checks/bounds_violation_summary.csv
```

Sensitivity analysis is performed for:

* Reflux ratio
* Feed benzene fraction

The sensitivity plots are stored in:

```text
outputs/plots/Sensitivity Analysis/
```

---

## Feature Importance

Feature importance is evaluated for the tree-based models and ANN.

The plots are stored in:

```text
outputs/plots/
├── feature_importance_ann.png
└── feature_importance_trees.png
```

These plots are used to examine which operating variables have the largest influence on the surrogate predictions.

---

## Software Requirements

### DWSIM

For reproducing the simulation data:

* DWSIM **9.0.5**
* Windows 64-bit
* Compatible .NET installation
* DWSIM Automation API

DWSIM is required only when regenerating the DWSIM simulation datasets.

### Python

Python **3.10 or later** is recommended.

### Main Python Dependencies

```text
numpy
pandas
scikit-learn
xgboost
joblib
matplotlib
scipy
pythonnet
jupyter
```

They can be installed using:

```bash
pip install numpy pandas scikit-learn xgboost joblib matplotlib scipy pythonnet jupyter
```

---

## How to Use the Repository

There are two main ways to use the project.

### A. Use the Existing Dataset and Models

DWSIM is **not required** if the objective is to inspect the existing datasets, run the machine-learning workflow or evaluate the saved models.

The repository already contains:

```text
data/
models/
notebooks/
outputs/
```

The trained models and preprocessing objects are available under:

```text
models/01_trained_models_all_5/
```

### B. Regenerate the DWSIM Dataset

DWSIM is required when regenerating the simulation datasets.

The complete workflow is:

```text
Sampling
   ↓
DWSIM Automation
   ↓
DWSIM Flowsheet Calculation
   ↓
Convergence Check
   ↓
Converged / Non-Converged CSV
   ↓
Data Cleaning
   ↓
Model Training
   ↓
Hyperparameter Tuning
   ↓
Independent LHS Holdout Evaluation
   ↓
Physical Consistency Checks
```

---

## Reproduction Steps

### Step 1 — Install DWSIM

Install:

```text
DWSIM 9.0.5
Windows 64-bit
```

The installer used for this project was:

```text
DWSIM_v905_win64_setup.exe
```

DWSIM was obtained from:

[https://sourceforge.net/projects/dwsim/](https://sourceforge.net/projects/dwsim/)

### Step 2 — Install Python Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

### Step 3 — Configure DWSIM

The local DWSIM installation path must be configured before generating new simulations.

The relevant file is:

```text
src/simulation/model_generator.py
```

The path should point to the DWSIM installation on the local machine.

For example:

```python
dwsimpath = r"C:\Path\To\DWSIM"
```

A user-specific installation path should not be copied directly to another system.

### Step 4 — Run Initial DWSIM Validation

Run:

```text
src/sampling/01_sobol_validation.py
src/sampling/02_sobol_intermediate_validation.py
```

These scripts are used to validate the DWSIM automation workflow before generating the complete datasets.

### Step 5 — Generate Sobol Dataset

Run:

```text
src/sampling/03_generate_2560_sobol.py
```

This requests 2,560 Sobol simulation cases.

The results are stored under:

```text
data/02_raw_train_sobol/
```

### Step 6 — Generate LHS Holdout Dataset

Run:

```text
src/sampling/04_generate_500_lhs.py
```

This requests 500 LHS simulation cases.

The results are stored under:

```text
data/03_raw_holdout_lhs/
```

The LHS dataset remains independent of model training and tuning.

### Step 7 — Data Quality Check

Run:

```text
notebooks/01_Data_Quality_Check.ipynb
```

### Step 8 — Data Cleaning and Preprocessing

Run:

```text
notebooks/02_Data_Cleaning_Preprocessing.ipynb
```

The processed datasets are stored in:

```text
data/04_processed_dwsim/
```

### Step 9 — Exploratory Data Analysis

Run:

```text
notebooks/03_Visualization_EDA.ipynb
```

This notebook is used to inspect the dataset and visualize relationships between the input and output variables.

### Step 10 — Model Training

Run:

```text
notebooks/04_Model_Training.ipynb
```

The notebook initially explores six regression approaches and carries five models forward for final comparison.

### Step 11 — Hyperparameter Tuning

Run:

```text
notebooks/05_Hyperparameter_Tuning.ipynb
```

The results are stored in:

```text
data/05_tuning_results/
```

### Step 12 — Final Holdout Evaluation

Run:

```text
notebooks/06_Final_Holdout_Evaluation.ipynb
```

The independent 491-row LHS dataset is used for final evaluation.

The results are stored in:

```text
data/06_physical_checks/holdout_error_metrics.csv
```

### Step 13 — Physical Consistency Check

Run:

```text
notebooks/07_Physical_Consistency_Check.ipynb
```

This evaluates physical-bound violations and sensitivity behaviour.

### Step 14 — Generate Result Plots

Run:

```text
notebooks/08_Result_Plots.ipynb
```

The generated plots are stored under:

```text
outputs/plots/
```

---

## Trained Models

The trained model artifacts are stored in:

```text
models/01_trained_models_all_5/
```

The directory contains:

```text
ann.pkl
polynomial_regression.pkl
poly_features.pkl
random_forest.pkl
scaler_X.pkl
scaler_y.pkl
svr.pkl
xgboost.pkl
```

The preprocessing objects are included because they are required for consistent model prediction.

---

## Important Result Files

### Holdout Performance

```text
data/06_physical_checks/holdout_error_metrics.csv
```

Contains the final:

* MAE
* RMSE
* R²

values from the independent LHS holdout evaluation.

### Physical Consistency

```text
data/06_physical_checks/bounds_violation_summary.csv
```

Contains physical-bound violation counts for the evaluated models.

### Final Model Selection

```text
data/06_physical_checks/final_model_selection.json
```

Contains the selected model for each target.

### Hyperparameter Results

```text
data/05_tuning_results/
```

Contains:

```text
best_params.json
validation_r2_scores.csv
```

---

## Reproducibility Notes

The repository contains the generated datasets, trained model artifacts and result files used for the reported results.

The committed datasets and evaluation results should be treated as the reference results for the project.

Random Forest, XGBoost and ANN involve stochastic training, so small differences may occur when models are retrained on another system or with different library versions.

For the closest reproduction:

* Use DWSIM 9.0.5.
* Use the same operating ranges.
* Use the same train/validation split.
* Use `random_state = 42`.
* Use the saved hyperparameters.
* Use the same preprocessing procedure.
* Keep the LHS dataset independent from training and tuning.

---

## DWSIM vs Machine Learning Requirements

### DWSIM is required for:

* Creating new simulation data
* Re-running the DWSIM flowsheet
* Generating new Sobol samples
* Generating new LHS samples
* Reproducing the automated simulation workflow

### DWSIM is not required for:

* Inspecting the existing datasets
* Running machine-learning notebooks using existing CSV files
* Evaluating saved models
* Viewing generated plots
* Inspecting final model-selection results

---

## Main Files for Reproduction

The most important files for understanding and reproducing the workflow are:

```text
src/simulation/model_generator.py
src/simulation/dwsim_automation.py

src/sampling/03_generate_2560_sobol.py
src/sampling/04_generate_500_lhs.py

notebooks/01_Data_Quality_Check.ipynb
notebooks/02_Data_Cleaning_Preprocessing.ipynb
notebooks/03_Visualization_EDA.ipynb
notebooks/04_Model_Training.ipynb
notebooks/05_Hyperparameter_Tuning.ipynb
notebooks/06_Final_Holdout_Evaluation.ipynb
notebooks/07_Physical_Consistency_Check.ipynb
notebooks/08_Result_Plots.ipynb

data/06_physical_checks/holdout_error_metrics.csv
data/06_physical_checks/bounds_violation_summary.csv
data/06_physical_checks/final_model_selection.json

models/01_trained_models_all_5/
```

---

