# -*- coding: utf-8 -*-

"""
Train CatBoost score models for ASR speaking assessment.

This file will:
1. Load score labels and extracted ASR features
2. Merge fluency, lexical, pronunciation features
3. Train and evaluate 4 targets with 5-fold CV:
   - overall
   - fluency
   - lexical
   - pronunciation
4. Export prediction results
5. Generate SHAP summary plot for overall model
6. Train final models on full dataset
7. Save final CatBoost models into src/ml_models/
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt

from catboost import CatBoostRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score




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

# ============================================
# MODEL DIRECTORY
# ============================================

MODEL_DIR = BASE_DIR / "ml_models"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Thư mục lưu kết quả output
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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

    n = 19  # 0..18
    O = np.zeros((n, n), dtype=float)

    for a, b in zip(y_true, y_pred):
        O[a, b] += 1

    hist_true = np.bincount(y_true, minlength=n)
    hist_pred = np.bincount(y_pred, minlength=n)
    E = np.outer(hist_true, hist_pred) / len(y_true)

    W = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            W[i, j] = ((i - j) ** 2) / ((n - 1) ** 2)

    denom = np.sum(W * E)

    if denom == 0:
        return np.nan

    return 1 - np.sum(W * O) / denom


def check_file_exists(file_path):
    """
    Check whether input file exists.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")


def extract_file_name_number(df, source_col="file"):
    """
    Extract numeric file_name from file column.
    Example:
        1_prob.csv -> 1
    """
    df["file_name"] = (
        df[source_col]
        .astype(str)
        .str.extract(r"(\d+)")[0]
    )

    df["file_name"] = pd.to_numeric(
        df["file_name"],
        errors="coerce"
    ).astype("Int64")

    return df


# ============================================
# 2. CHECK INPUT FILES
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
# 3. LOAD SCORE FILE
# ============================================

score_df = pd.read_excel(SCORES_FILE)

score_df["class_name"] = score_df["class_name"].astype(str)
score_df["file_name"] = pd.to_numeric(
    score_df["file_name"],
    errors="coerce"
).astype("Int64")


# ============================================
# 4. LOAD FLUENCY FEATURES
# ============================================

fluency_df = pd.read_csv(FLUENCY_FILE)
fluency_df["class_name"] = fluency_df["class_name"].astype(str)
fluency_df = extract_file_name_number(fluency_df, source_col="file")


# ============================================
# 5. LOAD LEXICAL DIVERSITY
# ============================================

lex_div_df = pd.read_csv(LEX_DIV_FILE)
lex_div_df["class_name"] = lex_div_df["class_name"].astype(str)
lex_div_df = extract_file_name_number(lex_div_df, source_col="file")


# ============================================
# 6. LOAD LEXICAL SOPHISTICATION
# ============================================

lex_soph_df = pd.read_csv(LEX_SOPH_FILE)
lex_soph_df["class_name"] = lex_soph_df["class_name"].astype(str)
lex_soph_df = extract_file_name_number(lex_soph_df, source_col="file")


# ============================================
# 7. MERGE LEXICAL DIVERSITY + SOPHISTICATION
# ============================================

lex_df = lex_div_df.merge(
    lex_soph_df[
        [
            "class_name",
            "file_name",
            "A1",
            "A2",
            "B1",
            "B2",
            "C1",
        ]
    ],
    on=["class_name", "file_name"],
    how="inner"
)


# ============================================
# 8. LOAD PRONUNCIATION FEATURES
# ============================================

pron_df = pd.read_csv(PRON_FILE)
pron_df["class_name"] = pron_df["class_name"].astype(str)
pron_df = extract_file_name_number(pron_df, source_col="file")


# ============================================
# 9. MERGE ALL FEATURES WITH SCORES
# ============================================

needed_score_cols = [
    "class_name",
    "file_name",
    "avg_overall",
    "avg_fluency",
    "avg_lexical",
    "avg_pronunciation",
]

overall_df = (
    score_df[needed_score_cols]
    .merge(
        fluency_df,
        on=["class_name", "file_name"],
        how="inner"
    )
    .merge(
        lex_df,
        on=["class_name", "file_name"],
        how="inner"
    )
    .merge(
        pron_df,
        on=["class_name", "file_name"],
        how="inner"
    )
)

print("\n===== MERGED DATA SAMPLE =====")
print(overall_df.head())
print("\nNumber of rows after merge:", len(overall_df))


# ============================================
# 10. RENAME FEATURE COLUMNS
# ============================================

overall_df = overall_df.rename(
    columns={
        # Fluency
        "total_duration": "flu_total_duration",
        "total_words_x": "flu_total_words",
        "speech_rate_wps": "flu_speech_rate",
        "num_pauses": "flu_num_pauses",
        "duration_pauses": "flu_pause_duration",
        "ratio_pauses_to_duration": "flu_pause_ratio",

        # Lexical
        "TTR": "lex_TTR",
        "MSTTR": "lex_MSTTR",
        "A1": "lex_A1",
        "A2": "lex_A2",
        "B1": "lex_B1",
        "B2": "lex_B2",
        "C1": "lex_C1",

        # Pronunciation
        "total_words_y": "total_words_pron",
        "0-50%": "pro_0%-50%",
        "50-70%": "pro_50%-70%",
        "70-85%": "pro_70%-85%",
        "85-95%": "pro_85%-95%",
        "95-100%": "pro_95%-100%",
    }
)


# ============================================
# 11. DEFINE FEATURES AND TARGETS
# ============================================

overall_features = [
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
]

targets = {
    "overall": "avg_overall",
    "fluency": "avg_fluency",
    "lexical": "avg_lexical",
    "pronunciation": "avg_pronunciation",
}


# ============================================
# 12. CHECK REQUIRED COLUMNS
# ============================================

required_cols = overall_features + list(targets.values())

missing_cols = [
    col for col in required_cols
    if col not in overall_df.columns
]

if missing_cols:
    raise ValueError(
        "Missing required columns after merge/rename: "
        + ", ".join(missing_cols)
    )


# ============================================
# 13. CONVERT FEATURES TO NUMERIC + FILL NA
# ============================================

feature_medians = {}

for col in overall_features:
    overall_df[col] = pd.to_numeric(overall_df[col], errors="coerce")

    median_value = overall_df[col].median()
    feature_medians[col] = float(median_value)

    overall_df[col] = overall_df[col].fillna(median_value)


# Save feature medians for backend
feature_medians_path = MODEL_DIR / "feature_medians.json"

with open(feature_medians_path, "w", encoding="utf-8") as f:
    json.dump(feature_medians, f, ensure_ascii=False, indent=4)

print("\nSaved feature medians to:", feature_medians_path)


# Save feature columns for backend
feature_columns_path = MODEL_DIR / "feature_columns.json"

with open(feature_columns_path, "w", encoding="utf-8") as f:
    json.dump(overall_features, f, ensure_ascii=False, indent=4)

print("Saved feature columns to:", feature_columns_path)


# ============================================
# 14. 5-FOLD CROSS VALIDATION
# ============================================

kf = KFold(
    n_splits=N_SPLITS,
    shuffle=True,
    random_state=RANDOM_STATE
)

all_metrics = []
all_preds = []

# For overall SHAP across 5 CV folds
overall_fold_models = []
overall_shap_values_list = []
overall_X_test_list = []
overall_shap_importance_list = []


print("\n===== START 5-FOLD CROSS VALIDATION =====")

for target_name, target_column in targets.items():

    print(f"\n===== TARGET: {target_name.upper()} =====")

    data = overall_df.dropna(subset=[target_column]).copy()

    X_target = data[overall_features]
    y_target = data[target_column]

    maes = []
    rmses = []
    r2s = []
    qwks = []

    for fold, (train_idx, test_idx) in enumerate(kf.split(X_target), 1):

        X_train = X_target.iloc[train_idx]
        X_test = X_target.iloc[test_idx]

        y_train = y_target.iloc[train_idx]
        y_test = y_target.iloc[test_idx]

        model = CatBoostRegressor(
            iterations=300,
            learning_rate=0.05,
            depth=4,
            loss_function="RMSE",
            random_seed=RANDOM_STATE,
            verbose=False
        )

        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

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
                "pred_score": y_pred,
            }
        )

        all_preds.append(fold_result)

        print(
            f"Fold {fold}: "
            f"MAE={fold_mae:.3f} | "
            f"RMSE={fold_rmse:.3f} | "
            f"R2={fold_r2:.3f} | "
            f"QWK={fold_qwk:.3f}"
        )

        # ============================================
        # SAVE SHAP ONLY FOR OVERALL TARGET
        # ============================================
        if target_name == "overall":
            overall_fold_models.append(model)

            explainer = shap.TreeExplainer(model)
            shap_values_fold = explainer.shap_values(X_test)

            overall_shap_values_list.append(shap_values_fold)
            overall_X_test_list.append(X_test)

            shap_importance_fold = pd.DataFrame(
                {
                    "fold": fold,
                    "feature": overall_features,
                    "mean_abs_shap": np.abs(shap_values_fold).mean(axis=0),
                }
            )

            overall_shap_importance_list.append(shap_importance_fold)

    all_metrics.append(
        {
            "target": target_name,
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
# 15. EXPORT CV RESULTS
# ============================================

metrics_df = pd.DataFrame(all_metrics)

metrics_path = OUTPUT_DIR / "catboost_cv_metrics_all_targets.csv"
metrics_df.to_csv(metrics_path, index=False, encoding="utf-8-sig")

print("\n===== ALL MODEL METRICS =====")
print(metrics_df)
print("\nSaved metrics to:", metrics_path)


predictions_df = pd.concat(all_preds, ignore_index=True)

predictions_long_path = OUTPUT_DIR / "catboost_predictions_long_all_targets.csv"
predictions_df.to_csv(predictions_long_path, index=False, encoding="utf-8-sig")

print("Saved long predictions to:", predictions_long_path)


wide_predictions_df = predictions_df.pivot_table(
    index=["file_name"],
    columns="target",
    values=["true_score", "pred_score"],
    aggfunc="first"
)

wide_predictions_df.columns = [
    f"{target}_{score_type}"
    for score_type, target in wide_predictions_df.columns
]

wide_predictions_df = wide_predictions_df.reset_index()

ordered_cols = [
    "file_name",

    "fluency_pred_score",
    "fluency_true_score",

    "lexical_pred_score",
    "lexical_true_score",

    "pronunciation_pred_score",
    "pronunciation_true_score",

    "overall_pred_score",
    "overall_true_score",
]

# Chỉ lấy các cột tồn tại để tránh lỗi nếu target nào đó thiếu
ordered_cols_existing = [
    col for col in ordered_cols
    if col in wide_predictions_df.columns
]

wide_predictions_df = wide_predictions_df[ordered_cols_existing]

wide_predictions_path = OUTPUT_DIR / "catboost_predictions_wide_all_targets.csv"
wide_predictions_df.to_csv(wide_predictions_path, index=False, encoding="utf-8-sig")

print("\n===== PREDICTION SAMPLE =====")
print(wide_predictions_df.head(20))
print("\nSaved wide predictions to:", wide_predictions_path)


# ============================================
# 16. COMBINE OVERALL SHAP VALUES FROM 5 FOLDS
# ============================================

if overall_shap_values_list and overall_X_test_list:

    overall_shap_values_cv = np.vstack(overall_shap_values_list)
    overall_X_test_cv = pd.concat(overall_X_test_list, axis=0)

    # SHAP importance table
    overall_shap_importance_df = pd.concat(
        overall_shap_importance_list,
        ignore_index=True
    )

    overall_shap_importance_summary = (
        overall_shap_importance_df
        .groupby("feature", as_index=False)["mean_abs_shap"]
        .mean()
        .sort_values("mean_abs_shap", ascending=False)
    )

    shap_importance_path = OUTPUT_DIR / "overall_shap_importance_cv.csv"
    overall_shap_importance_summary.to_csv(
        shap_importance_path,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n===== OVERALL SHAP IMPORTANCE =====")
    print(overall_shap_importance_summary)
    print("\nSaved SHAP importance to:", shap_importance_path)

    # SHAP summary dot plot
    plt.figure(figsize=(10, 7))

    shap.summary_plot(
        overall_shap_values_cv,
        overall_X_test_cv,
        feature_names=overall_features,
        show=False,
        max_display=len(overall_features)
    )

    plt.title(
        "SHAP Summary Plot - Overall Model across 5 CV Folds",
        fontsize=14
    )

    plt.tight_layout()

    shap_summary_path = OUTPUT_DIR / "overall_shap_summary_cv.png"
    plt.savefig(shap_summary_path, dpi=300, bbox_inches="tight")
    plt.close()

    print("Saved SHAP summary plot to:", shap_summary_path)


# ============================================
# 17. TRAIN FINAL MODELS ON FULL DATASET
# ============================================

final_models = {}

print("\n===== TRAIN FINAL MODELS ON FULL DATASET =====")

for target_name, target_column in targets.items():

    print(f"\n===== TRAIN FINAL MODEL FOR {target_name.upper()} =====")

    data = overall_df.dropna(subset=[target_column]).copy()

    X_final = data[overall_features]
    y_final = data[target_column]

    final_model = CatBoostRegressor(
        iterations=300,
        learning_rate=0.05,
        depth=4,
        loss_function="RMSE",
        random_seed=RANDOM_STATE,
        verbose=False
    )

    final_model.fit(X_final, y_final)

    final_models[target_name] = final_model

    model_path = MODEL_DIR / f"{target_name}_score_model.cbm"
    final_model.save_model(str(model_path))

    print(f"Saved {target_name} model to: {model_path}")


# ============================================
# 18. TRAIN FINAL OVERALL SHAP EXPLAINER SAMPLE
# ============================================

# Lưu background data để backend có thể dùng cho SHAP nếu cần
background_data = overall_df[overall_features].copy()

background_path = MODEL_DIR / "shap_background_data.csv"
background_data.to_csv(background_path, index=False, encoding="utf-8-sig")

print("\nSaved SHAP background data to:", background_path)


# ============================================
# 19. SAVE TRAINING METADATA
# ============================================

training_metadata = {
    "n_splits": N_SPLITS,
    "random_state": RANDOM_STATE,
    "features": overall_features,
    "targets": targets,
    "model_params": {
        "iterations": 300,
        "learning_rate": 0.05,
        "depth": 4,
        "loss_function": "RMSE",
        "random_seed": RANDOM_STATE,
        "verbose": False,
    },
    "saved_models": {
        target_name: str(MODEL_DIR / f"{target_name}_score_model.cbm")
        for target_name in targets.keys()
    },
}

metadata_path = MODEL_DIR / "training_metadata.json"

with open(metadata_path, "w", encoding="utf-8") as f:
    json.dump(training_metadata, f, ensure_ascii=False, indent=4)

print("Saved training metadata to:", metadata_path)


# ============================================
# 20. DONE
# ============================================

print("\n===== TRAINING COMPLETED SUCCESSFULLY =====")
print("Model directory:", MODEL_DIR)
print("Output directory:", OUTPUT_DIR)

print("\nExpected backend model file:")
print(MODEL_DIR / "overall_score_model.cbm")