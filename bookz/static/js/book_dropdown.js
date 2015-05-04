// We add call backs to the dom elements and hook them up to the appropriate
// events
$(document).ready(function() {
    var dd_book_name_by_id = {}
    var dd_author_by_book = {};
    var dd_edition_by_book_and_author = {};
    $("div[id^=alert_dialog_index]").each(function(){
       $(this).fadeOut(2400, function() {
           $(this).remove()
       })
    });
    var selectionFunction = function(selector, setter) {
        $("#"+selector+" option:enabled").each(function() {
            setter.apply(this, arguments)
        });
    };
    var selectedCourseId = null;
    selectionFunction("course",  function() {
        selectedCourseId = this.value
    });
    var selectedBookId = null;
    selectionFunction("book",  function() {
        selectedBookId = this.value
    });
    var selectedAuthor = null;
    selectionFunction("author",  function() {
        selectedAuthor = this.value
    });
    var selectedEdition = null;
    selectionFunction("author",  function() {
        selectedEdition = this.value
    });
   var processServerResponse = function(route_name) {
       return function(request, response) {
           $.getJSON(route_name, request, function (data) {
               var selectOnlyOption = data.length <= 1;
               response($.map(data, function (item, index) {
                   return {
                       label: item.label,
                       value: item.value,
                       selected: selectedCourseId === item.value ? true:selectOnlyOption // Select if only option
                   };
               }));
           })
       }
   }
   $('#dd').cascadingDropdown({
          usePost: true,
          useJson: true,

          selectBoxes: [{
              selector: '.course',
              source: processServerResponse('/course/get_courses'),
              paramName: 'course'
          }, {
              selector: '.book',
              paramName: 'book',
              requires: ['.course'],
              source: processServerResponse("/course/get_books")
          }, {
              selector: '.author',
              paramName: 'author',
              requires: ['.course', '.book'],
              requiresAll: true,
              source:  processServerResponse('/course/get_author')
          }, {
              selector: '.edition',
              requires: ['.course', '.book', '.author'],
              source: processServerResponse('/course/get_edition')
          }]
      });
});