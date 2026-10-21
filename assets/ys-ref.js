/* Yorkseed referral: every outbound link from a Yorkseed page carries utm_source=yorkseed
   (and ref=yorkseed on Luma), so partners can see the traffic Yorkseed sends them.
   Own properties, mailto/tel and links that already carry a utm_source are left alone. */
(function(){
  var OWN=/(^|\.)(yorkseed\.co|yorkseedhouse\.com|yorkseedsummit\.com|yorkseedventures\.com|thevalois\.com)$/i;
  var SKIP=/(^|\.)(stripe\.com|google\.com|googleapis\.com|gstatic\.com|apple\.com|wa\.me|whatsapp\.com)$/i;
  var LUMA=/(^|\.)(lu\.ma|luma\.com)$/i;
  var page=(location.pathname.replace(/^\/|\.html$|\/$/g,'').replace(/[^a-z0-9]+/gi,'_')||'home').slice(0,60);
  function tag(a){
    try{
      if(!a.href||a.dataset.ysRef)return;
      var u=new URL(a.href,location.href);
      if(!/^https?:$/.test(u.protocol)||u.hostname===location.hostname||OWN.test(u.hostname)||SKIP.test(u.hostname))return;
      if(!u.searchParams.has('utm_source')){
        u.searchParams.set('utm_source','yorkseed');
        u.searchParams.set('utm_medium','referral');
        u.searchParams.set('utm_campaign',page);
      }
      if(LUMA.test(u.hostname)&&!u.searchParams.has('ref'))u.searchParams.set('ref','yorkseed');
      a.href=u.toString();a.dataset.ysRef='1';
    }catch(e){}
  }
  function all(root){var l=(root||document).querySelectorAll('a[href]');for(var i=0;i<l.length;i++)tag(l[i]);}
  // tag on load, on anything added later, and at the moment of click as a final catch
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){all();});else all();
  document.addEventListener('click',function(e){var a=e.target&&e.target.closest&&e.target.closest('a[href]');if(a)tag(a);},true);
  document.addEventListener('auxclick',function(e){var a=e.target&&e.target.closest&&e.target.closest('a[href]');if(a)tag(a);},true);
  try{new MutationObserver(function(m){for(var i=0;i<m.length;i++)for(var j=0;j<m[i].addedNodes.length;j++){var n=m[i].addedNodes[j];if(n.nodeType===1){if(n.matches&&n.matches('a[href]'))tag(n);all(n);}}}).observe(document.documentElement,{childList:true,subtree:true});}catch(e){}
})();
