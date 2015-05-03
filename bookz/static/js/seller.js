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

   $('#dd').cascadingDropdown({
          usePost: true,
          useJson: true,

          selectBoxes: [{
              selector: '.course',
              source: function (request, response) {
                  $.getJSON('/courses/get_courses', request, function (data) {
                      var selectOnlyOption = data.length <= 1;
                      dd_book_name_by_id = {}
                      dd_author_by_book = {}
                      dd_edition_by_book_and_author = {}
                      response($.map(data, function (item, index) {
                          return {
                              label: item.name,
                              value: item.id,
                              selected: selectedCourseId === item.id ? true:selectOnlyOption // Select if only option
                          };
                      }));
                  })
              },
              paramName: 'course'
          }, {
              selector: '.book',
              paramName: 'book',
              requires: ['.course'],
              source: function (request, response) {
                  $.getJSON('/courses/get_books', request, function (data) {
                      var selectOnlyOption = data.length <= 1;
                      response($.map(data, function (item, index) {
                          var item_id = parseInt(item.id)
                          if (!(item_id in dd_book_name_by_id)) {
                              dd_book_name_by_id[item_id] = [item.name]
                          } else {
                              dd_book_name_by_id[item_id].push(item.name)
                          }
                          if (!(item.name in dd_author_by_book)) {
                              dd_author_by_book[item.name] = [item.author]
                          } else {
                              dd_author_by_book[item.name].push(item.author)
                          }

                          var name_author = (item.name, item.author)
                          if (!(name_author in dd_edition_by_book_and_author)) {
                              dd_edition_by_book_and_author[name_author] = [item.edition]
                          } else {
                              dd_edition_by_book_and_author[name_author].push(item.edition)
                          }
                          return {
                              label: item.name,
                              value: item.id,
                              selected: selectedBookId === item.id ? true:selectOnlyOption // Select if only option
                          };
                      }));
                  });
              }
          }, {
              selector: '.author',
              paramName: 'author',
              requires: ['.course', '.book'],
              requiresAll: true,
              source: function (request, response) {
                  if (request.book !== "" && request.course !== "") {
                      var books = dd_book_name_by_id[parseInt(request.book)]
                      var selectOnlyOption = books.length <= 1;
                      response($.map(books, function (item, index) {
                          var author = dd_author_by_book[item]
                          return {
                              label: author,
                              value: index,
                              selected: selectedAuthor === author? true:selectOnlyOption // Select if only option
                          }
                      }));
                  }
              }
          }, {
              selector: '.edition',
              requires: ['.course', '.book', '.author'],
              source: function (request, response) {
                  if (request.book !== "" && request.course !== "" && request.author !== "") {
                      var books = dd_book_name_by_id[parseInt(request.book)]
                      books.forEach(function (book_name) {
                          var author_names = dd_author_by_book[book_name]
                          author_names.forEach(function (author) {
                              var edition = dd_edition_by_book_and_author[(book_name, author)]
                              var selectOnlyOption = edition.length <= 1;
                              response($.map(edition, function (item, index) {
                                  return {
                                      label: item,
                                      value: index,
                                      selected: selectedEdition === item? true:selectOnlyOption // Select if only option
                                  }
                              }));
                          })
                      });

                  }
              }
          }]
      });
});