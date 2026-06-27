# -*- coding: utf-8 -*-

"""
Train Linear Regression models for ASR speaking assessment.

Models saved:
1. fluency_score_model_linear.pkl
2. lexical_score_model_linear.pkl
3. pronunciation_score_model_linear.pkl
4. overall_score_model_linear.pkl

Grammar is NOT a separate model.

Grammar formula:
grammar = overall * 4 - fluency - lexical - pronunciation
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
# PROJECT ROOT
# ============================================

def find_project_root():
    """
    Tự tìm thư mục project root có folder data.
    Dùng được khi file này nằm ở project root hoặc scripts/ml.
    """
    current = Path(__file__).resolve().parent

    for path in [current] + list(current.parents):
        if (path / "data").exists():
            return path

    return current


BASE_DIR = find_project_root()

DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "ml_models"
OUTPUT_DIR = BASE_DIR / "outputs"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================
# DATA FILES
# ============================================

SCORES_FILE = DATA_DIR / "averaged_scores_by_filename.xlsx"

FLUENCY_FILE = DATA_DIR / "fluency.csv"
PRON_FILE = DATA_DIR / "pronunciation.csv"
LEX_SOPH_FILE = DATA_DIR / "lexical_sophistication.csv"
LEX_DIV_FILE = DATA_DIR / "lexical_diversity.csv"


# ============================================
# CONFIG
# ============================================

N_SPLITS = 5
RANDOM_STATE = 42


# ============================================
# HELPER FUNCTIONS
# ============================================

def round_half(x):
    """
    Làm tròn điểm về band 0.5.
    """
    x = np.asarray(x, dtype=float)
    x = np.clip(x, 0, 9)
    return np.round(x * 2) / 2


def clip_score(x):
    """
    Giới hạn điểm trong khoảng 0-9.
    """
    return np.clip(x, 0, 9)


def rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))


def qwk_half_band(y_true, y_pred):
    """
    Quadratic Weighted Kappa cho IELTS band 0.0 -> 9.0 step 0.5.
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
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")


def read_csv_auto(file_path):
    """
    Đọc CSV tự nhận dấu phẩy hoặc chấm phẩy.
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
    Convert numeric an toàn.
    Hỗ trợ số dạng 0,33333.
    """
    return pd.to_numeric(
        series.astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )


def extract_file_name_number(df, source_col="file"):
    """
    Tách file_name dạng số từ cột file.

    Ví dụ:
    1_prob.csv  -> 1
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


def find_score_column(score_df, target_name, candidates):
    """
    Tìm tên cột điểm trong score file.
    """
    for col in candidates:
        if col in score_df.columns:
            return col

    raise ValueError(
        f"Cannot find score column for target '{target_name}'. "
        f"Expected one of: {candidates}"
    )


def require_columns(df, required_cols, df_name):
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        raise ValueError(
            f"{df_name} missing columns: {missing}"
        )


def create_model():
    """
    Model Linear Regression có StandardScaler.
    Khi deploy, pkl này predict trực tiếp được.
    """
    return Pipeline(
        steps=[
            ("regressor", LinearRegression()),
        ]
    )


def get_coefficients(model, feature_names):
    regressor = model.named_steps["regressor"]

    coef_df = pd.DataFrame({
        "feature": feature_names,
        "coefficient": regressor.coef_,
    })

    coef_df["abs_coefficient"] = coef_df["coefficient"].abs()

    coef_df = coef_df.sort_values(
        "abs_coefficient",
        ascending=False,
    )

    return coef_df


# ============================================
# CHECK INPUT FILES
# ============================================

for file_path in [
    SCORES_FILE,
    FLUENCY_FILE,
    PRON_FILE,
    LEX_SOPH_FILE,
    LEX_DIV_FILE,
]:
    check_file_exists(file_path)

print("===== INPUT FILES FOUND =====")
print("Scores:", SCORES_FILE)
print("Fluency:", FLUENCY_FILE)
print("Pronunciation:", PRON_FILE)
print("Lexical sophistication:", LEX_SOPH_FILE)
print("Lexical diversity:", LEX_DIV_FILE)


# ============================================
# 1. LOAD SCORE FILE
# ============================================

score_df = pd.read_excel(SCORES_FILE)

require_columns(
    score_df,
    ["class_name", "file_name"],
    "score_df",
)

score_df["class_name"] = score_df["class_name"].astype(str)

score_df["file_name"] = pd.to_numeric(
    score_df["file_name"],
    errors="coerce",
).astype("Int64")


target_columns = {
    "fluency": "avg_fluency",
    "lexical": "avg_lexical",
    "pronunciation": "avg_pronunciation",
    "overall": "avg_overall",
}

print("\n===== TARGET COLUMNS =====")
print(target_columns)


# ============================================
# 2. LOAD FLUENCY FEATURES
# ============================================

fluency_df = read_csv_auto(FLUENCY_FILE)

require_columns(
    fluency_df,
    [
        "class_name",
        "file",
        "speech_rate_wps",
        "ratio_pauses_to_duration",
    ],
    "fluency_df",
)

fluency_df["class_name"] = fluency_df["class_name"].astype(str)
fluency_df = extract_file_name_number(fluency_df, source_col="file")

fluency_df = fluency_df[
    [
        "class_name",
        "file_name",
        "speech_rate_wps",
        "ratio_pauses_to_duration",
    ]
].copy()

fluency_df = fluency_df.rename(
    columns={
        "speech_rate_wps": "flu_speech_rate",
        "ratio_pauses_to_duration": "flu_pause_ratio",
    }
)


# ============================================
# 3. LOAD LEXICAL DIVERSITY
# ============================================

lex_div_df = read_csv_auto(LEX_DIV_FILE)

require_columns(
    lex_div_df,
    [
        "class_name",
        "file",
        "MSTTR",
    ],
    "lex_div_df",
)

lex_div_df["class_name"] = lex_div_df["class_name"].astype(str)
lex_div_df = extract_file_name_number(lex_div_df, source_col="file")

lex_div_df = lex_div_df[
    [
        "class_name",
        "file_name",
        "MSTTR",
    ]
].copy()

lex_div_df = lex_div_df.rename(
    columns={
        "MSTTR": "lex_MSTTR",
    }
)


# ============================================
# 4. LOAD LEXICAL SOPHISTICATION
# ============================================

lex_soph_df = read_csv_auto(LEX_SOPH_FILE)

require_columns(
    lex_soph_df,
    [
        "class_name",
        "file",
        "A1",
        "A2",
        "B1",
        "B2",
        "C1",
    ],
    "lex_soph_df",
)

lex_soph_df["class_name"] = lex_soph_df["class_name"].astype(str)
lex_soph_df = extract_file_name_number(lex_soph_df, source_col="file")

lex_soph_df = lex_soph_df[
    [
        "class_name",
        "file_name",
        "A1",
        "A2",
        "B1",
        "B2",
        "C1",
    ]
].copy()

lex_soph_df = lex_soph_df.rename(
    columns={
        "A1": "lex_A1",
        "A2": "lex_A2",
        "B1": "lex_B1",
        "B2": "lex_B2",
        "C1": "lex_C1",
    }
)


# ============================================
# 5. MERGE LEXICAL FEATURES
# ============================================

lex_df = lex_div_df.merge(
    lex_soph_df,
    on=["class_name", "file_name"],
    how="inner",
)


# ============================================
# 6. LOAD PRONUNCIATION FEATURES
# ============================================

pron_df = read_csv_auto(PRON_FILE)

require_columns(
    pron_df,
    [
        "class_name",
        "file",
        "0-50%",
        "50-70%",
        "70-85%",
        "85-95%",
        "95-100%",
    ],
    "pron_df",
)

pron_df["class_name"] = pron_df["class_name"].astype(str)
pron_df = extract_file_name_number(pron_df, source_col="file")

pron_df = pron_df[
    [
        "class_name",
        "file_name",
        "0-50%",
        "50-70%",
        "70-85%",
        "85-95%",
        "95-100%",
    ]
].copy()

pron_df = pron_df.rename(
    columns={
        "0-50%": "pro_0_50",
        "50-70%": "pro_50_70",
        "70-85%": "pro_70_85",
        "85-95%": "pro_85_95",
        "95-100%": "pro_95_100",
    }
)


# ============================================
# 7. MERGE ALL
# ============================================

score_keep_cols = [
    "class_name",
    "file_name",
    target_columns["fluency"],
    target_columns["lexical"],
    target_columns["pronunciation"],
    target_columns["overall"],
]

score_keep_cols = list(dict.fromkeys(score_keep_cols))

model_df = (
    score_df[score_keep_cols]
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
)

print("\n===== MERGED DATA SAMPLE =====")
print(model_df.head())
print("\nNumber of rows after merge:", len(model_df))


# ============================================
# 8. CONVERT RAW FEATURES TO NUMERIC
# ============================================

raw_feature_cols = [
    "flu_speech_rate",
    "flu_pause_ratio",

    "lex_MSTTR",
    "lex_A1",
    "lex_A2",
    "lex_B1",
    "lex_B2",
    "lex_C1",

    "pro_0_50",
    "pro_50_70",
    "pro_70_85",
    "pro_85_95",
    "pro_95_100",
]

for col in raw_feature_cols:
    model_df[col] = to_numeric_clean(model_df[col])


# ============================================
# 9. FEATURE ENGINEERING
# ============================================

model_df["lexical_advanced"] = (
    model_df["lex_B1"]
    + 2 * model_df["lex_B2"]
    + 3 * model_df["lex_C1"]
)

model_df["pron_bad"] = (
    2 * model_df["pro_0_50"]
    + model_df["pro_50_70"]
)

model_df["pron_good"] = (
    model_df["pro_85_95"]
    + 2 * model_df["pro_95_100"]
)

model_df["pron_neutral"] = model_df["pro_70_85"]




# ============================================
# 10. DEFINE FEATURES
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
    "pron_neutral",
]

overall_features = (
    fluency_features
    + lexical_features
    + pronunciation_features
)

features_by_model = {
    "fluency": fluency_features,
    "lexical": lexical_features,
    "pronunciation": pronunciation_features,
    "overall": overall_features,
}

targets = {
    "fluency": target_columns["fluency"],
    "lexical": target_columns["lexical"],
    "pronunciation": target_columns["pronunciation"],
    "overall": target_columns["overall"],
}


# ============================================
# 11. CLEAN FEATURES + TARGETS
# ============================================

all_features = list(
    dict.fromkeys(
        fluency_features
        + lexical_features
        + pronunciation_features
        + overall_features
    )
)

feature_medians = {}

for col in all_features:
    model_df[col] = to_numeric_clean(model_df[col])

    median_value = model_df[col].median()

    if pd.isna(median_value):
        raise ValueError(
            f"Feature '{col}' has no valid numeric value."
        )

    feature_medians[col] = float(median_value)
    model_df[col] = model_df[col].fillna(median_value)

for target_name, target_col in targets.items():
    model_df[target_col] = to_numeric_clean(model_df[target_col])


required_cols = all_features + list(targets.values())

model_df = model_df.dropna(subset=required_cols).copy()

print("\n===== FINAL TRAIN DATA =====")
print("Rows:", len(model_df))
print("Features by model:")
print(json.dumps(features_by_model, ensure_ascii=False, indent=4))


# ============================================
# 12. AUGMENT DATA
# GIỮ LOGIC TỪ CODE CŨ
# ============================================

def augment_fluency_train_df(df_input):
    df_base = df_input.copy()

    df2 = df_input.copy()
    df2["flu_pause_ratio"] = df2["flu_pause_ratio"] + 0.05
    df2[targets["fluency"]] = df2[targets["fluency"]] + 0.5

    df3 = df_input.copy()
    df3["flu_pause_ratio"] = df3["flu_pause_ratio"] + 0.1
    df3[targets["fluency"]] = df3[targets["fluency"]] + 1

    df_aug = pd.concat(
        [df_base, df2, df3],
        ignore_index=True,
    )

    df_aug[targets["fluency"]] = clip_score(
        df_aug[targets["fluency"]]
    )

    return df_aug


def augment_pronunciation_train_df(df_input):
    df_base = df_input.copy()

    df2 = df_input.copy()
    df2["pron_bad"] = df2["pron_bad"] - 5
    df2["pron_good"] = df2["pron_good"] + 5
    df2[targets["pronunciation"]] = (
        df2[targets["pronunciation"]] + 0.5
    )

    df3 = df_input.copy()
    df3["pron_bad"] = df3["pron_bad"] - 10
    df3["pron_good"] = df3["pron_good"] + 10
    df3[targets["pronunciation"]] = (
        df3[targets["pronunciation"]] + 1
    )

    df_aug = pd.concat(
        [df_base, df2, df3],
        ignore_index=True,
    )

    df_aug[targets["pronunciation"]] = clip_score(
        df_aug[targets["pronunciation"]]
    )

    return df_aug


def get_train_df_for_target(df_input, target_name):
    if target_name == "fluency":
        return augment_fluency_train_df(df_input)

    if target_name == "pronunciation":
        return augment_pronunciation_train_df(df_input)

    return df_input.copy()


# ============================================
# 13. SAVE FEATURE CONFIG
# ============================================

feature_columns_by_model_path = MODEL_DIR / "feature_columns_by_model.json"
feature_medians_path = MODEL_DIR / "feature_medians.json"
overall_feature_columns_path = MODEL_DIR / "feature_columns.json"

with open(feature_columns_by_model_path, "w", encoding="utf-8") as file:
    json.dump(
        features_by_model,
        file,
        ensure_ascii=False,
        indent=4,
    )

with open(feature_medians_path, "w", encoding="utf-8") as file:
    json.dump(
        feature_medians,
        file,
        ensure_ascii=False,
        indent=4,
    )

with open(overall_feature_columns_path, "w", encoding="utf-8") as file:
    json.dump(
        overall_features,
        file,
        ensure_ascii=False,
        indent=4,
    )

print("\nSaved feature columns by model to:", feature_columns_by_model_path)
print("Saved feature medians to:", feature_medians_path)
print("Saved overall feature columns to:", overall_feature_columns_path)


# ============================================
# 14. 5-FOLD CV
# ============================================

kf = KFold(
    n_splits=N_SPLITS,
    shuffle=True,
    random_state=RANDOM_STATE,
)

cv_rows = []
all_fold_predictions = []
all_cv_coefficients = []

print("\n===== START 5-FOLD CROSS VALIDATION =====")

for fold, (train_idx, test_idx) in enumerate(
    kf.split(model_df),
    start=1,
):
    print(f"\n===== FOLD {fold} =====")

    train_df = model_df.iloc[train_idx].copy()
    test_df = model_df.iloc[test_idx].copy()

    fold_models = {}
    fold_preds_raw = {}
    fold_preds_band = {}

    for target_name, target_col in targets.items():
        current_features = features_by_model[target_name]

        train_target_df = get_train_df_for_target(
            train_df,
            target_name,
        )

        X_train = train_target_df[current_features]
        y_train = train_target_df[target_col]

        X_test = test_df[current_features]
        y_test = test_df[target_col]

        model = create_model()
        model.fit(X_train, y_train)

        y_pred_raw = model.predict(X_test)
        y_pred_raw = clip_score(y_pred_raw)

        y_pred_band = round_half(y_pred_raw)

        fold_models[target_name] = model
        fold_preds_raw[target_name] = y_pred_raw
        fold_preds_band[target_name] = y_pred_band

        mae = mean_absolute_error(y_test, y_pred_raw)
        fold_rmse = rmse(y_test, y_pred_raw)
        r2 = r2_score(y_test, y_pred_raw)
        qwk = qwk_half_band(y_test, y_pred_raw)

        cv_rows.append({
            "target": target_name,
            "fold": fold,
            "num_rows_train": len(train_target_df),
            "num_rows_test": len(test_df),
            "num_features": len(current_features),
            "features": ", ".join(current_features),
            "MAE": mae,
            "RMSE": fold_rmse,
            "R2": r2,
            "QWK": qwk,
        })

        coef_df = get_coefficients(model, current_features)
        coef_df["target"] = target_name
        coef_df["fold"] = fold
        coef_df["intercept"] = model.named_steps["regressor"].intercept_

        all_cv_coefficients.append(coef_df)

        print(
            f"{target_name}: "
            f"MAE={mae:.4f}, "
            f"RMSE={fold_rmse:.4f}, "
            f"R2={r2:.4f}, "
            f"QWK={qwk:.4f}"
        )

    pred_grammar_raw = (
        fold_preds_raw["overall"] * 4
        - fold_preds_raw["fluency"]
        - fold_preds_raw["lexical"]
        - fold_preds_raw["pronunciation"]
    )

    pred_grammar_raw = clip_score(pred_grammar_raw)
    pred_grammar_band = round_half(pred_grammar_raw)

    true_grammar = (
        test_df[targets["overall"]].values * 4
        - test_df[targets["fluency"]].values
        - test_df[targets["lexical"]].values
        - test_df[targets["pronunciation"]].values
    )

    true_grammar = clip_score(true_grammar)

    grammar_mae = mean_absolute_error(
        true_grammar,
        pred_grammar_raw,
    )

    grammar_rmse = rmse(
        true_grammar,
        pred_grammar_raw,
    )

    grammar_r2 = r2_score(
        true_grammar,
        pred_grammar_raw,
    )

    grammar_qwk = qwk_half_band(
        true_grammar,
        pred_grammar_raw,
    )

    cv_rows.append({
        "target": "grammar_formula",
        "fold": fold,
        "num_rows_train": len(train_df),
        "num_rows_test": len(test_df),
        "num_features": 0,
        "features": "overall*4 - fluency - lexical - pronunciation",
        "MAE": grammar_mae,
        "RMSE": grammar_rmse,
        "R2": grammar_r2,
        "QWK": grammar_qwk,
    })

    print(
        f"grammar_formula: "
        f"MAE={grammar_mae:.4f}, "
        f"RMSE={grammar_rmse:.4f}, "
        f"R2={grammar_r2:.4f}, "
        f"QWK={grammar_qwk:.4f}"
    )

    fold_prediction_df = pd.DataFrame({
        "class_name": test_df["class_name"].values,
        "file_name": test_df["file_name"].values,
        "fold": fold,

        "true_fluency": test_df[targets["fluency"]].values,
        "pred_fluency_raw": fold_preds_raw["fluency"],
        "pred_fluency_band": fold_preds_band["fluency"],

        "true_lexical": test_df[targets["lexical"]].values,
        "pred_lexical_raw": fold_preds_raw["lexical"],
        "pred_lexical_band": fold_preds_band["lexical"],

        "true_pronunciation": test_df[targets["pronunciation"]].values,
        "pred_pronunciation_raw": fold_preds_raw["pronunciation"],
        "pred_pronunciation_band": fold_preds_band["pronunciation"],

        "true_overall": test_df[targets["overall"]].values,
        "pred_overall_raw": fold_preds_raw["overall"],
        "pred_overall_band": fold_preds_band["overall"],

        "true_grammar": true_grammar,
        "pred_grammar_raw": pred_grammar_raw,
        "pred_grammar_band": pred_grammar_band,
    })

    all_fold_predictions.append(fold_prediction_df)


# ============================================
# 15. EXPORT CV RESULTS
# ============================================

cv_metrics_df = pd.DataFrame(cv_rows)

cv_summary_df = (
    cv_metrics_df
    .groupby("target", as_index=False)
    .agg(
        MAE_mean=("MAE", "mean"),
        MAE_std=("MAE", "std"),
        RMSE_mean=("RMSE", "mean"),
        RMSE_std=("RMSE", "std"),
        R2_mean=("R2", "mean"),
        R2_std=("R2", "std"),
        QWK_mean=("QWK", "mean"),
        QWK_std=("QWK", "std"),
    )
)

cv_metrics_path = OUTPUT_DIR / "linear_regression_cv_metrics_by_fold.csv"
cv_summary_path = OUTPUT_DIR / "linear_regression_cv_metrics_summary.csv"

cv_metrics_df.to_csv(
    cv_metrics_path,
    index=False,
    encoding="utf-8-sig",
)

cv_summary_df.to_csv(
    cv_summary_path,
    index=False,
    encoding="utf-8-sig",
)

print("\n===== CV SUMMARY =====")
print(cv_summary_df)
print("\nSaved CV metrics to:", cv_metrics_path)
print("Saved CV summary to:", cv_summary_path)


predictions_df = pd.concat(
    all_fold_predictions,
    ignore_index=True,
)

predictions_path = OUTPUT_DIR / "linear_regression_predictions_cv.csv"

predictions_df.to_csv(
    predictions_path,
    index=False,
    encoding="utf-8-sig",
)

print("\nSaved CV predictions to:", predictions_path)


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

print("Saved CV coefficients to:", cv_coefficients_path)


# ============================================
# 16. TRAIN FINAL 4 MODELS
# ============================================

final_models = {}
final_coefficients = []

print("\n===== TRAIN FINAL MODELS ON FULL DATASET =====")

for target_name, target_col in targets.items():
    print(f"\n===== TRAIN FINAL MODEL FOR {target_name.upper()} =====")

    current_features = features_by_model[target_name]

    train_target_df = get_train_df_for_target(
        model_df,
        target_name,
    )

    X_final = train_target_df[current_features]
    y_final = train_target_df[target_col]

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
    print("Saved model to:", model_path)


# ============================================
# 17. SAVE FINAL COEFFICIENTS
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
# 18. SAVE BACKGROUND DATA
# ============================================

background_data = model_df[overall_features].copy()

background_path = MODEL_DIR / "linear_regression_background_data.csv"

background_data.to_csv(
    background_path,
    index=False,
    encoding="utf-8-sig",
)

print("Saved background data to:", background_path)


# ============================================
# 19. SAVE METADATA
# ============================================

training_metadata = {
    "model_type": "LinearRegression",
    "pipeline": "StandardScaler + LinearRegression",
    "n_splits": N_SPLITS,
    "random_state": RANDOM_STATE,
    "features_by_model": features_by_model,
    "overall_features": overall_features,
    "targets": targets,
    "grammar": {
        "is_model": False,
        "formula": "grammar = overall * 4 - fluency - lexical - pronunciation",
    },
    "saved_models": {
        "fluency": str(MODEL_DIR / "fluency_score_model_linear.pkl"),
        "lexical": str(MODEL_DIR / "lexical_score_model_linear.pkl"),
        "pronunciation": str(MODEL_DIR / "pronunciation_score_model_linear.pkl"),
        "overall": str(MODEL_DIR / "overall_score_model_linear.pkl"),
    },
    "saved_config_files": {
        "feature_columns_by_model": str(feature_columns_by_model_path),
        "feature_medians": str(feature_medians_path),
        "overall_feature_columns": str(overall_feature_columns_path),
        "background_data": str(background_path),
    },
    "saved_output_files": {
        "cv_metrics_by_fold": str(cv_metrics_path),
        "cv_metrics_summary": str(cv_summary_path),
        "cv_predictions": str(predictions_path),
        "cv_coefficients": str(cv_coefficients_path),
        "final_coefficients": str(final_coefficients_path),
    },
}

metadata_path = MODEL_DIR / "linear_regression_training_metadata.json"

with open(metadata_path, "w", encoding="utf-8") as file:
    json.dump(
        training_metadata,
        file,
        ensure_ascii=False,
        indent=4,
    )

print("Saved training metadata to:", metadata_path)


# ============================================
# 20. DONE
# ============================================

print("\n===== TRAINING COMPLETED SUCCESSFULLY =====")
print("Model directory:", MODEL_DIR)
print("Output directory:", OUTPUT_DIR)

print("\nSaved final model files:")
print("-", MODEL_DIR / "fluency_score_model_linear.pkl")
print("-", MODEL_DIR / "lexical_score_model_linear.pkl")
print("-", MODEL_DIR / "pronunciation_score_model_linear.pkl")
print("-", MODEL_DIR / "overall_score_model_linear.pkl")

print("\nGrammar is calculated by formula, no grammar pkl saved.")