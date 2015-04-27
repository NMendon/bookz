// We add call backs to the dom elements and hook them up to the appropriate
// events
$(document).ready(function(){
    var dd_book_name_by_id = {}
    var dd_author_by_book = {};
    var dd_edition_by_book_and_author = {};

   $('#dd').cascadingDropdown({
    usePost: true,
    useJson: true,

    selectBoxes: [
            {
                selector: '.course',
                source: function(request, response) {
                    $.getJSON('/courses/get_courses', request, function (data) {
                        var selectOnlyOption = data.length <= 1;
                        dd_book_name_by_id = {}
                        dd_author_by_book = {}
                        dd_edition_by_book_and_author = {}
                        response($.map(data, function(item, index) {
                            return {
                                label: item.name,
                                value: item.id,
                                selected: selectOnlyOption // Select if only option
                            };
                        }));
                    })
                },
                paramName: 'course'
            },
            {
                selector: '.book',
                paramName: 'book',
                requires: ['.course'],
                source: function(request, response) {
                    $.getJSON('/courses/get_books', request, function(data) {
                        var selectOnlyOption = data.length <= 1;
                        response($.map(data, function(item, index) {
                            var item_id = parseInt(item.id)
                            if(!(item_id in dd_book_name_by_id)) {
                                dd_book_name_by_id[item_id] = [item.name]
                            } else {
                                 dd_book_name_by_id[item_id].push(item.name)
                            }
                            if(!(item.name in dd_author_by_book)) {
                                dd_author_by_book[item.name] = [item.author]
                            } else {
                                dd_author_by_book[item.name].push(item.author)
                            }

                            var name_author = (item.name, item.author)
                            if(!(name_author in dd_edition_by_book_and_author)) {
                                dd_edition_by_book_and_author[name_author] = [item.edition]
                            } else{
                                dd_edition_by_book_and_author[name_author].push(item.edition)
                            }
                            return {
                                label: item.name,
                                value: item.id,
                                selected: selectOnlyOption // Select if only option
                            };
                        }));
                    });
                }
            },
            {
                selector: '.author',
                paramName: 'author',
                requires: ['.course', '.book'],
                requiresAll: true,
                source: function(request, response) {
                        if(request.book !== "" && request.course !== ""){
                            var books = dd_book_name_by_id[parseInt(request.book)]
                            var selectOnlyOption = books.length <= 1;
                            response($.map(books, function(item, index){
                                return {
                                    label: dd_author_by_book[item],
                                    value: index,
                                    selected: selectOnlyOption
                                }
                            }));
                        }
                }
            },
            {
                selector: '.edition',
                requires: ['.course', '.book', '.author'],
                source: function(request, response) {
                    if(request.book !== "" && request.course !== "" && request.author !== "") {
                        var books = dd_book_name_by_id[parseInt(request.book)]
                        books.forEach(function(book_name){
                            var author_names = dd_author_by_book[book_name]
                            author_names.forEach(function(author){
                                var edition = dd_edition_by_book_and_author[(book_name, author)]
                                var selectOnlyOption = edition.length <= 1;
                                response($.map(edition, function(item, index) {
                                    return {
                                        label: item,
                                        value: index,
                                        selected: selectOnlyOption
                                    }
                                }));
                            })
                        }) ;

                    }
                }
            }
        ]
    });
});