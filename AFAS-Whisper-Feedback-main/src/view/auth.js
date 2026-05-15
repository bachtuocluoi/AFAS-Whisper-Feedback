const BACKEND_BASE_URL =
  window.APP_CONFIG?.BACKEND_BASE_URL || "http://127.0.0.1:8100";
  
const token = localStorage.getItem("access_token");

function loadUser() {
    if (!token) {
       alert("User not login.");
       window.location.href = "/view/login.html";
       return;
    }
	//if(jwtDecode(token).exp < Date.now() / 1000) {
		//alert("Session expired");
		//localStorage.removeItem("access_token");
		//window.location.href = "/view/login.html";
	//}
	return token;
}

