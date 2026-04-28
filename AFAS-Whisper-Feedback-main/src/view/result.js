const BACKEND_BASE_URL =
  window.APP_CONFIG?.BACKEND_BASE_URL || "http://127.0.0.1:8100";

let dashboardData = null;

const token = localStorage.getItem("access_token");
	  
async function loadUser() {
    if (!token) {
       alert("User not login.");
       window.location.href = "/view/login.html";
       return;
    }
}

loadUser();

function format2(val) {
  return Number(val || 0).toFixed(2);
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

  const fig  = d.charts.lexical_bar;

  Plotly.newPlot("lexicalMainChart", fig.data, fig.layout);
  Plotly.newPlot("lexicalDiversityChart", d.charts.lexical_diversity_bar.data);

  document.getElementById("lexicalDiversityFeedbackText").innerText =
    d.feedback.lexical_diversity;

  document.getElementById("lexicalLevelFeedbackText").innerText =
    d.feedback.lexical_level;
}

function renderPronunciation() {
  const d = dashboardData;

  document.getElementById("p0_50").innerText = format2(d.pronunciation.score_0_50);
  document.getElementById("p50_70").innerText = format2(d.pronunciation.score_50_70);
  document.getElementById("p70_85").innerText = format2(d.pronunciation.score_70_85);
  document.getElementById("p85_95").innerText = format2(d.pronunciation.score_85_95);
  document.getElementById("p95_100").innerText = format2(d.pronunciation.score_95_100);
  document.getElementById("pronunciationScoreValue").innerText =
  format2(d.pronunciation.pronunciation_score ?? 0);

  const fig = d.charts.pronunciation_bar;

  Plotly.newPlot("pronChart", fig.data, fig.layout);

  document.getElementById("pronunciationFeedbackText").innerText =
    d.feedback.pronunciation;
}

function goToTranscript() {
  window.location.href = "/view/transcript.html";
}

function goBackUpload() {
  localStorage.removeItem("submit_id");
  window.location.href = "/view/upload.html";
}


loadResult();