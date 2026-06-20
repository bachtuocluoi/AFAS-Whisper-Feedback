loadUser();

let scoreData = null;
let shapData = null;


function getSubmitId() {
    const params = new URLSearchParams(window.location.search);
    return params.get("submit_id") || localStorage.getItem("submit_id");
}

function format2(val) {
    if (val === null || val === undefined || val === "") {
        return "-";
    }

    const num = Number(val);

    if (Number.isNaN(num)) {
        return "-";
    }

    return num.toFixed(2);
}

function parseShapValues(rawShapValues) {
    if (!rawShapValues) {
        return {};
    }

    if (typeof rawShapValues === "string") {
        try {
            return JSON.parse(rawShapValues);
        } catch (e) {
            console.error("Cannot parse shap_values:", e);
            return {};
        }
    }

    if (typeof rawShapValues === "object") {
        return rawShapValues;
    }

    return {};
}


function loadScorePage() {
    console.log("SCORE JS RUNNING");

    if (!loadUser()) return;

    const submit_id = getSubmitId();

    console.log("submit_id for score:", submit_id);

    if (!submit_id) {
        alert("No submit_id");
        window.location.href = "/view/upload.html";
        return;
    }

    const scoreUrl = BACKEND_BASE_URL + "/api/v1/score/" + submit_id;

    console.log("Calling score API:", scoreUrl);

    fetch(scoreUrl, {
        method: "GET",
        headers: {
            "Authorization": "Bearer " + token
        }
    })

        .then(res => {

            if (res.status === 401) {
                handleUnauthorized();
                return null;
            }

            if (!res.ok) {
                return res.text().then(t => {
                    throw new Error(t || "Failed to load score data");
                });
            }

            return res.json();
        })

        .then(data => {

            if (!data) return;

            console.log("RAW SCORE DATA:", data);

            scoreData = data;
            shapData = parseShapValues(scoreData.shap_values);

            console.log("PARSED SHAP DATA:", shapData);

            renderScores();
            renderShapTable();

        })

        .catch(err => {
            console.error(err);
            alert("Failed to load score: " + err.message);
        });
}


function renderScores() {
    if (!scoreData) return;

    document.getElementById("overallScore").innerText =
        format2(scoreData.overall_score);

    document.getElementById("fluencyScore").innerText =
        format2(scoreData.fluency_score);

    document.getElementById("lexicalScore").innerText =
        format2(scoreData.lexical_score);

    document.getElementById("grammarScore").innerText =
    format2(scoreData.grammar_score);


    document.getElementById("pronunciationScore").innerText =
        format2(scoreData.pronunciation_score);
}


// ============================================
// TÊN HIỂN THỊ CỦA CÁC FEATURE
// ============================================
const FEATURE_LABELS = {
    // Lexical features
    lex_A1: "A1-level vocabulary (%)",
    lex_A2: "A2-level vocabulary (%)",
    lex_B1: "B1-level vocabulary (%)",
    lex_B2: "B2-level vocabulary (%)",
    lex_C1: "C1-level vocabulary (%)",
    lex_TTR: "Lexical diversity (TTR)",
    lex_MSTTR: "Lexical diversity (MSTTR)",

    // Pronunciation features
    "pro_0%-50%": "Pronunciation confidence: 0–50% (%)",
    "pro_50%-70%": "Pronunciation confidence: 50–70% (%)",
    "pro_70%-85%": "Pronunciation confidence: 70–85% (%)",
    "pro_85%-95%": "Pronunciation confidence: 85–95% (%)",
    "pro_95%-100%": "Pronunciation confidence: 95–100% (%)",

    // Grammar features
    gra_ratio_error_sentences: "Grammar error sentence ratio",
    gra_total_errors: "Total grammar errors",
    gra_error_rate: "Grammar error rate",

    grammar_ratio_error_sentences: "Grammar error sentence ratio",
    grammar_total_errors: "Total grammar errors",
    grammar_error_rate: "Grammar error rate",


    // Fluency features
    flu_speech_rate: "Speech rate (words per minute)",
    flu_pause_ratio: "Pause ratio"
};


// ============================================
// LẤY TÊN HIỂN THỊ
// ============================================
function getFeatureLabel(featureName) {
    return FEATURE_LABELS[featureName] || featureName;
}


// ============================================
// RENDER SHAP TABLE
// ============================================
function renderShapTable() {
    const shap = shapData?.overall;

    if (!shap || !Array.isArray(shap.features)) {
        console.warn("No overall SHAP features found.");
        return;
    }

    const tbody = document.getElementById("shapTableBody");

    tbody.innerHTML = "";

    shap.features.forEach(item => {
        const color =
            item.impact === "increase"
                ? "#16a34a"
                : "#dc2626";

        const featureLabel = getFeatureLabel(item.feature);

        tbody.innerHTML += `
            <tr>
                <td title="${item.feature}">
                    ${featureLabel}
                </td>

                <td>
                    ${format2(item.feature_value)}
                </td>

                <td style="color: ${color}; font-weight: bold;">
                    ${format2(item.shap_value)}
                </td>

                <td style="color: ${color}; font-weight: bold;">
                    ${item.impact}
                </td>
            </tr>
        `;
    });
}



function goBackUpload() {
    localStorage.removeItem("submit_id");
    localStorage.removeItem("ques_id");
    window.location.href = "/view/upload.html";
}



function goBackResult() {
    window.location.href = "/view/result.html";
}

function goToHomepage() {
    localStorage.removeItem("ques_id");
    window.location.href = "/view/homepage.html";
}


window.addEventListener("DOMContentLoaded", loadScorePage);