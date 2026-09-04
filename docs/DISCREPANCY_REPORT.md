# DISCREPANCY REPORT: LAKEHOUSE VS NOTEBOOK

## 1. Current Lakehouse Configuration

### 1.1 ML Configuration (from `backend/ml/train.py`)

```python
RANDOM_STATE = 42
TEST_SIZE = 0.20
N_SPLITS = 10
PREPROCESSING = []  # No StandardScaler

FEATURE_COLUMNS = [
    "jk_enc",
    "angkatan",
    "ip",
    "ipk",
    "total_sks",
    "jumlah_mk",
    "sks_seharusnya",
    "selisih_sks",
]

TARGET_COLUMN = "label"
IDENTIFIER_COLUMN = "id_mahasiswa"
POSITIVE_CLASS = 1  # Terlambat
```

### 1.2 Current Lakehouse Results

**Without SMOTE:**
- CV Accuracy: 0.7200 (mean)
- Holdout Accuracy: 0.7308
- Precision: 0.9243
- Recall: 0.7216
- F1: 0.8105
- Training rows: 15,599

**With SMOTE:**
- CV Accuracy: 0.6649 (mean)
- Holdout Accuracy: 0.6785
- Precision: 0.9471
- Recall: 0.6324
- F1: 0.7584
- Training rows: 15,599

### 1.3 Current Inference Results

- Inference population: 12,501 students (AKTIF 2022-2024)
- Angkatan 2022: 4,109
- Angkatan 2023: 4,046
- Angkatan 2024: 4,346

---

## 2. Baseline IPYNB Configuration

### 2.1 Expected ML Configuration

Based on the task description, the notebook uses:

```python
# Expected configuration
test_size = 0.20
random_state = 42
n_splits = 10
scoring = 'accuracy'

# Features (8 features)
features = [
    "jenis_kelamin",  # NOT jk_enc
    "angkatan",
    "ip",
    "ipk",
    "total_sks",
    "jumlah_mk",
    "sks_seharusnya",
    "selisih_sks",
]

# Label logic
# LULUS + lama_studi <= 4 → Tepat Waktu (0)
# LULUS + lama_studi > 4 → Terlambat (1)
# AKTIF 2019-2021 → Terlambat (1)
# AKTIF 2022-2024 → NULL (inference only)
```

### 2.2 Baseline IPYNB Results

**Without SMOTE:**
- CV Accuracy: 0.7456
- Accuracy: 0.7319
- Precision: 0.8752
- Recall: 0.7552
- F1: 0.8108

**With SMOTE:**
- CV Accuracy: 0.6858
- Accuracy: 0.6606
- Precision: 0.9100
- Recall: 0.6147
- F1: 0.7337

### 2.3 Baseline Inference Results

- Inference population: 12,244 students (AKTIF 2022-2024)
- Angkatan 2022: 3,987
- Angkatan 2023: 3,985
- Angkatan 2024: 4,272

---

## 3. IDENTIFIED DISCREPANCIES

### 3.1 FEATURE NAME MISMATCH (CRITICAL)

**Issue:** The notebook uses `jenis_kelamin` as a feature, but the Lakehouse uses `jk_enc`.

**Notebook:**
```python
features = ["jenis_kelamin", "angkatan", "ip", "ipk", ...]
# jenis_kelamin is likely encoded as integer (0/1) or string
```

**Lakehouse:**
```python
FEATURE_COLUMNS = ["jk_enc", "angkatan", "ip", "ipk", ...]
# jk_enc is derived fromjenis_kelamin using encoding
```

**Impact:** This is a MAJOR discrepancy. The notebook might be using the raw `jenis_kelamin` column directly (which could be string or already encoded), while the Lakehouse creates a new column `jk_enc` through encoding.

**Root Cause:** The notebook might have pre-encoded `jenis_kelamin` to integer in earlier steps, or it might be using a different encoding method.

### 3.2 INFERENCE POPULATION MISMATCH

**Issue:** The inference population differs significantly.

| Angkatan | Notebook | Lakehouse | Difference |
|---|---:|---:|---:|
| 2022 | 3,987 | 4,109 | +122 |
| 2023 | 3,985 | 4,046 | +61 |
| 2024 | 4,272 | 4,346 | +74 |
| **Total** | **12,244** | **12,501** | **+257** |

**Root Cause:** This was identified in the previous task. The Lakehouse added imputation for students without KHS (ip = ipk), which added 257 students back to the inference population.

**Impact:** The notebook's inference results (12,244 students) cannot be directly compared to the Lakehouse results (12,501 students).

### 3.3 METRIC DIFFERENCES

| Metric | Without SMOTE | | With SMOTE | |
|---|---:|---:|---:|---:|
| | Lakehouse | Notebook | Lakehouse | Notebook |
| CV Accuracy | 0.7200 | 0.7456 | 0.6649 | 0.6858 |
| Accuracy | 0.7308 | 0.7319 | 0.6785 | 0.6606 |
| Precision | 0.9243 | 0.8752 | 0.9471 | 0.9100 |
| Recall | 0.7216 | 0.7552 | 0.6324 | 0.6147 |
| F1 | 0.8105 | 0.8108 | 0.7584 | 0.7337 |

**Observations:**
1. CV Accuracy is lower in Lakehouse (-0.0256 without SMOTE, -0.0209 with SMOTE)
2. Precision is higher in Lakehouse (+0.0491 without SMOTE, +0.0371 with SMOTE)
3. Recall is lower in Lakehouse (-0.0336 without SMOTE, +0.0177 with SMOTE)
4. F1 is nearly identical without SMOTE (-0.0003), higher with SMOTE (+0.0247)

### 3.4 KHS AGGREGATION METHOD

**Issue:** The way IP (Indeks Prestasi) is aggregated from KHS records might differ.

**Lakehouse (gold_fact_khs.py):**
```python
df = df.groupBy("id_mahasiswa").agg(
    F.first("ip", ignorenulls=True).alias("ip"),
    F.first("sks", ignorenulls=True).alias("sks"),
    F.count("*").alias("jumlah_data_khs"),
)
```

**Potential Notebook Approach:**
- Could be using `mean(ip)` instead of `first(ip)`
- Could be using the latest semester's IP
- Could be using a different aggregation method

**Impact:** This could affect the `ip` feature values, which would impact model performance.

### 3.5 LABEL LOGIC FOR AKTIF 2019-2021

**Issue:** The notebook might handle AKTIF students from 2019-2021 differently.

**Lakehouse (gold_mahasiswa.py):**
```python
# status_kelulusan for AKTIF 2019-2021
.when(
    (F.upper(F.trim(F.col("status_mahasiswa"))) == "AKTIF")
    & (F.col("angkatan").isin(2019, 2020, 2021)),
    F.lit("Terlambat"),
)
```

**Potential Notebook Approach:**
- Might not include AKTIF 2019-2021 in training data
- Might use a different label for these students
- Might filter them out entirely

**Impact:** If the notebook doesn't include AKTIF 2019-2021 in training, the training dataset size would be different.

### 3.6 TRAINING DATASET SIZE

**Issue:** The training dataset size might differ.

**Lakehouse:** 15,599 rows
**Notebook:** Unknown (needs verification)

**Potential Causes:**
- Different filtering for LULUS students
- Different handling of AKTIF 2019-2021
- Different missing value handling
- Different duplicate removal

---

## 4. ROOT CAUSE ANALYSIS

### 4.1 Primary Root Causes

1. **Feature Name Mismatch (jenis_kelamin vs jk_enc)**
   - The notebook likely uses `jenis_kelamin` directly (already encoded or as string)
   - The Lakehouse creates `jk_enc` through encoding
   - This could affect how the model interprets the feature

2. **KHS Aggregation Method**
   - Lakehouse uses `first(ip, ignorenulls=True)` which takes the first non-null IP
   - Notebook might use `mean(ip)` or `last(ip)` or a different aggregation
   - This affects the `ip` feature values

3. **Inference Population Difference**
   - Lakehouse added 257 students through imputation (ip = ipk)
   - Notebook uses 12,244 students without this imputation
   - Direct comparison of inference results is not valid

4. **Label Logic for AKTIF 2019-2021**
   - Lakehouse includes AKTIF 2019-2021 as labeled data (Terlambat)
   - Notebook might exclude them or use different logic
   - This affects training dataset composition

### 4.2 Secondary Root Causes

1. **Random State and Split Configuration**
   - Both use random_state=42, test_size=0.20
   - But if training data is different, splits will be different

2. **SMOTE Implementation**
   - Lakehouse uses imblearn's SMOTE
   - Notebook might use a different SMOTE implementation

3. **Cross Validation Configuration**
   - Both use StratifiedKFold with n_splits=10
   - But if data is different, CV folds will be different

---

## 5. RECOMMENDED INVESTIGATION STEPS

### 5.1 Verify Notebook Configuration

1. **Check feature names:**
   - Does notebook use `jenis_kelamin` or `jk_enc`?
   - How is `jenis_kelamin` encoded in the notebook?

2. **Check KHS aggregation:**
   - How does notebook calculate `ip` from KHS records?
   - Is it `mean(ip)`, `first(ip)`, `last(ip)`, or something else?

3. **Check training data filtering:**
   - Does notebook include AKTIF 2019-2021 in training?
   - What label is assigned to AKTIF 2019-2021?

4. **Check inference population:**
   - How does notebook filter AKTIF 2022-2024?
   - Does it include students without KHS records?

### 5.2 Verify Lakehouse Implementation

1. **Check Gold Layer:**
   - Verify `ip` aggregation in `gold_fact_khs.py`
   - Verify label logic for AKTIF 2019-2021 in `gold_mahasiswa.py`

2. **Check Feature Store:**
   - Verify feature engineering in `feature_engineering.py`
   - Verify training dataset creation in `training_dataset.py`
   - Verify inference dataset creation in `inference_dataset.py`

3. **Check ML Pipeline:**
   - Verify feature columns in `data_preparation.py`
   - Verify train/test split in `train.py`
   - Verify model training in `train.py`

---

## 6. ACTION ITEMS

### 6.1 Immediate Actions

1. **Locate and examine the notebook file**
   - Find `bronze-silver-gold (22-24).ipynb`
   - Extract actual ML configuration

2. **Compare feature engineering**
   - Check how `jenis_kelamin` is handled in notebook
   - Check how `ip` is aggregated from KHS in notebook

3. **Compare training data filtering**
   - Check how notebook filters LULUS students
   - Check how notebook handles AKTIF 2019-2021

4. **Compare inference population**
   - Check how notebook filters AKTIF 2022-2024
   - Check if notebook includes students without KHS

### 6.2 Fix Actions (if needed)

1. **Feature Name Alignment**
   - If notebook uses `jenis_kelamin`, change Lakehouse to use same
   - If notebook uses `jk_enc`, keep Lakehouse as is

2. **KHS Aggregation Alignment**
   - Change `gold_fact_khs.py` to match notebook's aggregation method

3. **Label Logic Alignment**
   - Change `gold_mahasiswa.py` to match notebook's label logic

4. **Inference Population Alignment**
   - Change `inference_dataset.py` to match notebook's filtering

---

## 7. CONCLUSION

The primary discrepancies between the Lakehouse and Notebook are:

1. **Feature name mismatch** (`jenis_kelamin` vs `jk_enc`)
2. **KHS aggregation method** (`first(ip)` vs potential `mean(ip)`)
3. **Inference population** (12,501 vs 12,244 students)
4. **Label logic for AKTIF 2019-2021**

To reconcile the Lakehouse with the Notebook, we need to:

1. **Locate and examine the actual notebook file**
2. **Extract the exact ML configuration from the notebook**
3. **Align the Lakehouse implementation with the notebook configuration**
4. **Re-run the pipeline and validate results**

The metric differences (CV Accuracy, Precision, Recall, F1) are likely caused by these configuration differences, not by random variation or library versions.

---

*Report generated: 2026-09-02*
*Pipeline Version: v4.0.0*
*Status: AWAITING NOTEBOOK VERIFICATION*
