$(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip();

    $('#languageChangeInput').change(function () {
        $(this).parents('form').submit();
    });
});
