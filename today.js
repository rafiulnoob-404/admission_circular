/* Today is not the same thing as a data update timestamp. */
(function () {
  'use strict';
  function renderToday() {
    var text = new Intl.DateTimeFormat('bn-BD', {
      timeZone: 'Asia/Dhaka', day: 'numeric', month: 'long', year: 'numeric'
    }).format(new Date());
    document.querySelectorAll('[data-bd-today]').forEach(function (node) { node.textContent = text; });
  }
  renderToday();
  setInterval(renderToday, 60000);
})();
