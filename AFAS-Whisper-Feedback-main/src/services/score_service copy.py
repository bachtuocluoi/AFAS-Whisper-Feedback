"""
Score prediction service.

This service predicts speaking scores from extracted features and generates
local SHAP explanations for the OVERALL model only.

Important rule:
- Prediction:
    Each model uses feature_columns_by_model.json.
- SHAP:
    Only the overall model is explained, using feature_columns.json.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from catboost import CatBoostRegressor, Pool


# ============================================
# ROUNDING
# ============================================

def round_half(score: float) -> float:
    """
    Round score to IELTS-like 0.5 band using half-up rule.
    """
    score = float(score)
    score = max(0.0, min(9.0, score))

    return math.floor(score * 2 + 0.5 + 1e-12) / 2


# ============================================
# PATHS
# ============================================

# Current file: src/services/score_service.py
# parents[2] points to the project root.
BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = BASE_DIR / "ml_models"

# feature_columns.json is a LIST of all features used by the overall model.
FEATURE_COLUMNS_PATH = MODEL_DIR / "feature_columns.json"

# feature_columns_by_model.json is a DICT.
FEATURE_COLUMNS_BY_MODEL_PATH = MODEL_DIR / "feature_columns_by_model.json"

FEATURE_MEDIANS_PATH = MODEL_DIR / "feature_medians.json"

MODEL_PATHS = {
    "overall": MODEL_DIR / "overall_score_model.cbm",
    "fluency": MODEL_DIR / "fluency_score_model.cbm",
    "lexical": MODEL_DIR / "lexical_score_model.cbm",
    "pronunciation": MODEL_DIR / "pronunciation_score_model.cbm",
}


# ============================================
# CACHE
# ============================================

_MODEL_CACHE: Dict[str, CatBoostRegressor] = {}
_JSON_CACHE: Dict[str, Any] = {}


# ============================================
# LOAD HELPERS
# ============================================

def _load_json(path: Path) -> Any:
    """
    Load and cache JSON file.
    """
    cache_key = str(path)

    if cache_key in _JSON_CACHE:
        return _JSON_CACHE[cache_key]

    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    _JSON_CACHE[cache_key] = data

    return data


def load_overall_feature_columns() -> List[str]:
    """
    Load feature_columns.json.

    This file must be a list because it is used as:
        X[overall_feature_columns]

    It is used for:
    - building the full 14-feature input
    - overall SHAP explanation
    """
    feature_columns = _load_json(FEATURE_COLUMNS_PATH)

    if not isinstance(feature_columns, list):
        raise TypeError(
            "feature_columns.json must be a list of feature names."
        )

    return feature_columns


def load_features_by_model() -> Dict[str, List[str]]:
    """
    Load feature_columns_by_model.json.

    This file must be a dictionary:
    {
        "fluency": [...],
        "lexical": [...],
        "pronunciation": [...],
        "overall": [...]
    }
    """
    features_by_model = _load_json(FEATURE_COLUMNS_BY_MODEL_PATH)

    if not isinstance(features_by_model, dict):
        raise TypeError(
            "feature_columns_by_model.json must be a dictionary, "
            "not a list."
        )

    required_targets = [
        "overall",
        "fluency",
        "lexical",
        "pronunciation",
    ]

    for target_name in required_targets:
        if target_name not in features_by_model:
            raise KeyError(
                f"Missing key '{target_name}' in "
                "feature_columns_by_model.json"
            )

        if not isinstance(features_by_model[target_name], list):
            raise TypeError(
                f"features_by_model['{target_name}'] must be a list."
            )

    return features_by_model


def _load_model(model_path: Path) -> CatBoostRegressor:
    """
    Load a CatBoost model from disk.
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model = CatBoostRegressor()
    model.load_model(str(model_path))

    return model


def load_score_model(target_name: str) -> CatBoostRegressor:
    """
    Load and cache a CatBoost model by target name.
    """
    if target_name in _MODEL_CACHE:
        return _MODEL_CACHE[target_name]

    if target_name not in MODEL_PATHS:
        raise ValueError(f"Unknown target name: {target_name}")

    model = _load_model(MODEL_PATHS[target_name])
    _MODEL_CACHE[target_name] = model

    return model


# ============================================
# FEATURE BUILDING
# ============================================

def build_score_features(
    fluency_data: Dict[str, Any],
    lexical_cefr: Dict[str, Any],
    lexical_diversity: Dict[str, Any],
    pronunciation_data: Dict[str, Any],
) -> pd.DataFrame:
    """
    Build one-row DataFrame containing all 14 overall features.

    Later:
    - each score model selects its own columns from feature_columns_by_model.json
    - SHAP selects overall columns from feature_columns.json
    """

    overall_feature_columns = load_overall_feature_columns()
    feature_medians = _load_json(FEATURE_MEDIANS_PATH)

    feature_dict = {
        # Fluency
        "flu_speech_rate": fluency_data.get("speech_rate", 0.0),
        "flu_pause_ratio": fluency_data.get("pause_ratio", 0.0),

        # Lexical diversity
        "lex_TTR": lexical_diversity.get("ttr", 0.0),
        "lex_MSTTR": lexical_diversity.get("msttr", 0.0),

        # Lexical CEFR distribution
        "lex_A1": lexical_cefr.get("a1", 0.0),
        "lex_A2": lexical_cefr.get("a2", 0.0),
        "lex_B1": lexical_cefr.get("b1", 0.0),
        "lex_B2": lexical_cefr.get("b2", 0.0),
        "lex_C1": lexical_cefr.get("c1", 0.0),

        # Pronunciation confidence distribution
        "pro_0%-50%": pronunciation_data.get("score_0_50", 0.0),
        "pro_50%-70%": pronunciation_data.get("score_50_70", 0.0),
        "pro_70%-85%": pronunciation_data.get("score_70_85", 0.0),
        "pro_85%-95%": pronunciation_data.get("score_85_95", 0.0),
        "pro_95%-100%": pronunciation_data.get("score_95_100", 0.0),
    }

    X = pd.DataFrame([feature_dict])

    for col in overall_feature_columns:
        if col not in X.columns:
            X[col] = feature_medians.get(col, 0.0)

        X[col] = pd.to_numeric(X[col], errors="coerce")
        X[col] = X[col].fillna(feature_medians.get(col, 0.0))

    # IMPORTANT:
    # overall_feature_columns comes from feature_columns.json, so it is a list.
    X = X[overall_feature_columns]

    return X


def select_features_for_prediction(
    X_all: pd.DataFrame,
    target_name: str,
) -> pd.DataFrame:
    """
    Select correct feature columns for model prediction.

    This uses feature_columns_by_model.json.
    """
    features_by_model = load_features_by_model()

    if target_name not in features_by_model:
        raise ValueError(f"Unknown target name: {target_name}")

    target_features = features_by_model[target_name]

    missing_cols = [
        col for col in target_features
        if col not in X_all.columns
    ]

    if missing_cols:
        raise ValueError(
            f"Missing feature columns for {target_name}: "
            + ", ".join(missing_cols)
        )

    return X_all[target_features]


def select_features_for_overall_shap(
    X_all: pd.DataFrame,
) -> pd.DataFrame:
    """
    Select feature columns for overall SHAP.

    This uses feature_columns.json, not feature_columns_by_model.json.
    """
    overall_feature_columns = load_overall_feature_columns()

    missing_cols = [
        col for col in overall_feature_columns
        if col not in X_all.columns
    ]

    if missing_cols:
        raise ValueError(
            "Missing overall SHAP feature columns: "
            + ", ".join(missing_cols)
        )

    return X_all[overall_feature_columns]


# ============================================
# PREDICTION HELPERS
# ============================================

def clip_score(score: float) -> float:
    """
    Clip predicted score to IELTS-like range 0-9.
    """
    return max(0.0, min(9.0, float(score)))


def _predict_score(
    model: CatBoostRegressor,
    X: pd.DataFrame,
) -> float:
    """
    Predict raw score using loaded CatBoost model.
    """
    pred = model.predict(X)[0]
    return clip_score(pred)


# ============================================
# SHAP
# ============================================

def _make_overall_local_shap_dict(
    model: CatBoostRegressor,
    X_overall: pd.DataFrame,
    prediction_raw: float,
    prediction_rounded: float,
) -> dict:
    """
    Create local SHAP explanation for the overall model only.

    X_overall must use feature_columns.json.
    """

    shap_values = model.get_feature_importance(
        data=Pool(X_overall),
        type="ShapValues",
    )

    # CatBoost returns shape: [n_samples, n_features + 1]
    # Last value is expected value / base value.
    row_shap = shap_values[0][:-1]
    base_value = shap_values[0][-1]

    result = {
        "base_value": round(float(base_value), 4),
        "prediction_raw": round(float(prediction_raw), 4),
        "prediction": round(float(prediction_rounded), 1),
        "features": [],
    }

    for feature_name, feature_value, shap_value in zip(
        X_overall.columns,
        X_overall.iloc[0].values,
        row_shap,
    ):
        result["features"].append(
            {
                "feature": feature_name,
                "feature_value": round(float(feature_value), 4),
                "shap_value": round(float(shap_value), 4),
                "impact": "increase" if shap_value >= 0 else "decrease",
            }
        )

    result["features"] = sorted(
        result["features"],
        key=lambda item: abs(item["shap_value"]),
        reverse=True,
    )

    return result


# ============================================
# MAIN SERVICE FUNCTION
# ============================================

def predict_scores_with_shap_from_features(
    fluency_data: Dict[str, Any],
    lexical_cefr: Dict[str, Any],
    lexical_diversity: Dict[str, Any],
    pronunciation_data: Dict[str, Any],
) -> dict:
    """
    Predict scores and compute overall SHAP explanation.

    Rules:
    1. Build all 14 features once.
    2. Predict each model using feature_columns_by_model.json.
    3. Explain only the overall model using feature_columns.json.
    """

    X_all = build_score_features(
        fluency_data=fluency_data,
        lexical_cefr=lexical_cefr,
        lexical_diversity=lexical_diversity,
        pronunciation_data=pronunciation_data,
    )

    output = {
        "scores": {},
        "raw_scores": {},
        "shap": {},
    }

    overall_prediction_raw = None
    overall_prediction_rounded = None

    for target_name in [
        "overall",
        "fluency",
        "lexical",
        "pronunciation",
    ]:
        model = load_score_model(target_name)

        # Prediction uses feature_columns_by_model.json.
        X_target = select_features_for_prediction(
            X_all=X_all,
            target_name=target_name,
        )

        prediction_raw = _predict_score(
            model=model,
            X=X_target,
        )

        prediction_rounded = round_half(prediction_raw)

        #print("====", target_name, "====")
        #print("features:", list(X_target.columns))
        #print("shape:", X_target.shape)
        #print("raw:", prediction_raw)
        #print("rounded:", prediction_rounded)

        output["scores"][f"{target_name}_score"] = round(
            float(prediction_rounded),
            1,
        )

        output["raw_scores"][f"{target_name}_score"] = round(
            float(prediction_raw),
            4,
        )

        if target_name == "overall":
            overall_prediction_raw = prediction_raw
            overall_prediction_rounded = prediction_rounded

    # SHAP only for the overall model.
    overall_model = load_score_model("overall")
    X_overall_shap = select_features_for_overall_shap(X_all)

    output["shap"]["overall"] = _make_overall_local_shap_dict(
        model=overall_model,
        X_overall=X_overall_shap,
        prediction_raw=overall_prediction_raw,
        prediction_rounded=overall_prediction_rounded,
    )

    return output