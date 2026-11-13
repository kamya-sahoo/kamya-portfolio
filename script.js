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
