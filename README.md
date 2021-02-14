# wzapp

*featherweight WeurkZeug web APPlications*

This package is a nano-framework built upon the [werkzeug](https://werkzeug.palletsprojects.com/) library. Compared to [flask](https://flask.palletsprojects.com/), this is more of a **sip** -- containing only the essential application structure.

## Installation
No `setup.py` is yet defined. Copy the python repository into your `site-packages` or on an `ad-hoc` manner in your source code.

## Usage
The library defines a **WebApp** class which represents the web application. The application contains a `routing_table` (`werkzeug.routing.Map`) where view functions are registered into the application. View functions can be either added to the routing_table using the `add` method or the `WebApp.view` decorator which automatically defines it.

View functions are python functions which are provided the http request ( **HTTPRequest** class) and are expected to return a http response object (**HTTPResponse**) or throw an exception in case of error.

## Example
```python
from wzapp import WebApp, HTTPResponse

app = WebApp()

#basic route
@app.view('/')
def homepage(req):
   return HTTPResponse('Hello World!')

#using the Werkzeug placeholders to parameterize 
# a URL tree. name is passed as a python argument
@app.view('/name/<string:name>'
def namepage(req, name):
   return HTTPResponse('Greetings, name!')

#the application has built in error and exception
#handler functions which can be modified.
@app.view('/error/<string:key')
def errorpage(req, key):
   raise RuntimeError(key)


#wsgi mode
application = app

# run stand-alone server (werkzeug.serving.run_simple)
app.run()
```

## License
[MIT](https://choosealicense.com/licenses/mit/)
