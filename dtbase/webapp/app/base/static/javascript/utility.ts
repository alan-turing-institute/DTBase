// Zip to arrays [x0, x1, x2, ...] and [y0, y1, y2, ...] into
// [{x: x0, y: 01}, {x: x1, y: y1}, {x: x2, y: y2}, ...]
// Used to gather data for plots into a format preferred by Chart.js
export function dictionary_scatter(x, y) {
  const value_array = [];
  for (let j = 0; j < y.length; j++) {
    const mydict = { x: x[j], y: y[j] };
    value_array.push(mydict);
  }
  return value_array;
}

// function used to toggle the visibility of the password field
export function passwordToggle() {
  const passwordField = document.getElementById("pwd_login");
  const passwordFieldType = passwordField.getAttribute("type");
  if (passwordFieldType === "password") {
    passwordField.setAttribute("type", "text");
  } else {
    passwordField.setAttribute("type", "password");
  }
}

window.passwordToggle = passwordToggle;
