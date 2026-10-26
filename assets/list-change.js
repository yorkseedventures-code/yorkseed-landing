/* The Yorkseed List: "Change or remove this event" request form.
   Any element with [data-ys-change] opens it. Optional attributes: data-title, data-date, data-link, data-url.
   window.YSChange({title,date,link,url}) opens it from code. Requests are emailed to info@yorkseed.co. */
(function () {
  var KEY = "5c1c96c6-7a4f-4cc7-85d3-4dd79f67e20a";
  var css = ".ysc-bg{position:fixed;inset:0;background:rgba(10,10,10,.55);z-index:99999;display:flex;align-items:center;justify-content:center;padding:16px}" +
    ".ysc{background:#faf7f1;color:#111;max-width:480px;width:100%;max-height:92vh;overflow:auto;padding:26px 24px 22px;font:400 15px/1.5 'DM Sans',system-ui,sans-serif;position:relative;box-shadow:0 20px 60px rgba(0,0,0,.35)}" +
    ".ysc h2{font:400 26px/1.1 'Playfair Display',Georgia,serif;margin:0 0 6px}.ysc p{margin:0 0 14px;color:#555;font-size:14px}.ysc .x{position:absolute;top:8px;right:12px;background:none;border:0;font-size:26px;cursor:pointer;color:#555}" +
    ".ysc label{display:block;font:500 11px 'DM Mono',ui-monospace,monospace;letter-spacing:.1em;text-transform:uppercase;color:#555;margin:12px 0 5px}" +
    ".ysc input,.ysc select,.ysc textarea{width:100%;font:inherit;font-size:16px;padding:11px 12px;border:1px solid rgba(0,0,0,.18);background:#fff;color:#111;border-radius:0}" +
    ".ysc textarea{min-height:110px;resize:vertical}.ysc .go{margin-top:16px;width:100%;padding:13px;background:#c8102e;color:#fff;border:0;font:500 12px 'DM Mono',ui-monospace,monospace;letter-spacing:.1em;text-transform:uppercase;cursor:pointer}" +
    ".ysc .go[disabled]{opacity:.6;cursor:default}.ysc .err{color:#b42318;font-size:13px;margin-top:8px}.ysc .ysc-ev{background:#fff;border:1px solid rgba(0,0,0,.1);padding:9px 12px;font-size:14px;margin:0 0 4px}" +
    ".ysc .hp{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}";
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function open(info) {
    info = info || {};
    if (!document.getElementById("ysc-css")) { var st = document.createElement("style"); st.id = "ysc-css"; st.textContent = css; document.head.appendChild(st); }
    var bg = document.createElement("div"); bg.className = "ysc-bg"; bg.setAttribute("role", "dialog"); bg.setAttribute("aria-modal", "true");
    var prev = document.activeElement;
    bg.innerHTML = '<form class="ysc" novalidate><button type="button" class="x" aria-label="Close">×</button>' +
      '<h2>Change or remove your event</h2><p>Tell us what to fix and we will update the List within a day. Only the host or organizer should send this.</p>' +
      '<div class="ysc-ev"><b>' + esc(info.title || "Your event") + '</b>' + (info.date ? ' · ' + esc(info.date) : '') + '</div>' +
      '<label for="ysc-t">What do you need?</label><select id="ysc-t"><option>Fix details (title, description, venue, link)</option><option>Change the date or time</option><option>Event is cancelled or removed</option><option>Something else</option></select>' +
      '<label for="ysc-d">What should it say? *</label><textarea id="ysc-d" placeholder="e.g. New start time is 7pm. Venue is now ..."></textarea>' +
      '<label for="ysc-e">Your email *</label><input id="ysc-e" type="email" autocomplete="email" placeholder="So we can confirm the change">' +
      '<label for="ysc-n">Your name</label><input id="ysc-n" autocomplete="name">' +
      '<input class="hp" tabindex="-1" autocomplete="off" aria-hidden="true" id="ysc-h">' +
      '<div class="err" id="ysc-err" hidden></div><button class="go" type="submit">Send request</button></form>';
    document.body.appendChild(bg);
    var f = bg.firstChild, err = f.querySelector("#ysc-err"), btn = f.querySelector(".go");
    function close() { bg.remove(); document.removeEventListener("keydown", onKey); if (prev && prev.focus) prev.focus(); }
    function onKey(e) { if (e.key === "Escape") close(); }
    document.addEventListener("keydown", onKey);
    f.querySelector(".x").onclick = close; bg.addEventListener("click", function (e) { if (e.target === bg) close(); });
    f.querySelector("#ysc-d").focus();
    f.onsubmit = function (ev) {
      ev.preventDefault();
      var d = f.querySelector("#ysc-d").value.trim(), em = f.querySelector("#ysc-e").value.trim();
      if (d.length < 5) { err.textContent = "Please tell us what to change."; err.hidden = false; return; }
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(em)) { err.textContent = "Please enter a valid email so we can confirm."; err.hidden = false; return; }
      if (f.querySelector("#ysc-h").value) { close(); return; }
      err.hidden = true; btn.disabled = true; btn.textContent = "Sending…";
      var type = f.querySelector("#ysc-t").value, name = f.querySelector("#ysc-n").value.trim();
      var data = {
        access_key: KEY, subject: "List change request: " + (info.title || "event") + " (" + type + ")", from_name: "The Yorkseed List", replyto: em,
        "Request": type, "Event": info.title || "", "Date": info.date || "", "Event link": info.link || "", "List page": info.url || location.href,
        "What to change": d, "Requester email": em, "Requester name": name, botcheck: ""
      };
      fetch("https://api.web3forms.com/submit", { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify(data) })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (!j || !j.success) throw 0;
          f.innerHTML = '<button type="button" class="x" aria-label="Close">×</button><h2>Request sent</h2><p>Thanks. We will update the List and email you at ' + esc(em) + ' once it is done.</p><button type="button" class="go" id="ysc-ok">Close</button>';
          f.querySelector(".x").onclick = close; f.querySelector("#ysc-ok").onclick = close;
        })
        .catch(function () { btn.disabled = false; btn.textContent = "Send request"; err.textContent = "That did not send. Please try again, or email info@yorkseed.co."; err.hidden = false; });
    };
  }
  window.YSChange = open;
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("[data-ys-change]");
    if (!a) return; e.preventDefault();
    open({ title: a.getAttribute("data-title"), date: a.getAttribute("data-date"), link: a.getAttribute("data-link"), url: a.getAttribute("data-url") || location.href });
  });
})();
