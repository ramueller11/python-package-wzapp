# set the path so we can directly import wz app
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(os.path.dirname(__file__)))))

# Begin Example
from wzapp import WebApp, HTTPResponse
from werkzeug.exceptions import Forbidden

app = WebApp()
app.name = 'Static Filesystem Example'

@app.view('/')
def homepage(req):
    return HTTPResponse("""
    <h1>Static File System Example</h1>
    <p>If you can see the image below, the filesystem was mounted.</p>
    <img src='/static/an_image.png'></img>
    <br><br>
    Click <a href='/static/boring.txt'>here</a> to read our terms of service.
    <br><br>
    If you want to be really naughty, take a look at the <a href='/static/.htpasswd'>.htpasswd</a> or 
    <a href='/static/.my.cnf'>.my.cnf</a> files.<br>
    """, mimetype='text/html')

app.mount_fsdir('/static', os.path.join(os.getcwd(), 'static'))

if __name__ == '__main__':
    app.run()
