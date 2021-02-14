"""
wzapp
*featherweight WeurkZeug web APPlications*

This package is a nano-framework built upon the werkzeug library.
Compared to flask, this is more of a sip -- containing only the essential application structure.
"""

# import basic data structures from werkzeug
# in principle, we could generalize and make HTTPRequest and HTTPResponse interfaces
# and interconnect between backends.
from werkzeug.wrappers import Request as HTTPRequest, Response as HTTPResponse

#define routing constructs
from werkzeug.routing import Map as RouteTable, Rule

#let's mirror all of the nicely defined HTTPExceptions
from werkzeug import exceptions

from .errors import WebAppError, ExceptionResponse, ErrorResponse
from .app import WebApp