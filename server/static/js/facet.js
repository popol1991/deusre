function update_date() {
    var from = $('#datefrom').val();
    if (from.length == 0) from = '0000-00-00';
    var to = $('#dateto').val();
    if (to.length == 0) to = '3000-00-00';

    var facets = eval($('.data-placeholder').html());
    for (var i = 0; i < facets.length; i++) {
        var date = facets[i]['date'];
        var id = "#" + i + "-date";
        if (date > from && date < to) {
            $(id).addClass('highlight');
        } else {
            $(id).removeClass('highlight');
        }
    }
};
