# set the path so we can directly import wz app
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(os.path.dirname(__file__)))))

# Begin Example
import wzapp

app = wzapp.WebApp()
app.name    = 'Hello World'
app.version = '0.1.0'

@app.view('/')
def homepage(req):
    resp = wzapp.HTTPResponse('Hello World!')
    return resp

if __name__ == '__main__':
    app.run()

# -----------------------------------------------------------
