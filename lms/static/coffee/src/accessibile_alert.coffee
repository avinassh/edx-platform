
class SRAlert
  constructor: ->
    $('body').append('<div id="reader-feedback" class="sr" aria-role="alert" aria-hidden="false" aria-atomic="true" aria-live="polite"></div>')
    @el = $('#reader-feedback')

  readElts: (elts) ->
    feedback = ''
    $.each elts, (idx, value) =>
      feedback += '<p>' + $(value).html() + '</p>\n'
    @el.html(feedback)

  readText: (text) ->
    @el.text(text)


window.SR = new SRAlert
