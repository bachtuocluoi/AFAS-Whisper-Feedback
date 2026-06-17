let dashboardData = null;

loadUser();

function format2(val) {
    return Number(val || 0).toFixed(2);
}

function formatPercent(val) {
    if (val === null || val === undefined || isNaN(val)) {
        return "-";
    }

    return `${(Number(val) * 100).toFixed(1)}%`;
}

function loadResult() {
    const submit_id = localStorage.getItem("submit_id");

    if (!submit_id) {
        alert("No submit_id");
        window.location.href = "/view/upload.html";
        return;
    }

    fetch(BACKEND_BASE_URL + "/api/v1/result/" + submit_id, {
        method: "GET",
        headers: {
            "Authorization": "Bearer " + token
        }
    })
        .then(res => {
            if (!res.ok) return res.text().then(t => { throw new Error(t); });
            return res.json();
        })
        .then(data => {
            dashboardData = data;

            renderFluency();
            renderLexical();
            renderPronunciation();
            renderGrammar();
        })
        .catch(err => {
            console.error(err);
            alert("Failed to load result: " + err.message);
        });
}

function renderFluency() {
    const d = dashboardData?.fluency;
    const fb = dashboardData?.feedback;

    if (!d) {
        document.getElementById("speechRateValue").innerText = "N/A";
        document.getElementById("pauseRatioValue").innerText = "N/A";
        document.getElementById("fluencyFeedbackText").innerText = "No fluency feedback.";
        document.getElementById("pauseFeedbackText").innerText = "No pause feedback.";
        return;
    }

    document.getElementById("speechRateValue").innerText = format2(d.speed_rate);
    document.getElementById("pauseRatioValue").innerText = format2(d.pause_ratio);

    document.getElementById("fluencyFeedbackText").innerText =
        fb?.fluency || "No fluency feedback.";

    document.getElementById("pauseFeedbackText").innerText =
        fb?.pause || "No pause feedback.";
}

function renderLexical() {
    const d = dashboardData;

    if (!d?.lexical) {
        document.getElementById("A1").innerText = "N/A";
        document.getElementById("A2").innerText = "N/A";
        document.getElementById("B1").innerText = "N/A";
        document.getElementById("B2").innerText = "N/A";
        document.getElementById("C1").innerText = "N/A";
        document.getElementById("lexicalDiversityFeedbackText").innerText =
            "No lexical diversity feedback.";
        document.getElementById("lexicalLevelFeedbackText").innerText =
            "No lexical level feedback.";
        return;
    }

    document.getElementById("A1").innerText = format2(d.lexical.A1);
    document.getElementById("A2").innerText = format2(d.lexical.A2);
    document.getElementById("B1").innerText = format2(d.lexical.B1);
    document.getElementById("B2").innerText = format2(d.lexical.B2);
    document.getElementById("C1").innerText = format2(d.lexical.C1);

    const fig = d.charts?.lexical_bar;

    if (fig) {
        Plotly.newPlot("lexicalMainChart", fig.data, fig.layout);
    }

    if (d.charts?.lexical_diversity_bar) {
        Plotly.newPlot(
            "lexicalDiversityChart",
            d.charts.lexical_diversity_bar.data,
            d.charts.lexical_diversity_bar.layout
        );
    }

    document.getElementById("lexicalDiversityFeedbackText").innerText =
        d.feedback?.lexical_diversity || "No lexical diversity feedback.";

    document.getElementById("lexicalLevelFeedbackText").innerText =
        d.feedback?.lexical_level || "No lexical level feedback.";
}

function renderPronunciation() {
    const d = dashboardData;

    if (!d?.pronunciation) {
        document.getElementById("p0_50").innerText = "N/A";
        document.getElementById("p50_70").innerText = "N/A";
        document.getElementById("p70_85").innerText = "N/A";
        document.getElementById("p85_95").innerText = "N/A";
        document.getElementById("p95_100").innerText = "N/A";
        document.getElementById("pronunciationFeedbackText").innerText =
            "No pronunciation feedback.";
        return;
    }

    document.getElementById("p0_50").innerText = format2(d.pronunciation.score_0_50);
    document.getElementById("p50_70").innerText = format2(d.pronunciation.score_50_70);
    document.getElementById("p70_85").innerText = format2(d.pronunciation.score_70_85);
    document.getElementById("p85_95").innerText = format2(d.pronunciation.score_85_95);
    document.getElementById("p95_100").innerText = format2(d.pronunciation.score_95_100);

    const fig = d.charts?.pronunciation_bar;

    if (fig) {
        Plotly.newPlot("pronChart", fig.data, fig.layout);
    }

    document.getElementById("pronunciationFeedbackText").innerText =
        d.feedback?.pronunciation || "No pronunciation feedback.";
}

function renderGrammar() {
    const grammar = dashboardData?.grammar;
    const fb = dashboardData?.feedback;

    if (!grammar) {
        document.getElementById("grammarErrorSentenceRatio").innerText = "N/A";
        document.getElementById("grammarTotalErrors").innerText = "N/A";
        document.getElementById("grammarErrorRate").innerText = "N/A";

        document.getElementById("grammarFeedbackText").innerText =
            "No grammar feedback.";

        return;
    }

    document.getElementById("grammarErrorSentenceRatio").innerText =
        formatPercent(grammar.ratio_error_sentences);

    document.getElementById("grammarTotalErrors").innerText =
        grammar.total_errors ?? 0;

    document.getElementById("grammarErrorRate").innerText =
        format2(grammar.error_rate);

    document.getElementById("grammarFeedbackText").innerText =
        fb?.grammar || "No grammar feedback.";
}



function goToTranscript() {
    window.location.href = "/view/transcript.html";
}

function goBackUpload() {
    localStorage.removeItem("submit_id");
    window.location.href = "/view/upload.html";
}

function goToHomepage() {
    window.location.href = "/view/homepage.html";
}

function goToScore() {
    const submit_id =
        new URLSearchParams(window.location.search).get("submit_id") ||
        localStorage.getItem("submit_id");

    console.log("GO TO SCORE submit_id =", submit_id);

    if (!submit_id) {
        alert("No submit_id. Please upload audio again.");
        window.location.href = "/view/upload.html";
        return;
    }

    localStorage.setItem("submit_id", submit_id);

    window.location.href = `/view/score.html?submit_id=${submit_id}`;
}

loadResult();