
# Supply Chain Risk Prediction – ML Model Handover

## 1. Project Overview

This module predicts next-day inventory stockout risk using historical retail supply chain data.

The objective is to predict whether a product at a particular store is likely to experience a stockout on the following day.

**Prediction output:**
- 0 – No stockout predicted
- 1 – Stockout predicted

The trained model is integrated with an Agentic AI-based risk assessment and mitigation workflow.

## 2. Dataset Information

**Dataset:** FreshRetailNet-50K  
**Source:** Hugging Face – Dingdong-Inc/FreshRetailNet-50K  
**Original training data:** 4,500,000 rows × 19 columns.

The original dataset is stored in Databricks and is not included in this repository.

## 3. Target Variable Generation

The original dataset does not directly contain the next-day prediction target.

The following steps were performed:

1. Created `stockout_label`:
   - 1 if `stock_hour6_22_cnt > 0`
   - 0 otherwise.
2. Grouped records by `city_id`, `store_id`, and `product_id`.
3. Ordered records chronologically using `dt`.
4. Used Spark `lead()` to obtain the following day's stockout label.
5. Retained consecutive-day records using a one-day date-gap condition.

**Final target variable:** `next_day_stockout_label`

## 4. Model Input Features

The model uses exactly 16 raw input features.

| Feature | Data Type |
|---|---|
| city_id | Long |
| store_id | Long |
| management_group_id | Long |
| first_category_id | Long |
| second_category_id | Long |
| third_category_id | Long |
| product_id | Long |
| sale_amount | Double |
| discount | Double |
| holiday_flag | Integer |
| activity_flag | Integer |
| precpt | Double |
| avg_temperature | Double |
| avg_humidity | Double |
| avg_wind_level | Double |
| stockout_label | Integer |

The sample input file is available at:

`sample_data/sample_model_input.csv`

The sample contains 10 records and 16 raw feature columns. It does not contain the target or prediction columns.

## 5. Data Preprocessing

Preprocessing was implemented using PySpark ML Pipeline.

### Categorical features

- city_id
- store_id
- management_group_id
- first_category_id
- second_category_id
- third_category_id
- product_id
- holiday_flag
- activity_flag
- stockout_label

### Numerical features

- sale_amount
- discount
- precpt
- avg_temperature
- avg_humidity
- avg_wind_level

### Preprocessing steps

1. StringIndexer converts categorical values into numerical indices.
2. OneHotEncoder converts categorical indices into encoded vectors.
3. VectorAssembler combines categorical and numerical features.
4. The final assembled feature vector contains 2,149 dimensions.

**Unseen categorical values:** StringIndexer was configured with `handleInvalid="keep"`. Previously unseen categories are assigned an additional index bucket during transformation. The same fitted preprocessing pipeline must be reused during inference.

The fitted preprocessing PipelineModel is stored separately in Databricks.

## 6. Train, Validation and Test Split

A chronological split was used to preserve the time sequence and avoid random mixing of dates.

| Dataset | Date Range | Records |
|---|---|---:|
| Training | 2024-03-28 to 2024-05-27 | 3,050,000 |
| Validation | 2024-05-28 to 2024-06-10 | 700,000 |
| Testing | 2024-06-11 to 2024-06-24 | 700,000 |

## 7. Machine Learning Algorithm

**Algorithm:** Random Forest Classifier

Configuration:

- Number of trees: 50
- Maximum depth: 8
- Maximum bins: 32
- Random seed: 42
- Feature column: `features`
- Label column: `next_day_stockout_label`

The classification threshold was tuned using validation data. The selected threshold was 0.45.

## 8. Model Evaluation Results

Test-set evaluation at the 0.45 classification threshold:

| Metric | Result |
|---|---:|
| Accuracy | 65.24% |
| Precision | 59.33% |
| Recall | 63.94% |
| F1-score | 61.55% |

### Confusion Matrix

| | Predicted 0 | Predicted 1 |
|---|---:|---:|
| Actual 0 | 261,905 | 133,489 |
| Actual 1 | 109,839 | 194,767 |

## 9. Probability Handling

The model generates class probabilities.

The probability of class 1 represents the predicted stockout probability.

In PySpark:

```python
from pyspark.ml.functions import vector_to_array
from pyspark.sql.functions import col, when

predictions = predictions.withColumn(
    "stockout_probability",
    vector_to_array(col("probability"))[1]
)

predictions = predictions.withColumn(
    "predicted_stockout",
    when(
        col("stockout_probability") >= 0.45, 1
    ).otherwise(0)
)
```

**Important:** Class-1 probability is extracted from index `[1]` of the probability vector.

The ML classification threshold (0.45) is separate from the Agentic AI risk bands:

- Below 0.45: Low Risk
- 0.45 to below 0.70: Medium Risk
- 0.70 and above: High Risk

## 10. Databricks and MLflow Model Details

**Databricks workspace:**

https://dbc-dc0e09d2-c8cd.cloud.databricks.com

**Unity Catalog model name:**

`workspace.supply_chain_db.stockout_prediction_model`

**Registered model version:** 1

**Model status:** READY

**Registered model URI:**

```python
models:/workspace.supply_chain_db.stockout_prediction_model/1
```

**Preprocessing PipelineModel location:**

```text
/Volumes/workspace/supply_chain_db/supply_chain_data/preprocessing_model
```

Both artifacts are stored separately in Databricks.

## 11. Loading the Registered Model

Run the following in a Databricks notebook with appropriate workspace and Unity Catalog permissions.

```python
import mlflow

mlflow.set_registry_uri("databricks-uc")

registered_model_uri = (
    "models:/workspace.supply_chain_db."
    "stockout_prediction_model/1"
)

loaded_model = mlflow.spark.load_model(
    registered_model_uri,
    dfs_tmpdir=(
        "/Volumes/workspace/supply_chain_db/"
        "supply_chain_data/mlflow_tmp"
    )
)
```

## 12. Loading the Preprocessing Pipeline

```python
from pyspark.ml import PipelineModel

preprocessing_model = PipelineModel.load(
    "/Volumes/workspace/supply_chain_db/"
    "supply_chain_data/preprocessing_model"
)
```

## 13. Performing Predictions

The registered Random Forest model expects the assembled `features` vector, not the original raw columns.

Therefore, the preprocessing pipeline must be applied first.

```python
# Load raw input data
input_df = spark.read.csv(
    "/Volumes/workspace/supply_chain_db/"
    "supply_chain_data/sample_model_input.csv",
    header=True,
    inferSchema=True
)

# Apply the fitted preprocessing pipeline
prepared_df = preprocessing_model.transform(input_df)

# Generate predictions
predictions = loaded_model.transform(prepared_df)

# Extract class-1 probability
from pyspark.ml.functions import vector_to_array
from pyspark.sql.functions import col, when

predictions = predictions.withColumn(
    "stockout_probability",
    vector_to_array(col("probability"))[1]
)

predictions = predictions.withColumn(
    "predicted_stockout",
    when(
        col("stockout_probability") >= 0.45, 1
    ).otherwise(0)
)

display(
    predictions.select(
        "stockout_probability",
        "predicted_stockout"
    )
)
```

For a real integration, the input must contain all 16 raw features with compatible data types. Use the same preprocessing artifact; do not refit encoders or create a new feature transformation.

## 14. Repository Structure

```text
supply-chain-risk-mitigation/
│
├── notebooks/
│   └── 01_Phase1_Dataset_Analysis.ipynb
│
├── sample_data/
│   └── sample_model_input.csv
│
├── agent_orchestrator.py
├── app.py
├── databricks_model.py
├── mitigation_agent.py
├── read_predictions.py
├── risk_assessment_agent.py
├── risk_investigation_agent.py
├── strategy_evaluation_agent.py
├── README.md
└── .gitignore
```

## 15. Important Integration Notes

1. The preprocessing pipeline and registered ML model must both be accessible in Databricks.
2. The preprocessing pipeline must not be retrained independently during inference.
3. Input feature names and data types must match the training configuration.
4. Class-1 probability must be extracted using index `[1]`.
5. The model classification threshold is 0.45.
6. Databricks workspace and Unity Catalog permissions are required.
7. Do not upload credentials, access tokens, `.env` files or the complete original dataset to GitHub.
8. The registered model and preprocessing pipeline are maintained in Databricks rather than committed as large binary files.

## 16. Python Scripts

- `app.py` – Streamlit dashboard.
- `agent_orchestrator.py` – Coordinates the risk-management workflow.
- `risk_assessment_agent.py` – Assigns stockout risk levels.
- `risk_investigation_agent.py` – Examines available product and sales context.
- `mitigation_agent.py` – Recommends corrective actions.
- `strategy_evaluation_agent.py` – Ranks mitigation strategies using heuristic priority scores.
- `databricks_model.py` – Databricks model integration.
- `read_predictions.py` – Retrieves prediction data from Databricks.

The current mitigation and strategy components use rule-based logic and heuristic scores. Their scores should not be interpreted as measured probabilities of success.

---

**End of ML Model Handover**
