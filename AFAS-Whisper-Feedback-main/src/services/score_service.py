
"""
Score prediction service.

This service predicts speaking scores from extracted features and generates
local SHAP explanations for each prediction.

Pipeline:
audio -> transcript -> features -> feedback -> score + SHAP
"""

import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from catboost import CatBoostRegressor, Pool


# File hiện tại: src/services/score_service.py
# parents[2] trỏ về root project
BASE_DIR = Path(__file__).resolve().parents[2]


# ============================================
# MODEL DIRECTORY
# ============================================

MODEL_DIR = BASE_DIR / "ml_models"

FEATURE_COLUMNS_PATH = MODEL_DIR / "feature_columns.json"
FEATURE_MEDIANS_PATH = MODEL_DIR / "feature_medians.json"

MODEL_PATHS = {
    "overall": MODEL_DIR / "overall_score_model.cbm",
    "fluency": MODEL_DIR / "fluency_score_model.cbm",
    "lexical": MODEL_DIR / "lexical_score_model.cbm",
    "pronunciation": MODEL_DIR / "pronunciation_score_model.cbm",
}


# Cache loaded models to avoid loading model files repeatedly
_MODEL_CACHE = {}


# ============================================
# LOAD HELPERS
# ============================================

def _load_json(path: Path):
    """
    Load a JSON file.

    Args:
        path: Path to JSON file

    Returns:
        Parsed JSON object

    Raises:
        FileNotFoundError: If file does not exist
    """

    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_model(model_path: Path) -> CatBoostRegressor:
    """
    Load a CatBoost model from disk.

    Args:
        model_path: Path to .cbm model file

    Returns:
        Loaded CatBoostRegressor model

    Raises:
        FileNotFoundError: If model file does not exist
    """

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model = CatBoostRegressor()
    model.load_model(str(model_path))

    return model


def load_score_model(target_name: str) -> CatBoostRegressor:
    """
    Load and cache a CatBoost model by target name.

    Args:
        target_name: One of overall, fluency, lexical, pronunciation

    Returns:
        Loaded CatBoostRegressor model
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
    pronunciation_data: Dict[str, Any]
) -> pd.DataFrame:
    """
    Build model input DataFrame from extracted feature dictionaries.

    This function maps runtime feature names to the exact feature names
    used during model training.

    Args:
        fluency_data: Output from compute_fluency_metrics()
        lexical_cefr: Output from compute_lexical_cefr_metrics()
        lexical_diversity: Output from compute_lexical_diversity_metrics()
        pronunciation_data: Output from compute_pronunciation_metrics()

    Returns:
        One-row pandas DataFrame with feature columns in training order
    """

    feature_columns = _load_json(FEATURE_COLUMNS_PATH)
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

    for col in feature_columns:
        if col not in X.columns:
            X[col] = feature_medians.get(col, 0.0)

        X[col] = pd.to_numeric(X[col], errors="coerce")
        X[col] = X[col].fillna(feature_medians.get(col, 0.0))

    X = X[feature_columns]

    return X


# ============================================
# PREDICTION HELPERS
# ============================================

def clip_score(score: float) -> float:
    """
    Clip predicted score to IELTS-like range 0-9.

    Args:
        score: Raw predicted score

    Returns:
        Score within [0, 9]
    """

    return max(0.0, min(9.0, float(score)))


def _predict_score(model: CatBoostRegressor, X: pd.DataFrame) -> float:
    """
    Predict score using a loaded CatBoost model.

    Args:
        model: Loaded CatBoost model
        X: Feature DataFrame

    Returns:
        Clipped predicted score
    """

    pred = model.predict(X)[0]
    return clip_score(pred)


# ============================================
# SHAP
# ============================================

def _make_local_shap_dict(
    model: CatBoostRegressor,
    X: pd.DataFrame,
    prediction: float
) -> dict:
    """
    Create local SHAP explanation for one predicted sample.

    Args:
        model: CatBoost model used for prediction
        X: One-row feature DataFrame
        prediction: Predicted score

    Returns:
        Dictionary containing base value, prediction, and feature contributions
    """

    shap_values = model.get_feature_importance(
        data=Pool(X),
        type="ShapValues"
    )

    # CatBoost returns shape: [n_samples, n_features + 1]
    # Last value is the expected value / base value
    row_shap = shap_values[0][:-1]
    base_value = shap_values[0][-1]

    result = {
        "base_value": round(float(base_value), 4),
        "prediction": round(float(prediction), 2),
        "features": []
    }

    for feature_name, feature_value, shap_value in zip(
        X.columns,
        X.iloc[0].values,
        row_shap
    ):
        result["features"].append({
            "feature": feature_name,
            "feature_value": round(float(feature_value), 4),
            "shap_value": round(float(shap_value), 4),
            "impact": "increase" if shap_value >= 0 else "decrease"
        })

    result["features"] = sorted(
        result["features"],
        key=lambda item: abs(item["shap_value"]),
        reverse=True
    )

    return result


# ============================================
# MAIN SERVICE FUNCTION
# ============================================

def predict_scores_with_shap_from_features(
    fluency_data: Dict[str, Any],
    lexical_cefr: Dict[str, Any],
    lexical_diversity: Dict[str, Any],
    pronunciation_data: Dict[str, Any]
) -> dict:
    """
    Predict scores and compute local SHAP explanations from extracted features.

    Args:
        fluency_data: Fluency features
        lexical_cefr: CEFR lexical distribution
        lexical_diversity: Lexical diversity features
        pronunciation_data: Pronunciation confidence features

    Returns:
        Dictionary containing:
        - scores: predicted score values
        - shap: local SHAP explanation for each score target
    """

    X = build_score_features(
        fluency_data=fluency_data,
        lexical_cefr=lexical_cefr,
        lexical_diversity=lexical_diversity,
        pronunciation_data=pronunciation_data
    )

    output = {
        "scores": {},
        "shap": {}
    }

    for target_name in ["overall", "fluency", "lexical", "pronunciation"]:
        model = load_score_model(target_name)

        prediction = _predict_score(model, X)

        output["scores"][f"{target_name}_score"] = round(float(prediction), 2)

        output["shap"][target_name] = _make_local_shap_dict(
            model=model,
            X=X,
            prediction=prediction
        )

    return output