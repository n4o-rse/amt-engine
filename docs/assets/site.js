/* Theme toggle for the static pages: follows the system until the visitor chooses. */
(function () {
  var key = "amt-theme", root = document.documentElement;
  function read() { try { return localStorage.getItem(key); } catch (e) { return null; } }
  function write(v) { try { localStorage.setItem(key, v); } catch (e) { /* private mode: ignore */ } }
  var saved = read();
  if (saved === "light" || saved === "dark") root.setAttribute("data-theme", saved);
  /* language of the start page: English unless the visitor chose German */
  var lkey = "amt-lang";
  function readLang() { try { return localStorage.getItem(lkey); } catch (e) { return null; } }
  function writeLang(v) { try { localStorage.setItem(lkey, v); } catch (e) { /* ignore */ } }
  function applyLang(v) { root.setAttribute("data-lang", v); root.setAttribute("lang", v); }
  applyLang(readLang() === "de" ? "de" : "en");
  document.addEventListener("DOMContentLoaded", function () {
    var lb = document.getElementById("lang-toggle");
    if (lb) {
      var setLabel = function () { lb.textContent = root.getAttribute("data-lang") === "de" ? "English" : "Deutsch"; };
      lb.addEventListener("click", function () {
        var next = root.getAttribute("data-lang") === "de" ? "en" : "de";
        applyLang(next); writeLang(next); setLabel();
      });
      setLabel();
    }
  });
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
