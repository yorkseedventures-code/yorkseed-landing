/* Yorkseed: link fields fill in https:// for the visitor.
   Works on every <input type="url">, including rows added later (event delegation).
   - Focus an empty field: "https://" is filled in, cursor at the end.
   - Paste a full link: a doubled "https://https://" is collapsed.
   - Leave the field: "acme.com" becomes "https://acme.com"; a bare "https://" is cleared,
     so optional fields stay empty and required fields still count as missing. */
(function () {
  var PREFIX = 'https://';
  function isUrlInput(el) {
    return el && el.tagName === 'INPUT' && (el.type === 'url' || el.hasAttribute('data-url')) && !el.readOnly && !el.disabled;
  }
  function fire(el) {
    try { el.dispatchEvent(new Event('input', { bubbles: true })); } catch (e) {}
  }
  function tidy(v) {
    v = v.replace(/^\s+|\s+$/g, '');
    // "https://https://x", "https://http://x", "https://www.https://x" -> keep the pasted scheme
    var m = v.match(/^https?:\/\/(https?:\/\/.*)$/i);
    if (m) v = m[1];
    return v;
  }
  document.addEventListener('focusin', function (e) {
    var el = e.target;
    if (!isUrlInput(el) || el.value) return;
    el.value = PREFIX;
    try { el.setSelectionRange(PREFIX.length, PREFIX.length); } catch (err) {}
  });
  document.addEventListener('input', function (e) {
    var el = e.target;
    if (!isUrlInput(el)) return;
    var t = tidy(el.value);
    if (t !== el.value.replace(/^\s+|\s+$/g, '')) {
      el.value = t;
      try { el.setSelectionRange(t.length, t.length); } catch (err) {}
    }
  });
  document.addEventListener('focusout', function (e) {
    var el = e.target;
    if (!isUrlInput(el)) return;
    var v = tidy(el.value);
    if (/^https?:\/\/?$/i.test(v)) v = '';
    else if (v && !/^[a-z][a-z0-9+.-]*:\/\//i.test(v)) v = PREFIX + v.replace(/^\/+/, '');
    if (v !== el.value) { el.value = v; fire(el); }
  });
  // Safety net: tidy every link field right before any form submits
  document.addEventListener('submit', function (e) {
    var f = e.target;
    if (!f || !f.querySelectorAll) return;
    [].forEach.call(f.querySelectorAll('input[type="url"],input[data-url]'), function (el) {
      var v = tidy(el.value);
      if (/^https?:\/\/?$/i.test(v)) v = '';
      else if (v && !/^[a-z][a-z0-9+.-]*:\/\//i.test(v)) v = PREFIX + v.replace(/^\/+/, '');
      el.value = v;
    });
  }, true);
})();
