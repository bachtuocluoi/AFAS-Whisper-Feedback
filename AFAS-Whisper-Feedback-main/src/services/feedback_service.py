

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
    Generate full feedback profile for a student.

    features = {
        "speech_rate": float,
        "pause_ratio": float,
        "msttr": float,
        "b2": float,
        "c1": float,
        "pronunciation": float
    }
    """


    speech_rate = features.get("speech_rate", 0.0)
    pause_ratio = features.get("pause_ratio", 0.0)
    msttr = features.get("msttr", 0.0)
    b2 = features.get("b2", 0.0)
    c1 = features.get("c1", 0.0)
    pronunciation = features.get("pronunciation", 0.0)

    return {
        "fluency": f_fluency(speech_rate),
        "pause": f_pause(pause_ratio),
        "lexical_diversity": f_lexical_diversity(msttr),
        "lexical_level": f_lexical_level(b2, c1),
        "pronunciation": f_pronunciation(pronunciation)
    }