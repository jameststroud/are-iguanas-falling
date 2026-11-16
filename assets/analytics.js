/* Visit counting with GoatCounter (no cookies, no personal data).

   SETUP: paste your GoatCounter code below. If your dashboard is at
   https://iguanas.goatcounter.com, the code is "iguanas".
   Until then nothing is loaded and nothing is counted.

   Embed snippet this mirrors (from https://www.goatcounter.com/help/start, Nov 2026):
   <script data-goatcounter="https://MYCODE.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
   Events use window.goatcounter.count({path, title, event: true})
   (https://www.goatcounter.com/help/events). */
var GOATCOUNTER_CODE = "GOATCOUNTER_CODE"; // TODO(James): replace with your GoatCounter code

(function () {
  var queue = [];
  var ready = function () { return window.goatcounter && typeof window.goatcounter.count === "function"; };

  /* window.track("name") records an event. Safe to call any time: if GoatCounter
     is blocked, slow or not set up, the event is dropped and nothing breaks. */
  window.track = function (name) {
    try {
      if (ready()) window.goatcounter.count({ path: name, title: name, event: true });
      else if (queue.length < 20) queue.push(name);
    } catch (e) {}
  };

  /* Events counted on every page */
  document.addEventListener("click", function (e) {
    try {
      var el = e.target.closest && e.target.closest("a,button");
      if (!el) return;
      if (el.hasAttribute("data-lang-toggle")) {
        // i18n.js switches the language in its own click handler; read the result after it
        setTimeout(function () { window.track("lang-switch-to-" + (window.getLang ? window.getLang() : "")); }, 0);
      } else if (el.hasAttribute("data-track")) {
        window.track(el.getAttribute("data-track"));
      } else if (el.href && el.href.indexOf("inaturalist.org") !== -1) {
        window.track("inaturalist-click");
      }
    } catch (err) {}
  });

  if (!GOATCOUNTER_CODE || GOATCOUNTER_CODE === "GOATCOUNTER_CODE") return; // not set up yet
  try {
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://gc.zgo.at/count.js";
    s.setAttribute("data-goatcounter", "https://" + GOATCOUNTER_CODE + ".goatcounter.com/count");
    s.onload = function () {
      var q = queue; queue = [];
      // count.js sets itself up on load; give it a moment, then send anything queued
      setTimeout(function () { q.forEach(window.track); }, 200);
    };
    s.onerror = function () { queue = []; };
    document.head.appendChild(s);
  } catch (e) {}
})();
