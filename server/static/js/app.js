$(document).ready(function () {
    $('#languageChangeInput').change(function () {
        $(this).parents('form').submit();
    });
});