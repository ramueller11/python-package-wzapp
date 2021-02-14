# set the path so we can directly import wz app
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(os.path.dirname(__file__)))))

# Begin Example
from wzapp import WebApp, HTTPResponse
from werkzeug.exceptions import Forbidden

app = WebApp()
app.name = 'Routing Example'

#basic route
@app.view('/')
def homepage(req):
   return HTTPResponse("""
   <h1>Routing Example</h1>
   <p>
   This is a silly example of a multi-page site.
   </p>
   
   Greetings:<br>
   <ul>
   <li><a href='/name/alex'>Alex</a></li>
   <li><a href='/name/bob'>Bob</a></li>
   </ul>
      
   An error:
   <ul>
   <li><a href='/error/out of coffee'>Out of Coffee!</a></li>
   <li><a href='/error/das blinkenlighten'>Das Blinkenlighten</a></li>
   </ul>
   
   A top secret site: 
   
   <ul>
   <li><a href='/topsecret'>Top Secret Site</a></li>
   </ul>
   
   """, mimetype='text/html')

#using the Werkzeug placeholders to parameterize
# a URL tree. name is passed as a python argument
@app.view('/name/<string:name>')
def namepage(req, name):
   return HTTPResponse('<h1>Greetings, %s!</h1>' % name, mimetype='text/html')

@app.view('/topsecret')
def topsecret(req):
    raise Forbidden()

#the application has built in error and exception
#handler functions which can be modified.
@app.view('/error/<string:key>')
def errorpage(req, key):
   raise RuntimeError(key)

if __name__ == '__main__':
    app.run()

# -----------------------------------------------------------
