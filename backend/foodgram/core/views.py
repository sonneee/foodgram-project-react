from django.http import HttpResponse


def page_not_found(request, exception):
    html = '''<html><h1>Custom 404</h1>
  <p>Страницы %s не существует, попробуйте позднее</p>
    </html>''' % request.path
    return HttpResponse(html)
