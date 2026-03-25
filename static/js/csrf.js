// Helper utilities for CSRF token handling in browser requests.
// Django sets a cookie named "csrftoken" by default.

function getCookie(name) {
  const cookies = document.cookie ? document.cookie.split(';') : [];
  for (let i = 0; i < cookies.length; i += 1) {
    const cookie = cookies[i].trim();
    if (cookie.startsWith(`${name}=`)) {
      return decodeURIComponent(cookie.substring(name.length + 1));
    }
  }
  return null;
}

function getCsrfToken() {
  // Prefer cookie value if available. Fall back to token embedded in the page.
  const cookieToken = getCookie('csrftoken');
  if (cookieToken) return cookieToken;
  return typeof window !== 'undefined' ? window.CSRF_TOKEN : null;
}

function addCsrfHeader(headers = {}) {
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    return { ...headers, 'X-CSRFToken': csrfToken };
  }
  return headers;
}

window.getCsrfToken = getCsrfToken;
window.addCsrfHeader = addCsrfHeader;
