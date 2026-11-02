/* The Yorkseed List: "Change or remove this event" request form.
   Any element with [data-ys-change] opens it. Optional attributes: data-title, data-date, data-link, data-url.
   window.YSChange({title,date,link,url}) opens it from code. Requests go to the Event Manager for approval. */
(function () {
  var API = "https://yorkseed-backend-production.up.railway.app/api/list-submissions/change";
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
    bg.innerHTML = '<form class="ysc" novalidate><button type="button" class="x" aria-label="Close">\u00d7</button>' +
      '<h2>Change or remove your event</h2><p>Fill in only what should change. We review every request, then update the List and email you. Only the host or organizer should send this.</p>' +
      '<div class="ysc-ev"><b>' + esc(info.title || "Your event") + '</b>' + (info.date ? ' \u00b7 ' + esc(info.date) : '') + '</div>' +
      '<label for="ysc-t">What do you need?</label><select id="ysc-t"><option value="edit">Change details</option><option value="remove">Remove it (cancelled or duplicate)</option></select>' +
      '<div id="ysc-f"><label for="ysc-ti">New title</label><input id="ysc-ti">' +
      '<label for="ysc-da">New date</label><input id="ysc-da" type="date">' +
      '<label for="ysc-st">New start time</label><input id="ysc-st" type="time"><label for="ysc-en">New end time</label><input id="ysc-en" type="time">' +
      '<label for="ysc-ve">New venue</label><input id="ysc-ve">' +
      '<label for="ysc-li">New link</label><input id="ysc-li" type="url" placeholder="https://">' +
      '<label for="ysc-de">New description</label><textarea id="ysc-de" style="min-height:80px"></textarea></div>' +
      '<label for="ysc-d">Anything else we should know?</label><textarea id="ysc-d" style="min-height:70px" placeholder="Optional"></textarea>' +
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
    var typ = f.querySelector("#ysc-t");
    typ.onchange = function () { f.querySelector("#ysc-f").hidden = typ.value === "remove"; };
    function v(id) { return f.querySelector(id).value.trim(); }
    f.onsubmit = function (ev) {
      ev.preventDefault();
      var em = v("#ysc-e"), kind = typ.value, note = v("#ysc-d");
      var fields = { title: v("#ysc-ti"), date: v("#ysc-da"), start: v("#ysc-st"), end: v("#ysc-en"), venue: v("#ysc-ve"), link: v("#ysc-li"), desc: v("#ysc-de") };
      var any = Object.keys(fields).some(function (k) { return fields[k]; });
      if (kind === "edit" && !any && note.length < 5) { err.textContent = "Please fill in what should change."; err.hidden = false; return; }
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(em)) { err.textContent = "Please enter a valid email so we can confirm."; err.hidden = false; return; }
      if (f.querySelector("#ysc-h").value) { close(); return; }
      err.hidden = true; btn.disabled = true; btn.textContent = "Sending\u2026";
      var body = { kind: kind, title: info.title || "", date: info.date || "", link: info.link || "", fields: fields, note: note, email: em, name: v("#ysc-n"), website: "" };
      fetch(API, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
        .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok) throw new Error(j.message || ""); }); })
        .then(function () {
          f.innerHTML = '<button type="button" class="x" aria-label="Close">\u00d7</button><h2>Request sent</h2><p>Thanks. We will review it, update the List and email you at ' + esc(em) + ' once it is done.</p><button type="button" class="go" id="ysc-ok">Close</button>';
          f.querySelector(".x").onclick = close; f.querySelector("#ysc-ok").onclick = close;
        })
        .catch(function (e) { btn.disabled = false; btn.textContent = "Send request"; err.textContent = (e && e.message) || "That did not send. Please try again, or email info@yorkseed.co."; err.hidden = false; });
    };
  }
  window.YSChange = open;
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("[data-ys-change]");
    if (!a) return; e.preventDefault();
    open({ title: a.getAttribute("data-title"), date: a.getAttribute("data-date"), link: a.getAttribute("data-link"), url: a.getAttribute("data-url") || location.href });
  });
})();
