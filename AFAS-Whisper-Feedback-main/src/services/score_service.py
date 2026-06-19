"""
Score prediction service using 4 Linear Regression PKL models.

Models:
1. fluency_score_model_linear.pkl
2. lexical_score_model_linear.pkl
3. pronunciation_score_model_linear.pkl
4. overall_score_model_linear.pkl

Important rules:
- Fluency, lexical, pronunciation, overall are predicted by 4 separate models.
- Grammar is NOT predicted by a model.
- Grammar is calculated by:

    grammar = overall * 4 - fluency - lexical - pronunciation

- Speech rate is used as WORDS PER MINUTE.
  Do NOT divide speech_rate by 60.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd


# ============================================
# ROUNDING
# ============================================

def round_half(score: float) -> float:
    """
    Round score to nearest 0.5 band.
    """
    score = float(score)
    score = max(0.0, min(9.0, score))

    return math.floor(score * 2 + 0.5 + 1e-12) / 2


def clip_score(score: float) -> float:
    """
    Clip predicted score to 0-9.
    """
    return max(0.0, min(9.0, float(score)))


# ============================================
# PATHS
# ============================================

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = BASE_DIR / "ml_models"

FEATURE_COLUMNS_BY_MODEL_PATH = MODEL_DIR / "feature_columns_by_model.json"
FEATURE_MEDIANS_PATH = MODEL_DIR / "feature_medians.json"

MODEL_PATHS = {
    "overall": MODEL_DIR / "overall_score_model_linear.pkl",
    "fluency": MODEL_DIR / "fluency_score_model_linear.pkl",
    "lexical": MODEL_DIR / "lexical_score_model_linear.pkl",
    "pronunciation": MODEL_DIR / "pronunciation_score_model_linear.pkl",
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


def load_features_by_model() -> Dict[str, List[str]]:
    """
    Load feature_columns_by_model.json.

    Required keys:
    {
        "fluency": [...],
        "lexical": [...],
        "pronunciation": [...],
        "overall": [...]
    }

    Grammar is not required because grammar has no model.
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
        "overall",
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


def load_feature_medians() -> Dict[str, float]:
    """
    Load feature medians generated during training.
    """
    feature_medians = _load_json(FEATURE_MEDIANS_PATH)

    if not isinstance(feature_medians, dict):
        raise TypeError(
            "feature_medians.json must be a dictionary."
        )

    return feature_medians


def _load_model(model_path: Path) -> Any:
    """
    Load pkl model.
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    return joblib.load(model_path)


def load_score_model(target_name: str) -> Any:
    """
    Load and cache model by target name.
    """
    if target_name in _MODEL_CACHE:
        return _MODEL_CACHE[target_name]

    if target_name not in MODEL_PATHS:
        raise ValueError(f"Unknown target name: {target_name}")

    model = _load_model(MODEL_PATHS[target_name])

    _MODEL_CACHE[target_name] = model

    return model


def get_all_feature_columns() -> List[str]:
    """
    Get union of all features used by the 4 models.
    """
    features_by_model = load_features_by_model()

    all_features = []

    for target_name in [
        "fluency",
        "lexical",
        "pronunciation",
        "overall",
    ]:
        for feature in features_by_model[target_name]:
            if feature not in all_features:
                all_features.append(feature)

    return all_features


# ============================================
# VALUE HELPERS
# ============================================

def get_value(
    data: Optional[Dict[str, Any]],
    keys: List[str],
    default: float = 0.0,
) -> float:
    """
    Get value from dict using multiple possible key names.
    """
    if data is None:
        return default

    for key in keys:
        if key in data and data[key] is not None:
            try:
                return float(data[key])
            except Exception:
                return default

    return default


# ============================================
# FEATURE BUILDING
# ============================================

def build_score_features(
    fluency_data: Dict[str, Any],
    lexical_cefr: Dict[str, Any],
    lexical_diversity: Dict[str, Any],
    pronunciation_data: Dict[str, Any],
    grammar_data: Dict[str, Any],
) -> pd.DataFrame:
    """
    Build one-row DataFrame containing all features needed by 4 models.

    grammar_data is kept only for compatibility with old backend calls.
    It is not used because grammar has no model.
    """

    all_feature_columns = get_all_feature_columns()
    feature_medians = load_feature_medians()

    # ============================================
    # FLUENCY
    # IMPORTANT:
    # speech rate is WORDS PER MINUTE.
    # Do NOT divide by 60.
    # ============================================

    raw_speech_rate = get_value(
    fluency_data,
    [
        "speech_rate_wps",
        "flu_speech_rate",
        "speech_rate",
        "speed_rate",
    ],
)

    if raw_speech_rate > 20:
        flu_speech_rate = raw_speech_rate / 60.0
    else:
        flu_speech_rate = raw_speech_rate

    flu_pause_ratio = get_value(
        fluency_data,
        [
            "pause_ratio",
            "flu_pause_ratio",
            "ratio_pauses_to_duration",
        ],
    )
    # ============================================
    # LEXICAL
    # ============================================

    lex_TTR = get_value(
        lexical_diversity,
        [
            "lex_TTR",
            "TTR",
            "ttr",
        ],
    )

    lex_MSTTR = get_value(
        lexical_diversity,
        [
            "lex_MSTTR",
            "MSTTR",
            "msttr",
        ],
    )

    lex_A1 = get_value(
        lexical_cefr,
        [
            "lex_A1",
            "A1",
            "a1",
        ],
    )

    lex_A2 = get_value(
        lexical_cefr,
        [
            "lex_A2",
            "A2",
            "a2",
        ],
    )

    lex_B1 = get_value(
        lexical_cefr,
        [
            "lex_B1",
            "B1",
            "b1",
        ],
    )

    lex_B2 = get_value(
        lexical_cefr,
        [
            "lex_B2",
            "B2",
            "b2",
        ],
    )

    lex_C1 = get_value(
        lexical_cefr,
        [
            "lex_C1",
            "C1",
            "c1",
        ],
    )

    lexical_advanced = (
        lex_B1
        + 2 * lex_B2
        + 3 * lex_C1
    )

    # ============================================
    # PRONUNCIATION
    # ============================================

    pro_0_50 = get_value(
        pronunciation_data,
        [
            "pro_0_50",
            "pro_0%-50%",
            "0-50%",
            "prob_0_50",
            "score_0_50",
            "score_0_50_percent",
        ],
    )

    pro_50_70 = get_value(
        pronunciation_data,
        [
            "pro_50_70",
            "pro_50%-70%",
            "50-70%",
            "prob_50_70",
            "score_50_70",
            "score_50_70_percent",
        ],
    )

    pro_70_85 = get_value(
        pronunciation_data,
        [
            "pro_70_85",
            "pro_70%-85%",
            "70-85%",
            "prob_70_85",
            "score_70_85",
            "score_70_85_percent",
        ],
    )

    pro_85_95 = get_value(
        pronunciation_data,
        [
            "pro_85_95",
            "pro_85%-95%",
            "85-95%",
            "prob_85_95",
            "score_85_95",
            "score_85_95_percent",
        ],
    )

    pro_95_100 = get_value(
        pronunciation_data,
        [
            "pro_95_100",
            "pro_95%-100%",
            "95-100%",
            "prob_95_100",
            "score_95_100",
            "score_95_100_percent",
        ],
    )

    pron_bad = (
        2 * pro_0_50
        + pro_50_70
    )

    pron_good = (
        pro_85_95
        + 2 * pro_95_100
    )

    pron_neutral = pro_70_85

    # ============================================
    # FEATURE DICT
    # Include both new names and old aliases.
    # This prevents errors if JSON still uses old feature names.
    # ============================================

    feature_dict = {
        # Fluency new names
        "flu_speech_rate": flu_speech_rate,
        "flu_pause_ratio": flu_pause_ratio,

        # Lexical new names
        "lex_TTR": lex_TTR,
        "lex_MSTTR": lex_MSTTR,
        "lex_A1": lex_A1,
        "lex_A2": lex_A2,
        "lex_B1": lex_B1,
        "lex_B2": lex_B2,
        "lex_C1": lex_C1,
        "lexical_advanced": lexical_advanced,

        # Lexical aliases
        "TTR": lex_TTR,
        "MSTTR": lex_MSTTR,
        "A1": lex_A1,
        "A2": lex_A2,
        "B1": lex_B1,
        "B2": lex_B2,
        "C1": lex_C1,

        # Pronunciation raw names
        "pro_0_50": pro_0_50,
        "pro_50_70": pro_50_70,
        "pro_70_85": pro_70_85,
        "pro_85_95": pro_85_95,
        "pro_95_100": pro_95_100,

        # Pronunciation aliases with %
        "pro_0%-50%": pro_0_50,
        "pro_50%-70%": pro_50_70,
        "pro_70%-85%": pro_70_85,
        "pro_85%-95%": pro_85_95,
        "pro_95%-100%": pro_95_100,

        # Pronunciation aliases original column names
        "0-50%": pro_0_50,
        "50-70%": pro_50_70,
        "70-85%": pro_70_85,
        "85-95%": pro_85_95,
        "95-100%": pro_95_100,

        # Pronunciation engineered names
        "pron_bad": pron_bad,
        "pron_good": pron_good,
        "pron_neutral": pron_neutral,

        # Pronunciation old engineered aliases
        "bad": pron_bad,
        "good": pron_good,
        "neutral": pron_neutral,
        "neural": pron_neutral,
        "pron_neural": pron_neutral,
    }

    X = pd.DataFrame([feature_dict])

    for col in all_feature_columns:
        if col not in X.columns:
            X[col] = feature_medians.get(col, 0.0)

        X[col] = pd.to_numeric(X[col], errors="coerce")
        X[col] = X[col].fillna(feature_medians.get(col, 0.0))

    X = X[all_feature_columns]

    return X


def select_features_for_prediction(
    X_all: pd.DataFrame,
    target_name: str,
) -> pd.DataFrame:
    """
    Select correct feature columns for one model.
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


# ============================================
# LINEAR MODEL EXPLANATION HELPERS
# ============================================

def _get_regressor_from_model(model: Any) -> Any:
    """
    Get LinearRegression object from Pipeline or direct model.
    """
    if hasattr(model, "named_steps"):
        if "regressor" in model.named_steps:
            return model.named_steps["regressor"]

        if "linear_regression" in model.named_steps:
            return model.named_steps["linear_regression"]

        for _, step in reversed(model.steps):
            if hasattr(step, "coef_") and hasattr(step, "intercept_"):
                return step

    if hasattr(model, "coef_") and hasattr(model, "intercept_"):
        return model

    raise ValueError(
        "Cannot find LinearRegression regressor inside model."
    )


def _transform_X_for_contribution(
    model: Any,
    X: pd.DataFrame,
) -> np.ndarray:
    """
    If model has StandardScaler, use standardized values.
    Otherwise use raw values.
    """
    if hasattr(model, "named_steps") and "scaler" in model.named_steps:
        scaler = model.named_steps["scaler"]
        return scaler.transform(X)

    return X.values.astype(float)


def make_linear_shap_dict(
    target_name: str,
    model: Any,
    X: pd.DataFrame,
    prediction_raw: float,
    prediction_clipped: float,
    prediction_rounded: float,
) -> Dict[str, Any]:
    """
    SHAP-like explanation for Linear Regression.

    For StandardScaler + LinearRegression:
        contribution = coefficient * standardized_feature_value

    base_value = intercept
    prediction_raw ≈ base_value + sum(contributions)
    """
    regressor = _get_regressor_from_model(model)

    X_transformed = _transform_X_for_contribution(
        model=model,
        X=X,
    )

    coefficients = np.asarray(
        regressor.coef_,
        dtype=float,
    ).ravel()

    intercept = float(regressor.intercept_)

    feature_names = list(X.columns)
    feature_values = X.iloc[0].astype(float).values

    contributions = coefficients * X_transformed[0]

    features = []

    for feature_name, feature_value, shap_value in zip(
        feature_names,
        feature_values,
        contributions,
    ):
        shap_value = float(shap_value)

        features.append({
            "feature": feature_name,
            "feature_value": round(float(feature_value), 4),
            "shap_value": round(shap_value, 4),
            "impact": "increase" if shap_value >= 0 else "decrease",
        })

    features = sorted(
        features,
        key=lambda item: abs(item["shap_value"]),
        reverse=True,
    )

    return {
        "target": target_name,
        "base_value": round(intercept, 4),
        "prediction_raw": round(float(prediction_raw), 4),
        "prediction_clipped": round(float(prediction_clipped), 4),
        "prediction": round(float(prediction_rounded), 1),
        "features": features,
    }


# ============================================
# GRAMMAR EXPLANATION HELPERS
# ============================================

def _features_to_contribution_map(
    shap_dict: Dict[str, Any],
    multiplier: float = 1.0,
) -> Dict[str, Dict[str, float]]:
    """
    Convert SHAP-like feature list to dict.
    Used for grammar formula.
    """
    result = {}

    for item in shap_dict["features"]:
        feature_name = item["feature"]

        result[feature_name] = {
            "feature_value": float(item["feature_value"]),
            "shap_value": float(item["shap_value"]) * multiplier,
        }

    return result


def make_formula_grammar_shap_dict(
    shap_by_model: Dict[str, Dict[str, Any]],
    grammar_raw_unclipped: float,
    grammar_clipped: float,
    grammar_rounded: float,
) -> Dict[str, Any]:
    """
    SHAP-like explanation for grammar formula.

    grammar = overall*4 - fluency - lexical - pronunciation
    """
    base_value = (
        shap_by_model["overall"]["base_value"] * 4
        - shap_by_model["fluency"]["base_value"]
        - shap_by_model["lexical"]["base_value"]
        - shap_by_model["pronunciation"]["base_value"]
    )

    contribution_maps = [
        _features_to_contribution_map(
            shap_by_model["overall"],
            multiplier=4.0,
        ),
        _features_to_contribution_map(
            shap_by_model["fluency"],
            multiplier=-1.0,
        ),
        _features_to_contribution_map(
            shap_by_model["lexical"],
            multiplier=-1.0,
        ),
        _features_to_contribution_map(
            shap_by_model["pronunciation"],
            multiplier=-1.0,
        ),
    ]

    combined = {}

    for contribution_map in contribution_maps:
        for feature_name, values in contribution_map.items():
            if feature_name not in combined:
                combined[feature_name] = {
                    "feature_value": values["feature_value"],
                    "shap_value": 0.0,
                }

            combined[feature_name]["shap_value"] += values["shap_value"]

    features = []

    for feature_name, values in combined.items():
        shap_value = float(values["shap_value"])

        features.append({
            "feature": feature_name,
            "feature_value": round(float(values["feature_value"]), 4),
            "shap_value": round(shap_value, 4),
            "impact": "increase" if shap_value >= 0 else "decrease",
        })

    features = sorted(
        features,
        key=lambda item: abs(item["shap_value"]),
        reverse=True,
    )

    return {
        "target": "grammar",
        "base_value": round(float(base_value), 4),
        "prediction_raw": round(float(grammar_raw_unclipped), 4),
        "prediction_clipped": round(float(grammar_clipped), 4),
        "prediction": round(float(grammar_rounded), 1),
        "formula": "overall*4 - fluency - lexical - pronunciation",
        "features": features,
    }


def make_grammar_components_shap_dict(
    clipped_scores: Dict[str, float],
    grammar_raw_unclipped: float,
    grammar_clipped: float,
    grammar_rounded: float,
) -> Dict[str, Any]:
    """
    Simple explanation for grammar by component scores.
    Useful for frontend.
    """
    features = [
        {
            "feature": "overall_score * 4",
            "feature_value": round(float(clipped_scores["overall"]), 4),
            "shap_value": round(float(clipped_scores["overall"] * 4), 4),
            "impact": "increase",
        },
        {
            "feature": "- fluency_score",
            "feature_value": round(float(clipped_scores["fluency"]), 4),
            "shap_value": round(float(-clipped_scores["fluency"]), 4),
            "impact": "decrease",
        },
        {
            "feature": "- lexical_score",
            "feature_value": round(float(clipped_scores["lexical"]), 4),
            "shap_value": round(float(-clipped_scores["lexical"]), 4),
            "impact": "decrease",
        },
        {
            "feature": "- pronunciation_score",
            "feature_value": round(float(clipped_scores["pronunciation"]), 4),
            "shap_value": round(float(-clipped_scores["pronunciation"]), 4),
            "impact": "decrease",
        },
    ]

    features = sorted(
        features,
        key=lambda item: abs(item["shap_value"]),
        reverse=True,
    )

    return {
        "target": "grammar_components",
        "base_value": 0.0,
        "prediction_raw": round(float(grammar_raw_unclipped), 4),
        "prediction_clipped": round(float(grammar_clipped), 4),
        "prediction": round(float(grammar_rounded), 1),
        "formula": "overall*4 - fluency - lexical - pronunciation",
        "features": features,
    }


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
    Predict scores using 4 PKL models.

    Rules:
    1. fluency = fluency model
    2. lexical = lexical model
    3. pronunciation = pronunciation model
    4. overall = overall model
    5. grammar = overall*4 - fluency - lexical - pronunciation
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
        "model_raw_scores": {},
        "shap": {},
        "features": X_all.to_dict(orient="records")[0],
    }

    raw_scores = {}
    clipped_scores = {}
    rounded_scores = {}
    shap_by_model = {}

    # ============================================
    # PREDICT 4 MODELS
    # ============================================

    for target_name in [
        "fluency",
        "lexical",
        "pronunciation",
        "overall",
    ]:
        model = load_score_model(target_name)

        X_target = select_features_for_prediction(
            X_all=X_all,
            target_name=target_name,
        )


        prediction_raw = float(model.predict(X_target)[0])

        prediction_clipped = clip_score(prediction_raw)
        prediction_rounded = round_half(prediction_clipped)

        raw_scores[target_name] = prediction_raw
        clipped_scores[target_name] = prediction_clipped
        rounded_scores[target_name] = prediction_rounded

        output["scores"][f"{target_name}_score"] = round(
            float(prediction_rounded),
            1,
        )

        output["raw_scores"][f"{target_name}_score"] = round(
            float(prediction_clipped),
            4,
        )

        output["model_raw_scores"][f"{target_name}_score"] = round(
            float(prediction_raw),
            4,
        )

        shap_by_model[target_name] = make_linear_shap_dict(
            target_name=target_name,
            model=model,
            X=X_target,
            prediction_raw=prediction_raw,
            prediction_clipped=prediction_clipped,
            prediction_rounded=prediction_rounded,
        )

        output["shap"][target_name] = shap_by_model[target_name]

    # ============================================
    # CALCULATE GRAMMAR BY FORMULA
    # Use clipped model scores to keep score range stable.
    # ============================================

    grammar_raw_unclipped = (
        clipped_scores["overall"] * 4
        - clipped_scores["fluency"]
        - clipped_scores["lexical"]
        - clipped_scores["pronunciation"]
    )

    grammar_clipped = clip_score(grammar_raw_unclipped)
    grammar_rounded = round_half(grammar_clipped)

    output["scores"]["grammar_score"] = round(
        float(grammar_rounded),
        1,
    )

    output["raw_scores"]["grammar_score"] = round(
        float(grammar_clipped),
        4,
    )

    output["model_raw_scores"]["grammar_score"] = round(
        float(grammar_raw_unclipped),
        4,
    )

    # ============================================
    # SHAP-LIKE EXPLANATION FOR GRAMMAR
    # ============================================

    output["shap"]["grammar"] = make_formula_grammar_shap_dict(
        shap_by_model=shap_by_model,
        grammar_raw_unclipped=grammar_raw_unclipped,
        grammar_clipped=grammar_clipped,
        grammar_rounded=grammar_rounded,
    )

    output["shap"]["grammar_components"] = make_grammar_components_shap_dict(
        clipped_scores=clipped_scores,
        grammar_raw_unclipped=grammar_raw_unclipped,
        grammar_clipped=grammar_clipped,
        grammar_rounded=grammar_rounded,
    )

    return output


# ============================================
# ALIAS FOR OLD IMPORTS
# ============================================

def predict_scores_from_features(
    fluency_data: Dict[str, Any],
    lexical_cefr: Dict[str, Any],
    lexical_diversity: Dict[str, Any],
    pronunciation_data: Dict[str, Any],
    grammar_data: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    Alias if other files still import predict_scores_from_features.
    """
    return predict_scores_with_shap_from_features(
        fluency_data=fluency_data,
        lexical_cefr=lexical_cefr,
        lexical_diversity=lexical_diversity,
        pronunciation_data=pronunciation_data,
        grammar_data=grammar_data,
    )