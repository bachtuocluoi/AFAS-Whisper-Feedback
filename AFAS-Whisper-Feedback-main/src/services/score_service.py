"""
Score prediction service using Linear Regression models.

This service predicts speaking scores from extracted features and generates
local explanation values for the OVERALL linear regression model.

Important rule:
- Prediction:
    Each model uses feature_columns_by_model.json.
- Explanation:
    Only the overall model is explained, using feature_columns.json.

For Linear Regression with StandardScaler:
    local contribution = coefficient * standardized_feature_value

This keeps the same output structure as SHAP:
{
    "shap": {
        "overall": {
            "base_value": ...,
            "prediction_raw": ...,
            "prediction": ...,
            "features": [...]
        }
    }
}
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import pandas as pd


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

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = BASE_DIR / "ml_models"

FEATURE_COLUMNS_PATH = MODEL_DIR / "feature_columns.json"
FEATURE_COLUMNS_BY_MODEL_PATH = MODEL_DIR / "feature_columns_by_model.json"
FEATURE_MEDIANS_PATH = MODEL_DIR / "feature_medians.json"

MODEL_PATHS = {
    "overall": MODEL_DIR / "overall_score_model_linear.pkl",
    "fluency": MODEL_DIR / "fluency_score_model_linear.pkl",
    "lexical": MODEL_DIR / "lexical_score_model_linear.pkl",
    "pronunciation": MODEL_DIR / "pronunciation_score_model_linear.pkl",
    "grammar": MODEL_DIR / "grammar_score_model_linear.pkl",
}


# ============================================
# CACHE
# ============================================

_MODEL_CACHE: Dict[str, Any] = {}
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
    - building the full feature input
    - overall explanation
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

    This file must contain feature lists for component models:
    {
        "fluency": [...],
        "lexical": [...],
        "pronunciation": [...],
        "grammar": [...]
    }

    Overall score is NOT predicted by a model anymore.
    Overall = (fluency + lexical + pronunciation + grammar) / 4
    """
    features_by_model = _load_json(FEATURE_COLUMNS_BY_MODEL_PATH)

    if not isinstance(features_by_model, dict):
        raise TypeError(
            "feature_columns_by_model.json must be a dictionary."
        )

    required_targets = [
        "fluency",
        "lexical",
        "pronunciation",
        "grammar",
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


def _load_model(model_path: Path) -> Any:
    """
    Load a Linear Regression pipeline from disk.

    Expected model format:
        Pipeline([
            ("scaler", StandardScaler()),
            ("linear_regression", LinearRegression())
        ])
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    return joblib.load(model_path)


def load_score_model(target_name: str) -> Any:
    """
    Load and cache a Linear Regression model by target name.
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
    grammar_data: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """
    Build one-row DataFrame containing all overall features.

    Later:
    - each score model selects its own columns from feature_columns_by_model.json
    - explanation selects overall columns from feature_columns.json
    """

    if grammar_data is None:
        grammar_data = {}

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

        # Grammar
        "gra_ratio_error_sentences": grammar_data.get("ratio_error_sentences",0.0,),
        "gra_total_errors": grammar_data.get("total_errors", 0.0),
        "gra_error_rate": grammar_data.get("error_rate", 0.0),
    }

    X = pd.DataFrame([feature_dict])

    for col in overall_feature_columns:
        if col not in X.columns:
            X[col] = feature_medians.get(col, 0.0)

        X[col] = pd.to_numeric(X[col], errors="coerce")
        X[col] = X[col].fillna(feature_medians.get(col, 0.0))

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


def select_features_for_overall_explanation(
    X_all: pd.DataFrame,
) -> pd.DataFrame:
    """
    Select feature columns for overall explanation.

    This uses feature_columns.json.
    """
    overall_feature_columns = load_overall_feature_columns()

    missing_cols = [
        col for col in overall_feature_columns
        if col not in X_all.columns
    ]

    if missing_cols:
        raise ValueError(
            "Missing overall explanation feature columns: "
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


def _predict_raw_score(
    model: Any,
    X: pd.DataFrame,
) -> float:
    """
    Predict raw score using loaded Linear Regression model.
    """
    pred = model.predict(X)[0]
    return float(pred)


# ============================================
# LINEAR EXPLANATION
# ============================================

# ============================================
# OVERALL AVERAGE EXPLANATION
# ============================================

def _make_overall_average_shap_dict(
    component_scores: Dict[str, float],
    overall_raw: float,
    overall_rounded: float,
) -> dict:
    """
    Create explanation for overall score.

    Overall is no longer predicted by a Linear Regression model.

    Formula:
        overall = (
            fluency_score
            + lexical_score
            + pronunciation_score
            + grammar_score
        ) / 4

    To keep the old frontend structure, this function returns a SHAP-like dict.
    Each component contributes score / 4 to the final overall score.
    """

    result = {
        "base_value": 0.0,
        "prediction_raw": round(float(overall_raw), 4),
        "prediction": round(float(overall_rounded), 1),
        "features": [],
    }

    for target_name in [
        "fluency",
        "lexical",
        "pronunciation",
        "grammar",
    ]:
        score = float(component_scores[target_name])
        contribution = score / 4

        result["features"].append(
            {
                "feature": f"{target_name}_score",
                "feature_value": round(score, 4),
                "shap_value": round(contribution, 4),
                "impact": "increase" if contribution >= 0 else "decrease",
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

# ============================================
# OVERALL AVERAGE EXPLANATION
# ============================================

def _make_overall_average_shap_dict(
    component_scores: Dict[str, float],
    overall_raw: float,
    overall_rounded: float,
) -> dict:
    """
    Create explanation for overall score.

    Overall is no longer predicted by a Linear Regression model.

    Formula:
        overall = (
            fluency_score
            + lexical_score
            + pronunciation_score
            + grammar_score
        ) / 4

    To keep the old frontend structure, this function returns a SHAP-like dict.
    Each component contributes score / 4 to the final overall score.
    """

    result = {
        "base_value": 0.0,
        "prediction_raw": round(float(overall_raw), 4),
        "prediction": round(float(overall_rounded), 1),
        "features": [],
    }

    for target_name in [
        "fluency",
        "lexical",
        "pronunciation",
        "grammar",
    ]:
        score = float(component_scores[target_name])
        contribution = score / 4

        result["features"].append(
            {
                "feature": f"{target_name}_score",
                "feature_value": round(score, 4),
                "shap_value": round(contribution, 4),
                "impact": "increase" if contribution >= 0 else "decrease",
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
    grammar_data: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Predict 4 component scores and calculate overall score.

    Rules:
    1. Predict fluency, lexical, pronunciation, grammar by 4 separate models.
    2. Overall is NOT predicted by model.
    3. Overall = (fluency + lexical + pronunciation + grammar) / 4.
    4. Overall is rounded to nearest 0.5 band.
    """

    X_all = build_score_features(
        fluency_data=fluency_data,
        lexical_cefr=lexical_cefr,
        lexical_diversity=lexical_diversity,
        pronunciation_data=pronunciation_data,
        grammar_data=grammar_data,
    )

    output = {
        "scores": {},
        "raw_scores": {},
        "shap": {},
    }

    component_scores = {}
    component_raw_scores = {}

    # Chỉ predict 4 model thành phần.
    # Không predict overall model nữa.
    for target_name in [
        "fluency",
        "lexical",
        "pronunciation",
        "grammar",
    ]:
        model = load_score_model(target_name)

        X_target = select_features_for_prediction(
            X_all=X_all,
            target_name=target_name,
        )

        prediction_raw = _predict_raw_score(
            model=model,
            X=X_target,
        )

        prediction_clipped = clip_score(prediction_raw)
        prediction_rounded = round_half(prediction_clipped)

        component_raw_scores[target_name] = prediction_clipped
        component_scores[target_name] = prediction_rounded

        output["scores"][f"{target_name}_score"] = round(
            float(prediction_rounded),
            1,
        )

        output["raw_scores"][f"{target_name}_score"] = round(
            float(prediction_clipped),
            4,
        )

    # ============================================
    # CALCULATE OVERALL SCORE
    # ============================================

    overall_raw = (
        component_scores["fluency"]
        + component_scores["lexical"]
        + component_scores["pronunciation"]
        + component_scores["grammar"]
    ) / 4

    overall_clipped = clip_score(overall_raw)
    overall_rounded = round_half(overall_clipped)

    output["scores"]["overall_score"] = round(
        float(overall_rounded),
        1,
    )

    output["raw_scores"]["overall_score"] = round(
        float(overall_clipped),
        4,
    )

    # ============================================
    # OVERALL EXPLANATION
    # ============================================

    output["shap"]["overall"] = _make_overall_average_shap_dict(
        component_scores=component_scores,
        overall_raw=overall_raw,
        overall_rounded=overall_rounded,
    )

    return output