# -*- coding: utf-8 -*-

"""
Train Linear Regression score models for ASR speaking assessment.

This file will:
1. Load score labels and extracted ASR features.
2. Merge fluency, lexical, pronunciation and grammar features.
3. Train and evaluate five separate targets with 5-fold CV:
   - fluency: only fluency features
   - lexical: only lexical features
   - pronunciation: only pronunciation features
   - grammar: only grammar features
   - overall: all features from fluency + lexical + pronunciation + grammar
4. Export CV metrics and predictions.
5. Export Linear Regression coefficients.
6. Train final models on the full dataset.
7. Save final Linear Regression models and backend configuration files.
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# ============================================
# PROJECT ROOT DIRECTORY
# ============================================

BASE_DIR = Path(__file__).resolve().parents[2]


# ============================================
# DATA DIRECTORY
# ============================================

DATA_DIR = BASE_DIR / "data"


# ============================================
# DATA FILES
# ============================================

SCORES_FILE = DATA_DIR / "averaged_scores_by_filename.xlsx"

FLUENCY_FILE = DATA_DIR / "fluency.csv"
PRON_FILE = DATA_DIR / "pronunciation.csv"

LEX_SOPH_FILE = DATA_DIR / "lexical_sophistication.csv"
LEX_DIV_FILE = DATA_DIR / "lexical_diversity.csv"

GRAMMAR_FILE = DATA_DIR / "grammar.csv"


# ============================================
# OUTPUT DIRECTORIES
# ============================================

MODEL_DIR = BASE_DIR / "ml_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================
# TRAINING CONFIGURATION
# ============================================

N_SPLITS = 5
RANDOM_STATE = 42


# ============================================
# 1. HELPER FUNCTIONS
# ============================================

def round_half(x):
    """
    Round score to nearest 0.5 band.
    """
    x = np.asarray(x, dtype=float)
    x = np.clip(x, 0, 9)
    return np.round(x * 2) / 2


def clip_score(y_pred):
    """
    Linear Regression can predict values outside 0-9.
    This keeps predictions inside IELTS score range.
    """
    return np.clip(y_pred, 0, 9)


def rmse(y_true, y_pred):
    """
    Root Mean Squared Error.
    """
    return np.sqrt(mean_squared_error(y_true, y_pred))


def qwk_half_band(y_true, y_pred):
    """
    Quadratic Weighted Kappa for IELTS band 0.0 -> 9.0 step 0.5.
    """
    y_true = round_half(y_true)
    y_pred = round_half(y_pred)

    y_true = (y_true * 2).astype(int)
    y_pred = (y_pred * 2).astype(int)

    n = 19
    observed = np.zeros((n, n), dtype=float)

    for actual_value, predicted_value in zip(y_true, y_pred):
        observed[actual_value, predicted_value] += 1

    hist_true = np.bincount(y_true, minlength=n)
    hist_pred = np.bincount(y_pred, minlength=n)

    expected = np.outer(hist_true, hist_pred) / len(y_true)

    weights = np.zeros((n, n), dtype=float)

    for i in range(n):
        for j in range(n):
            weights[i, j] = ((i - j) ** 2) / ((n - 1) ** 2)

    denominator = np.sum(weights * expected)

    if denominator == 0:
        return np.nan

    return 1 - np.sum(weights * observed) / denominator


def check_file_exists(file_path):
    """
    Check whether an input file exists.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")


def read_csv_auto(file_path):
    """
    Read csv with automatic separator detection.
    This helps when csv uses comma or semicolon.
    """
    encodings = ["utf-8-sig", "utf-8", "latin1"]

    last_error = None

    for encoding in encodings:
        try:
            return pd.read_csv(
                file_path,
                sep=None,
                engine="python",
                encoding=encoding,
            )
        except Exception as e:
            last_error = e

    raise last_error


def to_numeric_clean(series):
    """
    Convert numeric column safely.
    Supports decimal comma, for example:
        0,333333 -> 0.333333
    """
    return pd.to_numeric(
        series.astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )


def extract_file_name_number(df, source_col="file"):
    """
    Extract numeric file_name from file column.

    Examples:
        1_prob.csv  -> 1
        1_gram.csv  -> 1
        36_gram.csv -> 36
    """
    df = df.copy()

    df["file_name"] = (
        df[source_col]
        .astype(str)
        .str.extract(r"(\d+)")[0]
    )

    df["file_name"] = pd.to_numeric(
        df["file_name"],
        errors="coerce",
    ).astype("Int64")

    return df


def create_model():
    """
    Create Linear Regression model.

    StandardScaler is used so coefficients are easier to compare.
    """
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("regressor", LinearRegression()),
        ]
    )


def get_coefficients(model, feature_names):
    """
    Extract coefficients from Linear Regression pipeline.
    Coefficients are based on standardized features.
    """
    regressor = model.named_steps["regressor"]

    coef_df = pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient": regressor.coef_,
        }
    )

    coef_df["abs_coefficient"] = coef_df["coefficient"].abs()

    coef_df = coef_df.sort_values(
        "abs_coefficient",
        ascending=False,
    )

    return coef_df


def find_score_column(score_df, target_name, candidates):
    """
    Find target score column from several possible names.
    """
    for col in candidates:
        if col in score_df.columns:
            return col

    raise ValueError(
        f"Cannot find score column for target '{target_name}'. "
        f"Expected one of: {candidates}"
    )


# ============================================
# 2. CHECK INPUT FILES
# ============================================

for file_path in [
    SCORES_FILE,
    FLUENCY_FILE,
    PRON_FILE,
    LEX_SOPH_FILE,
    LEX_DIV_FILE,
    GRAMMAR_FILE,
]:
    check_file_exists(file_path)

print("===== INPUT FILES FOUND =====")
print("Scores:", SCORES_FILE)
print("Fluency:", FLUENCY_FILE)
print("Pronunciation:", PRON_FILE)
print("Lexical sophistication:", LEX_SOPH_FILE)
print("Lexical diversity:", LEX_DIV_FILE)
print("Grammar:", GRAMMAR_FILE)


# ============================================
# 3. LOAD SCORE FILE
# ============================================

score_df = pd.read_excel(SCORES_FILE)

score_df["class_name"] = score_df["class_name"].astype(str)

score_df["file_name"] = pd.to_numeric(
    score_df["file_name"],
    errors="coerce",
).astype("Int64")


# ============================================
# 4. DETECT TARGET SCORE COLUMNS
# ============================================

target_columns = {
    "fluency": find_score_column(
        score_df,
        "fluency",
        ["avg_fluency", "fluency_score"],
    ),
    "lexical": find_score_column(
        score_df,
        "lexical",
        ["avg_lexical", "lexical_score"],
    ),
    "pronunciation": find_score_column(
        score_df,
        "pronunciation",
        ["avg_pronunciation", "pronunciation_score"],
    ),
    "grammar": find_score_column(
        score_df,
        "grammar",
        ["avg_grammar", "grammar_score"],
    ),
    "overall": find_score_column(
        score_df,
        "overall",
        ["avg_overall", "overall_score"],
    ),
}

print("\n===== TARGET COLUMNS =====")
print(target_columns)


# ============================================
# 5. LOAD FLUENCY FEATURES
# ============================================

fluency_df = read_csv_auto(FLUENCY_FILE)

fluency_df["class_name"] = fluency_df["class_name"].astype(str)
fluency_df = extract_file_name_number(fluency_df, source_col="file")

fluency_keep_cols = [
    "class_name",
    "file_name",
    "speech_rate_wps",
    "ratio_pauses_to_duration",
]

fluency_df = fluency_df[fluency_keep_cols].copy()

fluency_df = fluency_df.rename(
    columns={
        "speech_rate_wps": "flu_speech_rate",
        "ratio_pauses_to_duration": "flu_pause_ratio",
    }
)


# ============================================
# 6. LOAD LEXICAL DIVERSITY FEATURES
# ============================================

lex_div_df = read_csv_auto(LEX_DIV_FILE)

lex_div_df["class_name"] = lex_div_df["class_name"].astype(str)
lex_div_df = extract_file_name_number(lex_div_df, source_col="file")

lex_div_keep_cols = [
    "class_name",
    "file_name",
    "TTR",
    "MSTTR",
]

lex_div_df = lex_div_df[lex_div_keep_cols].copy()


# ============================================
# 7. LOAD LEXICAL SOPHISTICATION FEATURES
# ============================================

lex_soph_df = read_csv_auto(LEX_SOPH_FILE)

lex_soph_df["class_name"] = lex_soph_df["class_name"].astype(str)
lex_soph_df = extract_file_name_number(lex_soph_df, source_col="file")

lex_soph_keep_cols = [
    "class_name",
    "file_name",
    "A1",
    "A2",
    "B1",
    "B2",
    "C1",
]

lex_soph_df = lex_soph_df[lex_soph_keep_cols].copy()


# ============================================
# 8. MERGE LEXICAL DIVERSITY + SOPHISTICATION
# ============================================

lex_df = lex_div_df.merge(
    lex_soph_df,
    on=["class_name", "file_name"],
    how="inner",
)

lex_df = lex_df.rename(
    columns={
        "TTR": "lex_TTR",
        "MSTTR": "lex_MSTTR",
        "A1": "lex_A1",
        "A2": "lex_A2",
        "B1": "lex_B1",
        "B2": "lex_B2",
        "C1": "lex_C1",
    }
)


# ============================================
# 9. LOAD PRONUNCIATION FEATURES
# ============================================

pron_df = read_csv_auto(PRON_FILE)

pron_df["class_name"] = pron_df["class_name"].astype(str)
pron_df = extract_file_name_number(pron_df, source_col="file")

pron_keep_cols = [
    "class_name",
    "file_name",
    "0-50%",
    "50-70%",
    "70-85%",
    "85-95%",
    "95-100%",
]

pron_df = pron_df[pron_keep_cols].copy()

pron_df = pron_df.rename(
    columns={
        "0-50%": "pro_0%-50%",
        "50-70%": "pro_50%-70%",
        "70-85%": "pro_70%-85%",
        "85-95%": "pro_85%-95%",
        "95-100%": "pro_95%-100%",
    }
)


# ============================================
# 10. LOAD GRAMMAR FEATURES
# ============================================

grammar_df = read_csv_auto(GRAMMAR_FILE)

grammar_df["class_name"] = grammar_df["class_name"].astype(str)
grammar_df = extract_file_name_number(grammar_df, source_col="file")

grammar_keep_cols = [
    "class_name",
    "file_name",
    "ratio_error_sentences",
    "total_errors",
    "error_rate",
]

missing_grammar_cols = [
    col for col in grammar_keep_cols
    if col not in grammar_df.columns
]

if missing_grammar_cols:
    raise ValueError(
        "Missing required columns in grammar.csv: "
        + ", ".join(missing_grammar_cols)
    )

grammar_df = grammar_df[grammar_keep_cols].copy()

grammar_df = grammar_df.rename(
    columns={
        "ratio_error_sentences": "gram_ratio_error",
        "total_errors": "gram_total_errors",
        "error_rate": "gram_error_rate",
    }
)


# ============================================
# 11. MERGE ALL FEATURES WITH SCORES
# ============================================

needed_score_cols = [
    "class_name",
    "file_name",
    target_columns["fluency"],
    target_columns["lexical"],
    target_columns["pronunciation"],
    target_columns["grammar"],
    target_columns["overall"],
]

needed_score_cols = list(dict.fromkeys(needed_score_cols))

overall_df = (
    score_df[needed_score_cols]
    .merge(
        fluency_df,
        on=["class_name", "file_name"],
        how="inner",
    )
    .merge(
        lex_df,
        on=["class_name", "file_name"],
        how="inner",
    )
    .merge(
        pron_df,
        on=["class_name", "file_name"],
        how="inner",
    )
    .merge(
        grammar_df,
        on=["class_name", "file_name"],
        how="inner",
    )
)

print("\n===== MERGED DATA SAMPLE =====")
print(overall_df.head())
print("\nNumber of rows after merge:", len(overall_df))


# ============================================
# 12. CONVERT RAW FEATURES TO NUMERIC BEFORE ENGINEERING
# ============================================

raw_feature_cols = [
    # Fluency
    "flu_speech_rate",
    "flu_pause_ratio",

    # Lexical
    "lex_TTR",
    "lex_MSTTR",
    "lex_A1",
    "lex_A2",
    "lex_B1",
    "lex_B2",
    "lex_C1",

    # Pronunciation
    "pro_0%-50%",
    "pro_50%-70%",
    "pro_70%-85%",
    "pro_85%-95%",
    "pro_95%-100%",

    # Grammar
    "gram_ratio_error",
    "gram_total_errors",
    "gram_error_rate",
]

for col in raw_feature_cols:
    if col not in overall_df.columns:
        raise ValueError(f"Missing raw feature column: {col}")

    overall_df[col] = to_numeric_clean(overall_df[col])


# ============================================
# 13. CREATE ENGINEERED FEATURES
# ============================================

# Lexical feature giống code chị đã thử:
# lexical_advanced = B1 + 2*B2 + 3*C1
overall_df["lexical_advanced"] = (
    overall_df["lex_B1"]
    + 2 * overall_df["lex_B2"]
    + 3 * overall_df["lex_C1"]
)

# Pronunciation feature giống code chị đã thử:
# bad = 2*(0-50%) + (50-70%)
# good = (85-95%) + 2*(95-100%)
# neural = 70-85%
overall_df["pron_bad"] = (
    2 * overall_df["pro_0%-50%"]
    + overall_df["pro_50%-70%"]
)

overall_df["pron_good"] = (
    overall_df["pro_85%-95%"]
    + 2 * overall_df["pro_95%-100%"]
)

overall_df["pron_neural"] = overall_df["pro_70%-85%"]


# ============================================
# 14. DEFINE FEATURES FOR EACH MODEL
# ============================================

fluency_features = [
    "flu_speech_rate",
    "flu_pause_ratio",
]

lexical_features = [
    "lex_MSTTR",
    "lexical_advanced",
]

pronunciation_features = [
    "pron_bad",
    "pron_good",
    "pron_neural",
]

grammar_features = [
    "gram_ratio_error",
    "gram_total_errors",
    "gram_error_rate",
]

# Overall không train model riêng nữa.
# Overall sẽ được tính ở backend:
# overall = (fluency + lexical + pronunciation + grammar) / 4
overall_features = (
    fluency_features
    + lexical_features
    + pronunciation_features
    + grammar_features
)

targets = {
    "fluency": target_columns["fluency"],
    "lexical": target_columns["lexical"],
    "pronunciation": target_columns["pronunciation"],
    "grammar": target_columns["grammar"],
}

features_by_model = {
    "fluency": fluency_features,
    "lexical": lexical_features,
    "pronunciation": pronunciation_features,
    "grammar": grammar_features,
}


# ============================================
# 15. CHECK REQUIRED COLUMNS
# ============================================

required_cols = list(
    dict.fromkeys(
        overall_features + list(targets.values())
    )
)

missing_cols = [
    col for col in required_cols
    if col not in overall_df.columns
]

if missing_cols:
    raise ValueError(
        "Missing required columns after merge / feature engineering: "
        + ", ".join(missing_cols)
    )


# ============================================
# 16. CONVERT ENGINEERED FEATURES TO NUMERIC + FILL NA
# ============================================

feature_medians = {}

for col in overall_features:
    overall_df[col] = to_numeric_clean(overall_df[col])

    median_value = overall_df[col].median()

    if pd.isna(median_value):
        raise ValueError(
            f"Feature '{col}' has no valid numeric value after merge."
        )

    feature_medians[col] = float(median_value)
    overall_df[col] = overall_df[col].fillna(median_value)


# ============================================
# 17. CONVERT TARGETS TO NUMERIC
# ============================================

for target_name, target_column in targets.items():
    overall_df[target_column] = to_numeric_clean(overall_df[target_column])


# ============================================
# 18. SAVE FEATURE CONFIGURATION FOR BACKEND
# ============================================

feature_columns_path = MODEL_DIR / "feature_columns.json"

with open(feature_columns_path, "w", encoding="utf-8") as file:
    json.dump(overall_features, file, ensure_ascii=False, indent=4)

print("\nSaved overall feature columns to:", feature_columns_path)


feature_columns_by_model_path = MODEL_DIR / "feature_columns_by_model.json"

with open(feature_columns_by_model_path, "w", encoding="utf-8") as file:
    json.dump(features_by_model, file, ensure_ascii=False, indent=4)

print("Saved feature columns by model to:", feature_columns_by_model_path)


feature_medians_path = MODEL_DIR / "feature_medians.json"

with open(feature_medians_path, "w", encoding="utf-8") as file:
    json.dump(feature_medians, file, ensure_ascii=False, indent=4)

print("Saved feature medians to:", feature_medians_path)


# ============================================
# 19. PREPARE 5-FOLD CROSS VALIDATION
# ============================================

kf = KFold(
    n_splits=N_SPLITS,
    shuffle=True,
    random_state=RANDOM_STATE,
)

all_metrics = []
all_preds = []
all_cv_coefficients = []


# ============================================
# 20. RUN 5-FOLD CROSS VALIDATION
# ============================================

print("\n===== START 5-FOLD CROSS VALIDATION =====")

for target_name, target_column in targets.items():
    print(f"\n===== TARGET: {target_name.upper()} =====")

    current_features = features_by_model[target_name]

    print("Features:", current_features)
    print("Model: StandardScaler + LinearRegression")

    data = overall_df.dropna(subset=[target_column]).copy()

    if len(data) < N_SPLITS:
        raise ValueError(
            f"Target '{target_column}' only has {len(data)} valid rows, "
            f"but N_SPLITS={N_SPLITS}."
        )

    X_target = data[current_features]
    y_target = data[target_column]

    maes = []
    rmses = []
    r2s = []
    qwks = []

    for fold, (train_idx, test_idx) in enumerate(
        kf.split(X_target),
        start=1,
    ):
        X_train = X_target.iloc[train_idx]
        X_test = X_target.iloc[test_idx]

        y_train = y_target.iloc[train_idx]
        y_test = y_target.iloc[test_idx]

        model = create_model()
        model.fit(X_train, y_train)

        y_pred_raw = model.predict(X_test)
        y_pred = clip_score(y_pred_raw)

        fold_mae = mean_absolute_error(y_test, y_pred)
        fold_rmse = rmse(y_test, y_pred)
        fold_r2 = r2_score(y_test, y_pred)
        fold_qwk = qwk_half_band(y_test, y_pred)

        maes.append(fold_mae)
        rmses.append(fold_rmse)
        r2s.append(fold_r2)
        qwks.append(fold_qwk)

        fold_result = pd.DataFrame(
            {
                "class_name": data.iloc[test_idx]["class_name"].values,
                "file_name": data.iloc[test_idx]["file_name"].values,
                "target": target_name,
                "fold": fold,
                "true_score": y_test.values,
                "pred_score_raw": y_pred_raw,
                "pred_score": y_pred,
            }
        )

        all_preds.append(fold_result)

        coef_df = get_coefficients(model, current_features)
        coef_df["target"] = target_name
        coef_df["fold"] = fold
        coef_df["intercept"] = model.named_steps["regressor"].intercept_

        all_cv_coefficients.append(coef_df)

        print(
            f"Fold {fold}: "
            f"MAE={fold_mae:.3f} | "
            f"RMSE={fold_rmse:.3f} | "
            f"R2={fold_r2:.3f} | "
            f"QWK={fold_qwk:.3f}"
        )

    all_metrics.append(
        {
            "target": target_name,
            "num_rows": len(data),
            "num_features": len(current_features),
            "features": ", ".join(current_features),
            "MAE_mean": np.mean(maes),
            "MAE_std": np.std(maes),
            "RMSE_mean": np.mean(rmses),
            "RMSE_std": np.std(rmses),
            "R2_mean": np.mean(r2s),
            "R2_std": np.std(r2s),
            "QWK_mean": np.nanmean(qwks),
            "QWK_std": np.nanstd(qwks),
        }
    )

# ============================================
# 19. EXPORT CV RESULTS
# ============================================

metrics_df = pd.DataFrame(all_metrics)

metrics_path = OUTPUT_DIR / "linear_regression_cv_metrics_all_targets.csv"

metrics_df.to_csv(
    metrics_path,
    index=False,
    encoding="utf-8-sig",
)

print("\n===== ALL MODEL METRICS =====")
print(metrics_df)
print("\nSaved metrics to:", metrics_path)


predictions_df = pd.concat(all_preds, ignore_index=True)

predictions_long_path = OUTPUT_DIR / "linear_regression_predictions_long_all_targets.csv"

predictions_df.to_csv(
    predictions_long_path,
    index=False,
    encoding="utf-8-sig",
)

print("Saved long predictions to:", predictions_long_path)


wide_predictions_df = predictions_df.pivot_table(
    index=["class_name", "file_name"],
    columns="target",
    values=["true_score", "pred_score"],
    aggfunc="first",
)

wide_predictions_df.columns = [
    f"{target}_{score_type}"
    for score_type, target in wide_predictions_df.columns
]

wide_predictions_df = wide_predictions_df.reset_index()

ordered_cols = [
    "class_name",
    "file_name",

    "fluency_pred_score",
    "fluency_true_score",

    "lexical_pred_score",
    "lexical_true_score",

    "pronunciation_pred_score",
    "pronunciation_true_score",

    "grammar_pred_score",
    "grammar_true_score",

    "overall_pred_score",
    "overall_true_score",
]

ordered_cols_existing = [
    col for col in ordered_cols
    if col in wide_predictions_df.columns
]

wide_predictions_df = wide_predictions_df[ordered_cols_existing]

wide_predictions_path = OUTPUT_DIR / "linear_regression_predictions_wide_all_targets.csv"

wide_predictions_df.to_csv(
    wide_predictions_path,
    index=False,
    encoding="utf-8-sig",
)

print("\n===== PREDICTION SAMPLE =====")
print(wide_predictions_df.head(20))
print("\nSaved wide predictions to:", wide_predictions_path)


# ============================================
# 20. EXPORT CV COEFFICIENTS
# ============================================

cv_coefficients_df = pd.concat(
    all_cv_coefficients,
    ignore_index=True,
)

cv_coefficients_path = OUTPUT_DIR / "linear_regression_coefficients_cv.csv"

cv_coefficients_df.to_csv(
    cv_coefficients_path,
    index=False,
    encoding="utf-8-sig",
)

print("\nSaved CV coefficients to:", cv_coefficients_path)


coefficient_summary_df = (
    cv_coefficients_df
    .groupby(["target", "feature"], as_index=False)
    .agg(
        coefficient_mean=("coefficient", "mean"),
        coefficient_std=("coefficient", "std"),
        abs_coefficient_mean=("abs_coefficient", "mean"),
    )
    .sort_values(
        ["target", "abs_coefficient_mean"],
        ascending=[True, False],
    )
)

coefficient_summary_path = OUTPUT_DIR / "linear_regression_coefficients_summary.csv"

coefficient_summary_df.to_csv(
    coefficient_summary_path,
    index=False,
    encoding="utf-8-sig",
)

print("Saved coefficient summary to:", coefficient_summary_path)


# ============================================
# 21. TRAIN FINAL MODELS ON FULL DATASET
# ============================================

final_models = {}
final_coefficients = []

print("\n===== TRAIN FINAL MODELS ON FULL DATASET =====")

for target_name, target_column in targets.items():
    print(f"\n===== TRAIN FINAL MODEL FOR {target_name.upper()} =====")

    current_features = features_by_model[target_name]

    data = overall_df.dropna(subset=[target_column]).copy()

    X_final = data[current_features]
    y_final = data[target_column]

    final_model = create_model()
    final_model.fit(X_final, y_final)

    final_models[target_name] = final_model

    model_path = MODEL_DIR / f"{target_name}_score_model_linear.pkl"

    joblib.dump(final_model, model_path)

    coef_df = get_coefficients(final_model, current_features)
    coef_df["target"] = target_name
    coef_df["intercept"] = final_model.named_steps["regressor"].intercept_

    final_coefficients.append(coef_df)

    print("Features:", current_features)
    print(f"Saved {target_name} model to: {model_path}")


# ============================================
# 22. SAVE FINAL COEFFICIENTS
# ============================================

final_coefficients_df = pd.concat(
    final_coefficients,
    ignore_index=True,
)

final_coefficients_path = OUTPUT_DIR / "linear_regression_coefficients_final.csv"

final_coefficients_df.to_csv(
    final_coefficients_path,
    index=False,
    encoding="utf-8-sig",
)

print("\nSaved final coefficients to:", final_coefficients_path)


# ============================================
# 23. SAVE BACKGROUND DATA
# ============================================

background_data = overall_df[overall_features].copy()

background_path = MODEL_DIR / "linear_regression_background_data.csv"

background_data.to_csv(
    background_path,
    index=False,
    encoding="utf-8-sig",
)

print("Saved background data to:", background_path)


# ============================================
# 24. SAVE TRAINING METADATA
# ============================================

training_metadata = {
    "model_type": "LinearRegression",
    "pipeline": "StandardScaler + LinearRegression",
    "n_splits": N_SPLITS,
    "random_state": RANDOM_STATE,
    "features": overall_features,
    "features_by_model": features_by_model,
    "targets": targets,
    "saved_models": {
        target_name: str(MODEL_DIR / f"{target_name}_score_model_linear.pkl")
        for target_name in targets
    },
    "saved_config_files": {
        "feature_columns": str(feature_columns_path),
        "feature_columns_by_model": str(feature_columns_by_model_path),
        "feature_medians": str(feature_medians_path),
        "background_data": str(background_path),
    },
    "saved_output_files": {
        "metrics": str(metrics_path),
        "predictions_long": str(predictions_long_path),
        "predictions_wide": str(wide_predictions_path),
        "cv_coefficients": str(cv_coefficients_path),
        "coefficient_summary": str(coefficient_summary_path),
        "final_coefficients": str(final_coefficients_path),
    },
}

metadata_path = MODEL_DIR / "linear_regression_training_metadata.json"

with open(metadata_path, "w", encoding="utf-8") as file:
    json.dump(training_metadata, file, ensure_ascii=False, indent=4)

print("Saved training metadata to:", metadata_path)


# ============================================
# 25. DONE
# ============================================

print("\n===== TRAINING COMPLETED SUCCESSFULLY =====")
print("Model directory:", MODEL_DIR)
print("Output directory:", OUTPUT_DIR)

print("\nSaved final model files:")
for target_name in targets:
    print("-", MODEL_DIR / f"{target_name}_score_model_linear.pkl")