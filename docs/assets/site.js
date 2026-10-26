/* Theme toggle for the static pages: follows the system until the visitor chooses. */
(function () {
  var key = "amt-theme", root = document.documentElement;
  function read() { try { return localStorage.getItem(key); } catch (e) { return null; } }
  function write(v) { try { localStorage.setItem(key, v); } catch (e) { /* private mode: ignore */ } }
  var saved = read();
  if (saved === "light" || saved === "dark") root.setAttribute("data-theme", saved);
  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.getElementById("theme-toggle");
    if (!btn) return;
    function effective() {
      var t = root.getAttribute("data-theme");
      if (t) return t;
      return window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    function label() { btn.textContent = effective() === "dark" ? "Light mode" : "Dark mode"; }
    btn.addEventListener("click", function () {
      var next = effective() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      write(next);
      label();
    });
    label();
  });
})();
