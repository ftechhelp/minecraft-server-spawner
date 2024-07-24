from bottle import route, run, template

@route('/')
def index():
    return template('./templates/index')


run(host='0.0.0.0', port=8888, reloader=True, debug=True)