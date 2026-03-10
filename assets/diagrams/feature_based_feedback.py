def f_fluency(speed_rate):
    if speed_rate < 90:
        return "Improve speech fluency"
    else:
        return "Fluency level acceptable"


def f_pause(pause_ratio):
    if pause_ratio > 0.20:
        return "Reduce excessive pauses"
    elif 0.15 <= pause_ratio <= 0.20:
        return "Pause usage acceptable"
    else:  # pause_ratio < 0.15
        return "Consider adding natural pauses"


def f_lexical_diversity(msttr):
    if msttr < 0.70:
        return "Increase lexical diversity"
    else:
        return "Lexical diversity acceptable"


def f_lexical_level(b2, c1):
    if (b2 + c1) < 0.10:
        return "Use more advanced vocabulary"
    else:
        return "Advanced vocabulary usage acceptable"


def f_pronunciation(score):
    if score < 0.70:
        return "Improve pronunciation clarity"
    else:
        return "Pronunciation quality acceptable"



def generate_feedback(features):
    """
    Generate full feedback profile for a student
    
    features = {
        "speech_rate": float,
        "pause_ratio": float,
        "msttr": float,
        "b2": float,
        "c1": float,
        "pronunciation": float
    }
    """

    fluency_feedback = f_fluency(features["speech_rate"])
    pause_feedback = f_pause(features["pause_ratio"])
    lexical_div_feedback = f_lexical_diversity(features["msttr"])
    lexical_level_feedback = f_lexical_level(features["b2"], features["c1"])
    pronunciation_feedback = f_pronunciation(features["pronunciation"])

    return {
        "fluency": fluency_feedback,
        "pause": pause_feedback,
        "lexical_diversity": lexical_div_feedback,
        "lexical_level": lexical_level_feedback,
        "pronunciation": pronunciation_feedback
    }

