import plotly.graph_objects as go


def fmt2(value):
    try:
        return f"{float(value):.2f}"
    except Exception:
        return "0.00"



def build_lexical_bar_chart(lexical):
    labels = ["A1", "A2", "B1", "B2", "C1"]
    values = [lexical["A1"], lexical["A2"], lexical["B1"], lexical["B2"], lexical["C1"]]

    fig = go.Figure()
    fig.add_bar(
        x=labels,
        y=values,
        text=[fmt2(v) for v in values],
        textposition="auto"
    )
    fig.update_layout(
        title="Lexical CEFR Distribution",
        template="plotly_white",
        margin=dict(l=40, r=20, t=50, b=40)
    )
    return fig


def build_lexical_diversity_chart(lexical):
    labels = ["TTR", "MTTR"]
    values = [lexical["ttr"], lexical["mttr"]]

    fig = go.Figure()
    fig.add_bar(
        x=labels,
        y=values,
        text=[fmt2(v) for v in values],
        textposition="auto"
    )
    fig.update_layout(
        title="Lexical Diversity",
        template="plotly_white",
        margin=dict(l=40, r=20, t=50, b=40)
    )
    return fig




def build_pronunciation_bar_chart(pron):
    labels = ["0-50%", "50-70%", "70-85%", "85-95%", "95-100%"]
    values = [
        pron["score_0_50"],
        pron["score_50_70"],
        pron["score_70_85"],
        pron["score_85_95"],
        pron["score_95_100"],
    ]

    fig = go.Figure()
    fig.add_bar(
        x=labels,
        y=values,
        text=[fmt2(v) for v in values],
        textposition="auto"
    )
    fig.update_layout(
        title="Pronunciation Distribution",
        template="plotly_white",
        margin=dict(l=40, r=20, t=50, b=40)
    )
    return fig