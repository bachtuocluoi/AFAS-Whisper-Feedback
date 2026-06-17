# ============================================
# LINEAR REGRESSION VERSION - ALL TARGETS
# ============================================
# - Train 4 model riêng: fluency, lexical, pronunciation, overall
# - Overall model dùng toàn bộ feature gốc của 3 nhóm
# - Không dùng prediction của 3 model con làm feature cho overall
# - Dùng 5-fold cross validation
# - Export metrics, prediction, coefficients, final model

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
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
GRAMMAR_FILE = DATA_DIR / "grammar.csv"
LEX_SOPH_FILE = DATA_DIR / "lexical_sophistication.csv"
LEX_DIV_FILE = DATA_DIR / "lexical_diversity.csv"


# ============================================
# OUTPUT DIRECTORIES
# ============================================

MODEL_DIR = BASE_DIR / "ml_models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

N_SPLITS = 5
RANDOM_STATE = 42
MODEL_TYPE = "linear_regression_with_standard_scaler"


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
    observed = np.zeros((n, n), dtype=float)

    for actual_value, predicted_value in zip(y_true, y_pred):
        observed[actual_value, predicted_value] += 1

    hist_true = np.bincount(y_true, minlength=n)
    hist_pred = np.bincount(y_pred, minlength=n)

    if len(y_true) == 0:
        return np.nan

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


def extract_file_name_number(df, source_col="file"):
    """
    Extract numeric file_name from file column.

    Example:
        1_prob.csv -> 1
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
    Create one Linear Regression model.

    StandardScaler is used because:
    - Features have different scales.
    - Coefficients become easier to compare.
    - LinearRegression itself is still the final prediction model.
    """
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("linear_regression", LinearRegression()),
        ]
    )


def predict_score(model, X):
    """
    Predict score and clip into IELTS score range 0-9.

    Nếu chị muốn so sánh tuyệt đối với CatBoost bản cũ,
    có thể bỏ np.clip và return trực tiếp model.predict(X).
    """
    y_pred = model.predict(X)
    y_pred = np.clip(y_pred, 0, 9)
    return y_pred


def extract_linear_coefficients(model, feature_names):
    """
    Extract standardized coefficients from Linear Regression pipeline.

    Vì model có StandardScaler ở trước LinearRegression,
    hệ số ở đây là hệ số sau chuẩn hóa feature.
    Nghĩa là có thể so sánh độ lớn tương đối giữa các feature tốt hơn.
    """
    linear_model = model.named_steps["linear_regression"]

    coefficient_df = pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient": linear_model.coef_,
        }
    )

    coefficient_df["abs_coefficient"] = coefficient_df["coefficient"].abs()

    coefficient_df = coefficient_df.sort_values(
        "abs_coefficient",
        ascending=False,
    )

    return coefficient_df


# ============================================
# 2. CHECK INPUT FILES
# ============================================

for file_path in [
    SCORES_FILE,
    FLUENCY_FILE,
    PRON_FILE,
    GRAMMAR_FILE,
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

# Xóa khoảng trắng ẩn trong tên cột
score_df.columns = score_df.columns.astype(str).str.strip()

print("===== SCORE FILE PATH =====")
print(SCORES_FILE)

print("===== SCORE COLUMNS =====")
print(score_df.columns.tolist())

score_df["class_name"] = score_df["class_name"].astype(str)
score_df["file_name"] = pd.to_numeric(
    score_df["file_name"],
    errors="coerce",
).astype("Int64")


# ============================================
# 4. LOAD FLUENCY FEATURES
# ============================================

fluency_df = pd.read_csv(FLUENCY_FILE)
fluency_df.columns = fluency_df.columns.astype(str).str.strip()

fluency_df["class_name"] = fluency_df["class_name"].astype(str)
fluency_df = extract_file_name_number(fluency_df, source_col="file")

fluency_df = fluency_df.rename(
    columns={
        "speech_rate_wps": "flu_speech_rate",
        "ratio_pauses_to_duration": "flu_pause_ratio",
    }
)

fluency_df = fluency_df[
    [
        "class_name",
        "file_name",
        "flu_speech_rate",
        "flu_pause_ratio",
    ]
]


# ============================================
# 5. LOAD LEXICAL DIVERSITY FEATURES
# ============================================

lex_div_df = pd.read_csv(LEX_DIV_FILE)
lex_div_df.columns = lex_div_df.columns.astype(str).str.strip()

lex_div_df["class_name"] = lex_div_df["class_name"].astype(str)
lex_div_df = extract_file_name_number(lex_div_df, source_col="file")

lex_div_df = lex_div_df.rename(
    columns={
        "TTR": "lex_TTR",
        "MSTTR": "lex_MSTTR",
    }
)

lex_div_df = lex_div_df[
    [
        "class_name",
        "file_name",
        "lex_TTR",
        "lex_MSTTR",
    ]
]


# ============================================
# 6. LOAD LEXICAL SOPHISTICATION FEATURES
# ============================================

lex_soph_df = pd.read_csv(LEX_SOPH_FILE)
lex_soph_df.columns = lex_soph_df.columns.astype(str).str.strip()

lex_soph_df["class_name"] = lex_soph_df["class_name"].astype(str)
lex_soph_df = extract_file_name_number(lex_soph_df, source_col="file")

lex_soph_df = lex_soph_df.rename(
    columns={
        "A1": "lex_A1",
        "A2": "lex_A2",
        "B1": "lex_B1",
        "B2": "lex_B2",
        "C1": "lex_C1",
    }
)

lex_soph_df = lex_soph_df[
    [
        "class_name",
        "file_name",
        "lex_A1",
        "lex_A2",
        "lex_B1",
        "lex_B2",
        "lex_C1",
    ]
]


lex_df = lex_div_df.merge(
    lex_soph_df,
    on=["class_name", "file_name"],
    how="inner",
)

# ============================================
# 8. LOAD PRONUNCIATION FEATURES
# ============================================

pron_df = pd.read_csv(PRON_FILE)
pron_df.columns = pron_df.columns.astype(str).str.strip()

pron_df["class_name"] = pron_df["class_name"].astype(str)
pron_df = extract_file_name_number(pron_df, source_col="file")

pron_df = pron_df.rename(
    columns={
        "0-50%": "pro_0%-50%",
        "50-70%": "pro_50%-70%",
        "70-85%": "pro_70%-85%",
        "85-95%": "pro_85%-95%",
        "95-100%": "pro_95%-100%",
    }
)

pron_df = pron_df[
    [
        "class_name",
        "file_name",
        "pro_0%-50%",
        "pro_50%-70%",
        "pro_70%-85%",
        "pro_85%-95%",
        "pro_95%-100%",
    ]
]


# ============================================
# 9. LOAD GRAMMAR FEATURES
# ============================================

grammar_df = pd.read_csv(GRAMMAR_FILE)
grammar_df.columns = grammar_df.columns.astype(str).str.strip()

grammar_df["class_name"] = grammar_df["class_name"].astype(str)
grammar_df = extract_file_name_number(grammar_df, source_col="file")

grammar_df = grammar_df.rename(
    columns={
        "ratio_error_sentences": "gra_ratio_error_sentences",
        "total_errors": "gra_total_errors",
        "error_rate": "gra_error_rate",
    }
)

grammar_df = grammar_df[
    [
        "class_name",
        "file_name",
        "gra_ratio_error_sentences",
        "gra_total_errors",
        "gra_error_rate",
    ]
]

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
    "avg_grammar",
]

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

        # Grammar
        "ratio_error_sentences": "gra_ratio_error_sentences",
        "total_errors": "gra_total_errors",
        "error_rate": "gra_error_rate",
    }
)


# ============================================
# 11. DEFINE FEATURES FOR EACH MODEL
# ============================================

fluency_features = [
    "flu_speech_rate",
    "flu_pause_ratio",
]

lexical_features = [
    "lex_TTR",
    "lex_MSTTR",
    "lex_A1",
    "lex_A2",
    "lex_B1",
    "lex_B2",
    "lex_C1",
]

pronunciation_features = [
    "pro_0%-50%",
    "pro_50%-70%",
    "pro_70%-85%",
    "pro_85%-95%",
    "pro_95%-100%",
]

grammar_features = [
    "gra_ratio_error_sentences",
    "gra_total_errors",
    "gra_error_rate",
]

# Overall model dùng toàn bộ feature gốc của ba nhóm.
# Không dùng prediction của ba model con làm feature.
overall_features = (
    fluency_features
    + lexical_features
    + pronunciation_features
    + grammar_features
)

# Train ba model thành phần trước, sau đó train overall model.
targets = {
    "fluency": "avg_fluency",
    "lexical": "avg_lexical",
    "pronunciation": "avg_pronunciation",
    "grammar": "avg_grammar",
    "overall": "avg_overall",
}

features_by_model = {
    "fluency": fluency_features,
    "lexical": lexical_features,
    "pronunciation": pronunciation_features,
    "grammar": grammar_features,
    "overall": overall_features,
}


# ============================================
# 12. CHECK REQUIRED COLUMNS
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

    if pd.isna(median_value):
        raise ValueError(
            f"Feature '{col}' has no valid numeric value after merge."
        )

    feature_medians[col] = float(median_value)
    overall_df[col] = overall_df[col].fillna(median_value)


# ============================================
# 14. SAVE FEATURE CONFIGURATION FOR BACKEND
# ============================================

# Giữ file cũ để tương thích với phần backend đang dùng overall model.
feature_columns_path = MODEL_DIR / "feature_columns.json"

with open(feature_columns_path, "w", encoding="utf-8") as file:
    json.dump(overall_features, file, ensure_ascii=False, indent=4)

print("\nSaved overall feature columns to:", feature_columns_path)


# File mới: lưu đúng feature theo từng model.
feature_columns_by_model_path = MODEL_DIR / "feature_columns_by_model.json"

with open(feature_columns_by_model_path, "w", encoding="utf-8") as file:
    json.dump(features_by_model, file, ensure_ascii=False, indent=4)

print("Saved feature columns by model to:", feature_columns_by_model_path)


# Lưu median để backend có thể fill feature thiếu trước khi predict.
feature_medians_path = MODEL_DIR / "feature_medians.json"

with open(feature_medians_path, "w", encoding="utf-8") as file:
    json.dump(feature_medians, file, ensure_ascii=False, indent=4)

print("Saved feature medians to:", feature_medians_path)


# ============================================
# 15. PREPARE 5-FOLD CROSS VALIDATION
# ============================================

kf = KFold(
    n_splits=N_SPLITS,
    shuffle=True,
    random_state=RANDOM_STATE,
)

all_metrics = []
all_preds = []

# Với Linear Regression, thay SHAP bằng coefficient.
# Chỉ tổng hợp coefficient theo 5 fold cho overall model.
overall_coefficient_list = []


# ============================================
# 16. RUN 5-FOLD CROSS VALIDATION
# ============================================

print("\n===== START 5-FOLD CROSS VALIDATION =====")

for target_name, target_column in targets.items():
    print(f"\n===== TARGET: {target_name.upper()} =====")

    current_features = features_by_model[target_name]

    print("Features:", current_features)
    print("Model type:", MODEL_TYPE)

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

    for fold, (train_idx, test_idx) in enumerate(kf.split(X_target), start=1):
        X_train = X_target.iloc[train_idx]
        X_test = X_target.iloc[test_idx]

        y_train = y_target.iloc[train_idx]
        y_test = y_target.iloc[test_idx]

        model = create_model()
        model.fit(X_train, y_train)

        y_pred = predict_score(model, X_test)

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
        # SAVE COEFFICIENTS ONLY FOR OVERALL TARGET
        # ============================================
        if target_name == "overall":
            coefficient_df = extract_linear_coefficients(
                model=model,
                feature_names=current_features,
            )

            coefficient_df.insert(0, "fold", fold)
            overall_coefficient_list.append(coefficient_df)

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
# 17. EXPORT CV RESULTS
# ============================================

metrics_df = pd.DataFrame(all_metrics)

metrics_path = OUTPUT_DIR / "linear_regression_cv_metrics_all_targets.csv"
metrics_df.to_csv(metrics_path, index=False, encoding="utf-8-sig")

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
# 18. COMBINE OVERALL COEFFICIENTS FROM 5 FOLDS
# ============================================

if overall_coefficient_list:
    overall_coefficients_cv = pd.concat(
        overall_coefficient_list,
        ignore_index=True,
    )

    coefficients_cv_path = OUTPUT_DIR / "overall_linear_coefficients_cv_detail.csv"
    overall_coefficients_cv.to_csv(
        coefficients_cv_path,
        index=False,
        encoding="utf-8-sig",
    )

    overall_coefficient_summary = (
        overall_coefficients_cv
        .groupby("feature", as_index=False)
        .agg(
            coefficient_mean=("coefficient", "mean"),
            coefficient_std=("coefficient", "std"),
            abs_coefficient_mean=("abs_coefficient", "mean"),
            abs_coefficient_std=("abs_coefficient", "std"),
        )
        .sort_values("abs_coefficient_mean", ascending=False)
    )

    coefficients_summary_path = OUTPUT_DIR / "overall_linear_coefficients_cv_summary.csv"
    overall_coefficient_summary.to_csv(
        coefficients_summary_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n===== OVERALL LINEAR COEFFICIENT SUMMARY FROM CV =====")
    print(overall_coefficient_summary)
    print("\nSaved coefficient detail to:", coefficients_cv_path)
    print("Saved coefficient summary to:", coefficients_summary_path)


# ============================================
# 19. TRAIN FINAL MODELS ON FULL DATASET
# ============================================

final_models = {}
final_coefficient_list = []

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

    coefficient_df = extract_linear_coefficients(
        model=final_model,
        feature_names=current_features,
    )

    coefficient_df.insert(0, "target", target_name)
    final_coefficient_list.append(coefficient_df)

    intercept = final_model.named_steps["linear_regression"].intercept_

    print("Features:", current_features)
    print("Intercept:", intercept)
    print(f"Saved {target_name} model to: {model_path}")


# ============================================
# 20. SAVE FINAL LINEAR COEFFICIENTS
# ============================================

final_coefficients_df = pd.concat(
    final_coefficient_list,
    ignore_index=True,
)

final_coefficients_path = OUTPUT_DIR / "linear_regression_final_coefficients_all_targets.csv"
final_coefficients_df.to_csv(
    final_coefficients_path,
    index=False,
    encoding="utf-8-sig",
)

print("\n===== FINAL LINEAR COEFFICIENTS =====")
print(final_coefficients_df)
print("\nSaved final coefficients to:", final_coefficients_path)


# Vẽ biểu đồ coefficient cho final overall model.
overall_final_coefficients = final_coefficients_df[
    final_coefficients_df["target"] == "overall"
].copy()

overall_final_coefficients = overall_final_coefficients.sort_values(
    "coefficient",
    ascending=True,
)

plt.figure(figsize=(10, 7))
plt.barh(
    overall_final_coefficients["feature"],
    overall_final_coefficients["coefficient"],
)
plt.axvline(0, linewidth=1)
plt.title("Linear Regression Coefficients - Final Overall Model", fontsize=14)
plt.xlabel("Standardized coefficient")
plt.tight_layout()

coefficient_plot_path = OUTPUT_DIR / "overall_linear_coefficients_final.png"
plt.savefig(coefficient_plot_path, dpi=300, bbox_inches="tight")
plt.close()

print("Saved overall coefficient plot to:", coefficient_plot_path)


# ============================================
# 21. SAVE BACKGROUND DATA
# ============================================

# Lưu toàn bộ feature để backend có thể chọn cột theo model khi cần giải thích.
background_data = overall_df[overall_features].copy()

background_path = MODEL_DIR / "linear_background_data.csv"
background_data.to_csv(
    background_path,
    index=False,
    encoding="utf-8-sig",
)

print("\nSaved background data to:", background_path)


# ============================================
# 22. SAVE TRAINING METADATA
# ============================================

training_metadata = {
    "model_type": MODEL_TYPE,
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
        "linear_background_data": str(background_path),
    },
    "saved_output_files": {
        "metrics": str(metrics_path),
        "predictions_long": str(predictions_long_path),
        "predictions_wide": str(wide_predictions_path),
        "final_coefficients": str(final_coefficients_path),
        "overall_coefficient_plot": str(coefficient_plot_path),
    },
}

metadata_path = MODEL_DIR / "linear_regression_training_metadata.json"

with open(metadata_path, "w", encoding="utf-8") as file:
    json.dump(training_metadata, file, ensure_ascii=False, indent=4)

print("Saved training metadata to:", metadata_path)


# ============================================
# 23. DONE
# ============================================

print("\n===== LINEAR REGRESSION TRAINING COMPLETED SUCCESSFULLY =====")
print("Model directory:", MODEL_DIR)
print("Output directory:", OUTPUT_DIR)

print("\nSaved final model files:")
for target_name in targets:
    print("-", MODEL_DIR / f"{target_name}_score_model_linear.pkl")
