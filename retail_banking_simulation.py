# ============================================================
# RETAIL BANKING PORTFOLIO SIMULATION
# Controlled Realism v5.2
# ============================================================

import pandas as pd
import numpy as np
import os

np.random.seed(42)

# ------------------------------------------------------------
# Project Paths
# ------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)

print("Environment initialised successfully.")
print("Data directory:", DATA_DIR)

# ============================================================
# GLOBAL CONFIGURATION — FROZEN SPEC v5.2
# ============================================================

N_CUSTOMERS = 50_000
N_BRANCHES = 15
YEARS = [2021, 2022, 2023, 2024]
MONTHS_ON_BOOK = 12

# Macro economic risk multiplier
macro_risk = {
    2021: 1.0,
    2022: 1.0,
    2023: 1.4,
    2024: 1.1
}


np.random.seed(42)

print("Configuration loaded.")
print("Customers:", N_CUSTOMERS)
print("Branches:", N_BRANCHES)


# ============================================================
# STEP 1: CREATE dim_branch
# ============================================================

branch_data = [

    # Low Risk (Urban) — 4 branches
    ("BR01", "Low Risk", 0.85, 0.006, 1.40, "Urban"),
    ("BR02", "Low Risk", 0.85, 0.006, 1.40, "Urban"),
    ("BR03", "Low Risk", 0.85, 0.006, 1.40, "Urban"),
    ("BR04", "Low Risk", 0.85, 0.006, 1.40, "Urban"),

    # Normal (Semi-Urban) — 6 branches
    ("BR05", "Normal", 1.00, 0.010, 1.00, "Semi-Urban"),
    ("BR06", "Normal", 1.00, 0.010, 1.00, "Semi-Urban"),
    ("BR07", "Normal", 1.00, 0.010, 1.00, "Semi-Urban"),
    ("BR08", "Normal", 1.00, 0.010, 1.00, "Semi-Urban"),
    ("BR09", "Normal", 1.00, 0.010, 1.00, "Semi-Urban"),
    ("BR10", "Normal", 1.00, 0.010, 1.00, "Semi-Urban"),

    # High Risk (Rural) — 4 branches
    ("BR11", "High Risk", 1.20, 0.015, 0.90, "Rural"),
    ("BR12", "High Risk", 1.20, 0.015, 0.90, "Rural"),
    ("BR13", "High Risk", 1.20, 0.015, 0.90, "Rural"),
    ("BR14", "High Risk", 1.20, 0.015, 0.90, "Rural"),

    # Stress (Rural) — 1 branch
    ("BR15", "Stress", 1.35, 0.020, 1.20, "Rural"),
]

dim_branch = pd.DataFrame(
    branch_data,
    columns=[
        "branch_id",
        "branch_group",
        "branch_risk_factor",
        "override_rate",
        "exposure_multiplier",
        "region_type"
    ]
)

print("\ndim_branch created.")
print(dim_branch.head())
print("Total branches:", len(dim_branch))


# ============================================================
# STEP 2: CREATE dim_customer
# ============================================================

# Generate customer IDs
customer_ids = np.arange(1, N_CUSTOMERS + 1)

# Assign branches randomly
branch_ids = np.random.choice(
    dim_branch["branch_id"],
    size=N_CUSTOMERS,
    p=[0.10,0.10,0.10,0.10, 
       0.07,0.07,0.07,0.07,0.07,0.07,
       0.04,0.04,0.04,0.04,
       0.02]
)



# Segment distribution logic (based on branch group)
segment_distribution = {
    "Low Risk":  [0.15, 0.35, 0.30, 0.20],
    "Normal":    [0.20, 0.35, 0.25, 0.20],
    "High Risk": [0.25, 0.30, 0.25, 0.20],
    "Stress":    [0.40, 0.30, 0.20, 0.10],
}

segments = []

for b in branch_ids:
    group = dim_branch.loc[dim_branch["branch_id"] == b, "branch_group"].values[0]
    seg = np.random.choice(["A", "B", "C", "D"], p=segment_distribution[group])
    segments.append(seg)

segments = np.array(segments)

# Credit score generation (realistic portfolio distribution)

score_band = np.random.choice(
    ["subprime", "near_prime", "prime", "super_prime"],
    size=N_CUSTOMERS,
    p=[0.08, 0.22, 0.40, 0.30]
)

credit_scores = []

for band in score_band:

    if band == "subprime":
        score = np.random.randint(300, 580)

    elif band == "near_prime":
        score = np.random.randint(580, 660)

    elif band == "prime":
        score = np.random.randint(660, 740)

    else:
        score = np.random.randint(740, 849)

    credit_scores.append(score)

credit_scores = np.array(credit_scores)

dim_customer = pd.DataFrame({
    "customer_id": customer_ids,
    "branch_id": branch_ids,
    "customer_segment": segments,
    "credit_score": credit_scores
})

# Introduce 1% duplicate customers (KYC duplication)
dup_count = int(0.01 * N_CUSTOMERS)
dup_rows = dim_customer.sample(dup_count, random_state=42)
dim_customer = pd.concat([dim_customer, dup_rows], ignore_index=True)

print("\ndim_customer created.")
print("Total rows (including duplicates):", len(dim_customer))
print("Unique customers:", dim_customer["customer_id"].nunique())




# ============================================================
# STEP 3: CREATE dim_time
# ============================================================

time_records = []

for y in YEARS:
    for m in range(1, 13):
        time_records.append({
            "time_id": f"{y}{str(m).zfill(2)}",
            "year": y,
            "month": m,
            "quarter": (m - 1) // 3 + 1
        })

dim_time = pd.DataFrame(time_records)

print("\ndim_time created.")
print(dim_time.head())
print("Total rows:", len(dim_time))



# ============================================================
# STEP 4: FACT_LOANS CREATION (FINAL CLEAN VERSION)
# ============================================================


# ---------------- Controlled loans per customer ----------------

customer_ids = dim_customer["customer_id"].drop_duplicates().values

loan_customer_list = []

for cid in customer_ids:

    loans_per_customer = min(np.random.poisson(1.5) + 1, 5)

    loan_customer_list.extend([cid] * loans_per_customer)

cust_sample = np.array(loan_customer_list)

N_LOANS = len(cust_sample)

loan_ids = np.array([f"LN{str(i).zfill(8)}" for i in range(1, N_LOANS + 1)])

# Efficient mapping
# Use unique customer table to avoid duplicate index expansion
customer_unique = dim_customer.drop_duplicates("customer_id")
cust_map = customer_unique.set_index("customer_id")

branch_sample = cust_map.loc[cust_sample, "branch_id"].values
segment_sample = cust_map.loc[cust_sample, "customer_segment"].values
credit_scores = cust_map.loc[cust_sample, "credit_score"].values

# ----------------  Year Distribution ----------------
years = np.random.choice(
    [2021, 2022, 2023, 2024],
    size=N_LOANS,
    p=[0.15, 0.20, 0.30, 0.35]
)

# ----------------  Origination Month ----------------
origination_months = np.random.choice(
    range(1,13),
    size=N_LOANS,
    p=[0.05,0.06,0.10,0.07,0.06,0.07,0.08,0.08,0.10,0.11,0.12,0.10]
)

# ---------------- Vectorised Time ID Lookup ----------------
time_lookup = dim_time.set_index(["year", "month"])["time_id"]
time_key = pd.MultiIndex.from_arrays([years, origination_months])
time_ids = time_lookup.loc[time_key].values

# ---------------- Loan Type ----------------
loan_types = np.random.choice(
    ["Home", "Personal", "Auto", "Business", "Education"],
    size=N_LOANS,
    p=[0.30, 0.25, 0.20, 0.15, 0.10]
)

# ---------------- Base Loan Amount ----------------
base_amount_map = {
    "Home": (500000, 5000000),
    "Personal": (50000, 500000),
    "Auto": (200000, 1500000),
    "Business": (300000, 3000000),
    "Education": (100000, 800000),
}

loan_amounts = np.array([
    np.random.randint(*base_amount_map[lt]) for lt in loan_types
])

# ---------------- Branch Parameters ----------------
branch_params = dim_branch.set_index("branch_id")

branch_risk = branch_params.loc[branch_sample, "branch_risk_factor"].values
override_rate = branch_params.loc[branch_sample, "override_rate"].values
exposure_multiplier = branch_params.loc[branch_sample, "exposure_multiplier"].values
region_type = branch_params.loc[branch_sample, "region_type"].values

# ---------------- Exposure Skew ----------------
loan_amounts = loan_amounts * exposure_multiplier

# ---------------- PD Model ----------------
base_pd = np.select(
    [
        credit_scores < 600,
        (credit_scores >= 600) & (credit_scores < 700),
        (credit_scores >= 700) & (credit_scores < 780),
        credit_scores >= 780
    ],
    [0.14, 0.07, 0.03, 0.01]
)

segment_multiplier = np.where(segment_sample == "A", 1.3, 1.0)

PD = base_pd * segment_multiplier * branch_risk
PD = np.clip(PD, 0.005, 0.40)

# ---------------- PD Override ----------------
override_flags = np.random.rand(N_LOANS) < override_rate
override_reduction = np.random.uniform(0.10, 0.30, N_LOANS)

PD[override_flags] *= (1 - override_reduction[override_flags])
PD = np.clip(PD, 0.005, 0.40)

# ---------------- Interest Rate ----------------
rate_ranges = {
    "Home": (8, 10),
    "Personal": (13, 18),
    "Auto": (10, 13),
    "Business": (11, 15),
    "Education": (9, 12)
}

interest_rates = np.array([
    np.random.uniform(*rate_ranges[lt]) for lt in loan_types
])

# ---------------- LGD ----------------
lgd_base = {
    "Home": 0.30,
    "Personal": 0.75,
    "Auto": 0.45,
    "Business": 0.60,
    "Education": 0.55
}

LGD = np.array([lgd_base[lt] for lt in loan_types])

region_multiplier = np.where(
    region_type == "Urban", 0.85,
    np.where(region_type == "Semi-Urban", 1.00, 1.15)
)

LGD = LGD * region_multiplier
LGD = np.clip(LGD, 0, 0.95)

# ---------------- EAD ----------------
EAD = loan_amounts * np.random.uniform(0.85, 1.00, N_LOANS)

# 1.5% anomaly
anomaly_mask = np.random.rand(N_LOANS) < 0.015
EAD[anomaly_mask] = loan_amounts[anomaly_mask] * 1.05

# ---------------- Expected Loss ----------------
expected_loss = PD * LGD * EAD

# ---------------- Collateral ----------------
collateral_value = loan_amounts * np.random.uniform(0.8, 1.5, N_LOANS)

missing_mask = np.random.rand(N_LOANS) < 0.025
collateral_value[missing_mask] = np.nan

# ---------------- Create DataFrame ----------------
fact_loans = pd.DataFrame({
    "loan_id": loan_ids,
    "customer_id": cust_sample,
    "branch_id": branch_sample,
    "time_id": time_ids,
    "origination_year": years,
    "origination_month": origination_months,
    "loan_type": loan_types,
    "loan_amount": loan_amounts,
    "interest_rate": interest_rates,
    "PD": PD,
    "LGD": LGD,
    "EAD": EAD,
    "expected_loss": expected_loss,
    "collateral_value": collateral_value,
    "pd_override_flag": override_flags.astype(int),
    "branch_risk_factor": branch_risk   # ← ADD THIS
})




# ============================================================
# STEP 5: TRANSITION ENGINE (FINAL FROZEN VERSION)
# ============================================================

# STEP 5: TRANSITION ENGINE

# Required columns in fact_loans:
# loan_id, PD, branch_risk_factor, origination_year, origination_month

branch_risk = fact_loans["branch_risk_factor"].values
pd_factor = fact_loans["PD"].values

current_state = np.array(["Current"] * N_LOANS)
migration_frames = []

year_factor = fact_loans["origination_year"].map(macro_risk).values

for month in range(1, MONTHS_ON_BOOK + 1):

    next_state = current_state.copy()

    monthly_noise = np.random.normal(1.0, 0.08, N_LOANS)
    monthly_noise = np.clip(monthly_noise, 0.85, 1.15)



    # Independent random draws
    rand_entry = np.random.rand(N_LOANS)
    rand_cure  = np.random.rand(N_LOANS)
    rand_esc   = np.random.rand(N_LOANS)
    rand_rec   = np.random.rand(N_LOANS)

    # ---------------- CURRENT → 30DPD ----------------
    mask_current = current_state == "Current"

    prob_30 = pd_factor * 0.45 * branch_risk * year_factor * monthly_noise
    prob_30 = np.clip(prob_30, 0, 0.12)

    next_state[mask_current & (rand_entry < prob_30)] = "30DPD"

    # ---------------- 30DPD ----------------
    mask_30 = current_state == "30DPD"

    cure_30 = 0.48
    
    esc_30 = (0.12 + 0.25 * pd_factor) * branch_risk * year_factor * monthly_noise
    esc_30 = np.clip(esc_30, 0, 0.30)

    next_state[mask_30 & (rand_cure < cure_30)] = "Current"
    next_state[mask_30 & (rand_cure >= cure_30) &
               (rand_esc < esc_30)] = "60DPD"

    # ---------------- 60DPD ----------------
    mask_60 = current_state == "60DPD"

    cure_60 = 0.25
    
    esc_60 = (0.22 + 0.35 * pd_factor) * branch_risk * year_factor * monthly_noise
    esc_60 = np.clip(esc_60, 0, 0.35)

    next_state[mask_60 & (rand_cure < cure_60)] = "30DPD"
    next_state[mask_60 & (rand_cure >= cure_60) &
               (rand_esc < esc_60)] = "90DPD"

    # ---------------- 90DPD ----------------
    mask_90 = current_state == "90DPD"

    cure_90 = 0.07
    esc_90 = (0.35 + 0.50 * pd_factor) * branch_risk * year_factor * monthly_noise
    esc_90 = np.clip(esc_90, 0, 0.55)

    next_state[mask_90 & (rand_cure < cure_90)] = "60DPD"
    next_state[mask_90 & (rand_cure >= cure_90) &
               (rand_esc < esc_90)] = "NPA"

    # ---------------- NPA ----------------
    mask_npa = current_state == "NPA"

    recovery_rate = 0.01  # behavioural recovery
    next_state[mask_npa & (rand_rec < recovery_rate)] = "90DPD"
    next_state[mask_npa & (rand_rec >= recovery_rate)] = "NPA"

    # Store month snapshot
    month_df = pd.DataFrame({
        "loan_id": fact_loans["loan_id"].values,
        "month_number": month,
        "state": next_state
    })

    migration_frames.append(month_df)
    current_state = next_state


# Combine all months
fact_loan_states = pd.concat(migration_frames, ignore_index=True)


# ============================================================
# REPORTING DATE (CALENDAR-CORRECT, VECTORISED, SAFE)
# ============================================================

fact_loan_states = fact_loan_states.merge(
    fact_loans[["loan_id", "origination_year", "origination_month"]],
    on="loan_id",
    how="left"
)

base_dates = pd.to_datetime(
    dict(
        year=fact_loan_states["origination_year"],
        month=fact_loan_states["origination_month"],
        day=1
    )
)

fact_loan_states["reporting_date"] = (
    base_dates.dt.to_period("M")
    + (fact_loan_states["month_number"] - 1)
).dt.to_timestamp()


print("Transition engine complete.")
print("Total migration rows:", len(fact_loan_states))

# ============================================================
# VALIDATION 1 — STRUCTURAL CHECKS
# ============================================================

print("\nUnique loans in migration:",
      fact_loan_states["loan_id"].nunique())

print("Expected loans:", N_LOANS)

rows_per_loan = fact_loan_states.groupby("loan_id").size()

print("Min rows per loan:", rows_per_loan.min())
print("Max rows per loan:", rows_per_loan.max())


print("\nUnique states:", fact_loan_states["state"].unique())
print("Null states:", fact_loan_states["state"].isna().sum())



state_dist = (
    fact_loan_states
    .groupby(["month_number", "state"])
    .size()
    .unstack(fill_value=0)
)

state_pct = state_dist.div(state_dist.sum(axis=1), axis=0)

print("\nState distribution by month (%):")
print(state_pct.round(3))



from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://postgres:Jayakrishnan51200@localhost:5432/retail_banking"
)

print("Connected to PostgreSQL.")

dim_branch.to_sql("dim_branch", engine, if_exists="replace", index=False)
dim_customer.to_sql("dim_customer", engine, if_exists="replace", index=False)
dim_time.to_sql("dim_time", engine, if_exists="replace", index=False)
fact_loans.to_sql("fact_loans", engine, if_exists="replace", index=False)
fact_loan_states.to_sql(
    "fact_loan_states",
    engine,
    if_exists="replace",
    index=False,
    chunksize=50000
)

print("All tables pushed successfully.")