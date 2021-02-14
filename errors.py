from . import HTTPResponse
import os, sys
import traceback as _tb

# -----------------------------------

class WebAppError( Exception ):
    """
    Define a dedicated web application specific error.
    """
    pass

# -----------------------------------

class ExceptionResponse( HTTPResponse ):
    """
    An HTTP Response designed to represent a Python Exception complete with traceback.
    """
    def __init__(self, ex):
        HTTPResponse.__init__(self)

        ex_typ, inst, ex_tb = sys.exc_info()

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

# --------------------------------------------------------

class ErrorResponse( HTTPResponse ):
    """
    An HTTP Response designed to represent a user-facing error message.
    """
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

# --------------------------------------------------------