document.addEventListener('change', function (event) {
  var select = event.target.closest('[data-mp-settings-nav]');
  if (select && select.value) {
    window.location.assign(select.value);
  }
});
