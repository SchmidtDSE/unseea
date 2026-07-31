// Persisted light/dark toggle. Falls back to the OS preference when unset.
(function () {
  var KEY = "unseea-theme";
  var root = document.documentElement;
  var stored = null;
  try { stored = localStorage.getItem(KEY); } catch (e) { /* private mode */ }
  if (stored === "light" || stored === "dark") root.setAttribute("data-theme", stored);

  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.getElementById("theme");
    if (!btn) return;
    function label() {
      var explicit = root.getAttribute("data-theme");
      var dark = explicit
        ? explicit === "dark"
        : window.matchMedia("(prefers-color-scheme: dark)").matches;
      btn.textContent = dark ? "Light" : "Dark";
      btn.setAttribute("aria-label", "Switch to " + (dark ? "light" : "dark") + " theme");
    }
    label();
    btn.addEventListener("click", function () {
      var explicit = root.getAttribute("data-theme");
      var dark = explicit
        ? explicit === "dark"
        : window.matchMedia("(prefers-color-scheme: dark)").matches;
      var next = dark ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem(KEY, next); } catch (e) { /* ignore */ }
      label();
    });
  });
})();
