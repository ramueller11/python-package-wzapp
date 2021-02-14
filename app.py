from . import HTTPResponse, HTTPRequest, exceptions, RouteTable, ExceptionResponse, ErrorResponse, Rule, WebAppError
import os, re, mimetypes


# ----------------------------------

def _default_exception_handler(ex):
    """
    Default exception handler for unhandled python Exceptions.

    :param ex: Exception to represent.
    :return: returns a HTTPResponse representation.
    """
    return ExceptionResponse(ex)


# ------------------------------------------------

def _default_http_error_handler(ex):
    """
    Default exception handler for werkzeug HTTPExceptions.

    :param ex: HTTPException to represent.
    :return: returns a HTTPResponse representation.
    """

    msg = ex.description if hasattr(ex, 'description') else str(ex)
    title = ex.name if hasattr(ex, 'name') else type(ex).__name__
    code = ex.code if hasattr(ex, 'code') else 400

    return ErrorResponse(message=ex.description.replace('. ', '.<br>'), title=ex.name, status=ex.code)


# ------------------------------------------------


def _default_app_error_handler(ex):
    """
    Default exception handler for WebAppErrors.

    :param ex: WebAppError to represent.
    :return: returns a HTTPResponse representation.
    """

    # create an HTML linebreak between senteences
    msg = str(ex).replace('. ', '.<br>')

    return ErrorResponse(message=msg)


# ------------------------------------------------


class WebApp():
    """
    Represents a Web Application and can be directly
    called using WSGI.
    """

    def __init__(self, name=None, version=None):
        """
        Initialize the Web Application

        :param name: name of the web application
        :param version: version of the web application
        """

        # define the name of the application and version
        self.name = name if name != None else 'My wzApp'
        self.version = version if version else '0.1'

        # server information (used by run method and will be automatically updated during runtime)
        self.server_addr = 'localhost'
        self.server_port = 8888

        # contains the routing rules (werkzeug.routing.Map)
        self.route_table = RouteTable()

        # this is the routing table that has been bound to the environment at runtime
        # and provides the routing (werkzeug.routing.MapAdapter)
        self.router = None

        # This is the function is called when a unhandled python exception is thrown.
        # this can be overwritten if desired.
        self.exception_handler = _default_exception_handler

        # This is the function is called when a unhandled HTTPError is thrown.
        # this can be overwritten if desired.
        self.http_error_handler = _default_http_error_handler

        # This is the function is called when a unhandled WebAppError is thrown.
        # this can be overwritten if desired.
        self.app_error_handler = _default_app_error_handler

    # -------------------------------------------------------------------

    def mount_subapp(self, subapp, prefix=None):
        """
        Mounts another instance of a WebApp into the routing table
        of this application.

        :param subapp: a WebApp instance
        :param prefix: the path prefix to mount (default=None)

        :return: None
        """

        if prefix == None:
            for r in subapp.route_table.iter_rules():
                self.route_table.add(r)
        else:
            from werkzeug.routing import Submount

            tree = Submount('/' + prefix.strip('/'),
                            [r for r in subapp.route_table.iter_rules()]
                            )
            self.route_table.add(tree)

    # -------------------------------------------------------------------

    def mount_fsdir(self, urlpath, localdir, allowSubdirs=True, filename_regex='.*'):
        """
         Provide an proxy of a filesystem directory for a given url path prefix in the
         routing table.

         Note that for security considerations only paths that do not contain special characters
         such as: @#!$%^&*()+=:;<>,?~. In addition, all paths that start with a period [.] such as
         .htaccess or .htpasswd are forbidden.

         :param urlpath:  the url path prefix to mount the file system to
         :param localdir: the path on the local machine to source files from
         :param allowSubdirs: allow traversal of all subdirectories of the local dir (True) or
                              only immediate files
         :param filename_regex: only allow access to files with basenames matching a given pattern.
                                for example only css,html,js files can be filtered by '.*[.](css|html|js)$'

         :return: None
         """

        import werkzeug.wsgi
        localdir = os.path.realpath(localdir)

        def _serve_file(req, path):

            # string of allowable characters in path
            allowChars = 'abcdefghijklmnopqrstuvwxyz0123456789_-. /'
            safepath = ''.join([c for c in path if c.lower() in allowChars])

            bn = safepath.split('/')[-1]
            if not allowSubdirs: safepath = bn

            # do not serve '.' files or directories
            if len(bn) < 1:  raise exceptions.Forbidden()
            if bn[0] == '.': raise exceptions.Forbidden()

            # check the match regex
            filter_chk = re.match(filename_regex, bn, re.I) != None
            if not filter_chk: raise exceptions.Forbidden()

            # generate the local path on the filesystem
            path_parts = [x for x in safepath.split('/') if len(x.strip()) > 0]
            path_parts.insert(0, localdir)
            fspath = os.path.realpath(os.path.join(*path_parts))

            # ensure same file root, not sure how this is possible?
            if fspath.find(localdir) != 0: raise exceptions.Forbidden()
            if not os.path.isfile(fspath): raise exceptions.NotFound()

            # get mimetype and file size
            filetype = mimetypes.guess_type(bn, strict=True)
            filetype = filetype[0] if len(filetype) > 1 else 'application/octet-stream'
            filesize = os.stat(fspath).st_size

            # generate the response, use the direct_passthrough for this response
            return HTTPResponse(
                werkzeug.wsgi.FileWrapper(open(fspath, 'rb')),
                headers={'Content-Length': filesize, 'Content-Type': filetype},
                direct_passthrough=True
            )

        if allowSubdirs:
            self.route_table.add(Rule('/%s/<path:path>' % urlpath.strip('/'), endpoint=_serve_file))
        else:
            self.route_table.add(Rule('/%s/<string:path>' % urlpath.strip('/'), endpoint=_serve_file))

    # ----------------------------------------------------

    def view(self, route, method=('GET'), **kwargs):
        """
        This is a decorator the creates a route_table entry for a given
        function.

        :param route: The route specification (Werkzeug notation)
        :param method: A HTTP method (string) or list of methods (tuple,list) to bind to
        :param kwargs: A list of keywords used in
        :return:
        """
        if isinstance(method, (str, type(u'a'))):
            method = (method,)

        kwargs['methods'] = method
        if 'endpoint' in kwargs: kwargs.pop()

        def wrapper(fn):
            self.route_table.add(Rule(route, **kwargs, endpoint=fn))
            return fn

        return wrapper

    # ------------------------------------------------------------------

    def _wsgi_handler(self, ws_env, ws_start_trigger):
        # this is a low level WSGI application function that serves as the
        # main HTTP handing function.

        if self.router is None:
            # extract server info from the environment
            self.server_port = ws_env['SERVER_PORT']
            self.server_addr = ws_env['SERVER_NAME']

            # setup the router
            self.router = self.route_table.bind_to_environ(ws_env)

        try:
            # use the view function to generate the HTTP Response object
            # the request is always passed to view functions
            req = HTTPRequest(ws_env)

            try:
                view_fn, pars = self.router.match(req.path)

            except exceptions.HTTPException as ex:
                if ex.code < 400 and hasattr(ex, 'new_url'):
                    return ex(ws_env, ws_start_trigger)
                else:
                    raise

            # set the application reference
            setattr(req, '_app', self)

            # dispatch the view function
            if len(pars) < 1:
                resp = view_fn(req)
            else:
                resp = view_fn(req, **pars)

        # exception triage
        except exceptions.HTTPException as ex:
            resp = self.http_error_handler(ex)
        except WebAppError as ex:
            resp = self.app_error_handler(ex)
        except Exception as ex:
            resp = self.exception_handler(ex)

        # return the response
        return resp(ws_env, ws_start_trigger)

    # ------------------------------------------------------------------

    def __call__(self, ws_env, ws_start_trigger):
        # this is python magic function which allows the app class to have the
        # signiture expected for a WSGI application() function. This is a
        # direct hop to _wsgi_handler
        return self._wsgi_handler(ws_env, ws_start_trigger)

    # ------------------------------------------------------------------

    def run(self, **kwargs):
        """
        Run the application using a built-in HTTP server (werkzeug.serving.run_simple).
        :param kwargs: Parameters for the werkzeug.serving.run_simple server.
        :return:
            None
        """

        import werkzeug.serving
        print('Running %s v.%s' % (self.name, self.version))
        werkzeug.serving.run_simple(self.server_addr, self.server_port, self._wsgi_handler, **kwargs)

# ----------------------------------------------------------------------------------------------------------------------