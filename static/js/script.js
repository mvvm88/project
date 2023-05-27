$(function() {
    if (window.history && window.history.pushState) {
    $(window).on('popstate', function () {
    window.history.pushState('forward', null, '#');
    window.history.forward(1);
    });
}
window.history.pushState ('forward', null, '#'); // В IE должны быть эти две строки
window.history.forward(1);
})
          if (window.history && window.history.pushState) {
            $(window).on('popstate', function () {
              var block1 = $('#pop').css('display');
              if (block1 == 'block') {
                window.location.href = attrHref;
              }
              var hashLocation = location.hash;
              var hashSplit = hashLocation.split("#!/");
              var hashName = hashSplit[1];
              if (hashName !== '') {
                var hash = window.location.hash;
                if (hash === '') {
                  popBox.style.display = 'none'
                  popSub.style.display = 'block'
                }
              }
            });
            history.pushState(null, null, location.href);
            window.addEventListener('popstate', function (event) {
              history.pushState(null, null, location.href);
            });
          }