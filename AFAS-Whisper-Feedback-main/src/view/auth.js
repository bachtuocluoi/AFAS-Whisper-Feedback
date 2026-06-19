const BACKEND_BASE_URL =
    window.APP_CONFIG?.BACKEND_BASE_URL || "http://127.0.0.1:8100";

const token = localStorage.getItem("access_token");
const refresh_token = localStorage.getItem("refresh_token");

function parseJwt(token) {
    var base64Url = token.split('.')[1];
    var base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    var jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function (c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));

    return JSON.parse(jsonPayload);
}

async function loadUser() {
    let token = localStorage.getItem("access_token");

    if (!token) {
        alert("User not login. Please login first");
        window.location.href = "/view/login.html";
        return;
    }

    const payload = parseJwt(token);

    if (!payload || !payload.exp) {
        handleUnauthorized();
        return null;
    }

    // Access token hết hạn thì refresh, không logout ngay
    if (payload.exp < Date.now() / 1000) {
        token = await getRefreshToken();

        if (!token) {
            return null;
        }
    }

    return token;
}

function handleUnauthorized() {
    alert("Session expired. Please log in again");

    localStorage.removeItem("access_token");
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("submit_id");

    window.location.href = "/view/login.html";
}

async function getRefreshToken() {
    const refreshToken = localStorage.getItem("refresh_token");

    if (!refreshToken) {
        handleUnauthorized();
        return null;
    }

    try {
        const response = await fetch(BACKEND_BASE_URL + "/api/v1/auth/refresh", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                refresh_token: refreshToken
            })
        });

        const data = await response.json();

        if (!response.ok) {
            console.error("Refresh token failed:", data);
            handleUnauthorized();
            return null;
        }

        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);

        return data.access_token;

    } catch (error) {
        console.error("Refresh token error:", error);
        handleUnauthorized();
        return null;
    }
}

