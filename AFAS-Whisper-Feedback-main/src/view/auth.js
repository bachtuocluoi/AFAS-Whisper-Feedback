const BACKEND_BASE_URL =
    window.APP_CONFIG?.BACKEND_BASE_URL || "http://127.0.0.1:8100";

const token = localStorage.getItem("access_token");

function parseJwt(token) {
    var base64Url = token.split('.')[1];
    var base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    var jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function (c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));

    return JSON.parse(jsonPayload);
}

function loadUser() {
    if (!token) {
        alert("User not login. Please login first");
        window.location.href = "/view/login.html";
        return;
    }
    if (parseJwt(token).exp < Date.now() / 1000) {
        handleUnauthorized();
    }
    return token;
}

function handleUnauthorized() {
    alert("Session expired. Please log in again");

    localStorage.removeItem("access_token");
    localStorage.removeItem("token");
    localStorage.removeItem("submit_id");

    window.location.href = "/view/login.html";
}

