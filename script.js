(function () {
  var dlg = document.getElementById('viewer');
  var img = document.getElementById('viewer-img');
  var title = document.getElementById('viewer-title');
  document.querySelectorAll('[data-full]').forEach(function (b) {
    b.addEventListener('click', function () {
      img.src = b.dataset.full;
      img.alt = b.dataset.title + ' certificate';
      title.textContent = b.dataset.title;
      dlg.showModal();
    });
  });
  dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
})();

(function () {
  var form = document.getElementById('contact-form');
  var status = document.getElementById('form-status');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = form.querySelector('button[type=submit]');
      var data = Object.fromEntries(new FormData(form));
      status.textContent = 'Sending…';
      btn.disabled = true;
      fetch('api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }).then(function (r) { return r.json().then(function (j) { return { r: r, j: j }; }); })
        .then(function (o) {
          if (o.r.ok) { status.textContent = 'Thanks! Your message was sent.'; form.reset(); }
          else status.textContent = o.j.error || Object.values(o.j.errors || {}).join(' ') || 'Something went wrong.';
        })
        .catch(function () { status.textContent = 'Could not reach the server. Please try again later.'; })
        .then(function () { btn.disabled = false; });
    });
  }
  var v = document.getElementById('visits');
  if (v) {
    var first = !sessionStorage.getItem('counted');
    fetch('api/visit' + (first ? '?count=1' : '')).then(function (r) { return r.json(); })
      .then(function (j) { sessionStorage.setItem('counted', '1'); v.textContent = '· ' + j.visits + ' visits'; })
      .catch(function () {});
  }
})();
