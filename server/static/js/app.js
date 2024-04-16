$(document).ready(function () {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })

    $('#languageChangeInputTop').change(function () {
        $(this).parents('form').submit();
    });

    $('#languageChangeInputBottom').change(function () {
        $(this).parents('form').submit();
    });
});
