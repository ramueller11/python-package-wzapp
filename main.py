import werkzeug as _wz
from werkzeug.wrappers import Request as HTTPRequest, Response as HTTPResponse
from werkzeug.routing import Map as RouteTable, Rule, Submount
from werkzeug import exceptions
import mimetypes
from sys import exc_info as _exc_info
import os, re
import traceback as _tb

# -----------------------------------

class WebAppError( Exception ):
    pass

# -----------------------------------

class ExceptionResponse( HTTPResponse ):
    def __init__(self, ex):
        HTTPResponse.__init__(self)

        ex_typ, inst, ex_tb = _exc_info()

        ex_typ  = ex_typ.__name__
        ex_msg = str(ex)

        tb = _tb.extract_tb(ex_tb, limit=100)

        html_templ =\
        """
        <html>
        <body style='padding:2em; font-size: 10pt; font-family: sans-serif; display: flex; flex-direction: column; justify-content: center; 
                   height: calc(95vh - 4em); overflow:hidden; '>
        <div>
            <div style='margin: 2em auto; text-align: center; display: flex; justify-content: center'>
                <div style='display: inline-block; font-size: 8em; padding: 2pt 10pt; color: #900;'>&#x26A0</div>
                <div style='display: inline-block; text-align: center;'>
                    <span style='font-size: 6em;font-weight: bold;'>Yikes!</span><br>
                    <span style='font-size: 2em; color: #888;'>An unexpected error occured during processing of this request.</span>
                </div>
            </div>
            <div style='padding: 2em 4em; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc;'>
                <span style='display: inline-block; margin-bottom: 2em; font-size: 2em; font-weight: bold;'>%s: %s</span><br>
                <span style="font-size: 1.5em; padding: 1em;">Error Stack:</span>
                <table style="margin: 1em 4em; font-size: 1em; font-family: monospace; background: #eee;">
                   %s
                </table>
            </div>
        </div>
        </summary>
        </body>
        </html>
        """

        tb_row_templ =\
        """
        <tr>
            <td style='text-align:right;'>%s:<span style='font-weight:bold; vertical-align: top;'>%5i</span></td>
            <td style='color: navy; text-align:right; vertical-align: top; padding-right: 4em;'>%s</td>
            <td>%s</td>
        </tr>
        """

        ftb = ''

        for r in tb:
            src, lineno, fn, ln = tuple(r)
            if len(src) > 40: src = '...' + src[-37:]
            ftb += tb_row_templ % (src, lineno, fn, ln)

        self.status_code = 500
        self.headers['Content-Type'] = 'text/html'
        self.data = html_templ % (ex_typ, ex_msg, ftb,)


class ErrorResponse( HTTPResponse ):
    def __init__(self, message,title='Oops!', icon='&#x26A0', status=400):
        HTTPResponse.__init__(self)

        html_templ = \
            """
            <html>
            <body style='padding:2em; font-size: 10pt; font-family: sans-serif; display: flex; flex-direction: column; justify-content: center; 
                       height: calc(95vh - 4em); overflow:hidden; '>
            <div>
                <div style='margin: 2em auto; text-align: center; padding: 4em; border-top: 2px solid #ccc; border-bottom: 2px solid #ccc;''>
                    <span style='font-size: 8em; color: darkred; padding-right: 0.25em;'>%s</span>
                    <span style='font-size: 6em;font-weight: bold; vertical-align: 0.1em;'>%s</span><br>
                    <span style='font-size: 3em; color: #888;'>%s</span>
                </div>
            </div>
            </body>
            </html>
            """

        self.headers = {'Content-Type':'text/html'}
        self.data = html_templ % (icon, title, message)
        self.status_code = status


# ----------------------------------

class WebApp():
    def __init__(self, name=None, version=None ):
        self.name = name if name != None else 'webserver'
        self.version = version if version else '0.1'
        self.server_addr = 'localhost'
        self.server_port = 8888
        self.route_table = RouteTable()
        self.router  = None
        self.exception_handler   = ExceptionResponse
        self.http_error_handler  = lambda x: ErrorResponse(message=x.description.replace('. ','.<br>'), title=x.name, status=x.code)
        self.app_error_handler   = lambda x: ErrorResponse(message=str(x).replace('. ','.<br>'))

    def mount_subapp(self, subapp, prefix=None):
        if prefix == None:
            for r in subapp.route_table.iter_rules():
                self.route_table.add(r)
        else:
            tree = Submount('/' + prefix.strip('/'),
                [r for r in subapp.route_table.iter_rules()]
            )
            self.route_table.add(tree)

    def mount_fsdir(self, urlpath, localdir, allowSubdirs=True, filename_regex='.*' ):
        import werkzeug.wsgi
        localdir = os.path.realpath(localdir)

        def _serve_file(req, path):
            allowChars = 'abcdefghijklmnopqrstuvwxyz0123456789_. /'
            safepath = ''.join([ c for c in path if c.lower() in allowChars ])

            bn = safepath.split('/')[-1]
            if not allowSubdirs: safepath=bn

            #do not serve '.' files or directories
            if len(bn) < 1:  raise exceptions.Forbidden()
            if bn[0] == '.': raise exceptions.Forbidden()

            #check the match regex
            filter_chk = re.match(filename_regex, bn, re.I) != None

            if not filter_chk: raise exceptions.Forbidden()

            path_parts = [ x for x in safepath.split('/') if len(x.strip()) > 0 ]
            path_parts.insert(0, localdir )
            fspath = os.path.realpath( os.path.join( *path_parts ) )

            #ensure same file root, not sure how this is possible?
            if fspath.find(localdir) != 0: raise exceptions.Forbidden()
            if not os.path.isfile(fspath): raise exceptions.NotFound()

            #get mimetype
            filetype = mimetypes.guess_type(bn,strict=True)
            filetype = filetype[0] if len(filetype) > 1 else 'application/octet-stream'
            filesize = os.stat(fspath).st_size

            return HTTPResponse(
                werkzeug.wsgi.FileWrapper(open(fspath,'rb')),
                headers={'Content-Length': filesize, 'Content-Type': filetype },
                         direct_passthrough=True
            )

        if allowSubdirs:
            self.route_table.add(Rule('/%s/<path:path>' % urlpath.strip('/'), endpoint=_serve_file ))
        else:
            self.route_table.add(Rule('/%s/<string:path>' % urlpath.strip('/'), endpoint=_serve_file ))

    # ----------------------------------------------------

    def view(self, route, method=('GET'), **kwargs ):
        """
        This is a decorator the creates a route_table entry for a given
        function.

        :param route: The route specification (Werkzeug notation)
        :param method: A HTTP method (string) or list of methods (tuple,list) to bind to
        :param kwargs: A list of keywords used in
        :return:
        """
        if isinstance(method, (str,type(u'a')) ):
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
            req  = HTTPRequest(ws_env)

            try:
                view_fn, pars = self.router.match(req.path)

            except exceptions.HTTPException as ex:
                if ex.code < 400 and hasattr(ex, 'new_url'):
                    return ex(ws_env, ws_start_trigger)
                else:
                    raise

            #set the application reference
            setattr(req, '_app', self)

            if len(pars) < 1:
                resp = view_fn(req)
            else:
                resp = view_fn(req, **pars)

        except exceptions.HTTPException as ex:
            resp = self.http_error_handler(ex)
        except WebAppError as ex:
            resp = self.app_error_handler(ex)
        except Exception as ex:
            resp = self.exception_handler(ex)

        # return the response
        return resp(ws_env, ws_start_trigger)

    
    def __call__(self, ws_env, ws_start_trigger):
        return self._wsgi_handler(ws_env,ws_start_trigger)
    
    def run(self, **kwargs):
        print('Running %s v.%s' % (self.name,self.version) )
        _wz.serving.run_simple(self.server_addr, self.server_port, self._wsgi_handler, **kwargs)

# ----------------------------

app = WebApp()

@app.view('/')
def homepage(req):
    resp = HTTPResponse()
    resp.data = 'Homepage'

    return resp

@app.view('/photo/<id>/')
@app.view('/photo/<id>')
def view_photo(req, id):
    resp = HTTPResponse()
    resp.data = 'Photo %s' % id
    return resp

@app.view('/yikes')
def yikes(req):
    raise exceptions.BadRequest()

@app.view('/except/<msg>')
def except_test(req, msg):

    if hasattr(exceptions,msg):
        raise getattr(exceptions,msg)

    raise RuntimeError(msg)

subapp = WebApp()

@subapp.view('/')
def subapp_homepage(req):
    resp = HTTPResponse()
    resp.data = 'This is the subapplication'
    return resp

@subapp.view('/<path:x>')
def subapp_test(req, x):
    resp = HTTPResponse()
    resp.data = 'This is the subapplication %s %s' % (x, req.args)
    return resp

app.mount_subapp(subapp,'/subapp')


app.mount_local_dir('files',"E:\\Movie Library\\Manifest\\S01E16")


# ---------------------

if __name__ == '__main__':
    app.run()