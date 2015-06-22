"""eHooke HTTP server module

This module implements HTTP access to eHooke instances

HTTP request handling based on examples by Doug Hellmann on
Python Module of the Week:
    http://pymotw.com/2/BaseHTTPServer/index.html


"""


from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import cgi
import urlparse
import threading
import uuid
import os
import string
import re

SESSION_FOLDER='sessions'
"""str: base folder for sessions

   This folder should exist when executing the server.
"""

SERVER_URL='http://127.0.0.1:8081'
"""str: url for the server"""

SESSION_ID_TAG='[SESSIONID]'
"""str: id tag to be replaced by session id in html source"""
HTML_FOLDER_TAG='[HTML]'
"""str: id tag to be replaced by the html folder"""
SESSION_FOLDER_TAG='[SESSION]'
"""str: id tag to be replaced by the current session folder"""

NEW_SESSION='/newsession'
"""str: url path indicating a new session request"""
SESSION_PAGE='/session'
"""str: url path for the page of a session indicated by an ?ID=id param"""
UPLOAD_FILE='/upload'
"""str: url path for the upload page for a session indicated by an ?ID=id param"""

HTML_FOLDER='html/'
"""str: path for html, css, js files"""

HTML_UPLOAD=HTML_FOLDER+'upload.html'
"""str: html file for the upload page"""
HTML_SESSION=HTML_FOLDER+'session.html'
"""str: html file for the session template page"""
HTML_INDEX=HTML_FOLDER+'index.html'
"""str: html file for the main page"""


def process_html(html_source,session_id=None):
    fil = open(html_source)
    source = fil.read()
    fil.close()
    source=string.replace(source,HTML_FOLDER_TAG,HTML_FOLDER)        
    if session_id is not None:
        source=string.replace(source,SESSION_ID_TAG,session_id)        
    return source
    
class Session:
    """eHooke session

       This class manages the folder with data and report files (in the server path)
       and a EHooke instance for running the computations
    """
    
    def __init__(self):        
        self.id=str(uuid.uuid4())
        """str: Unique identifier for this session"""
        self.folder=SESSION_FOLDER+'/'+self.id

    def setup(self):
        """creates session folder (add other setup stuff here)"""
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)
        
        

class SessionManager:
    """This is the main class that manages all sessions
       
    """
    def __init__(self):
        self.sessions={}        
        """dict: dictionary with each session by session ID"""
        
    def new_session(self):
        """Creates a new session, returning the ID string"""
        new_session=Session()
        self.sessions[new_session.id]=new_session
        new_session.setup()
        return new_session.id

    def get_session_path(self,session_id):
        """Returns the path to the session folder; includes the path delimiter"""
        print session_id
        if session_id in self.sessions.keys():
            return self.sessions[session_id].folder+'/'
        else:
            return ''

session_manager=SessionManager()
"""Global variable to manage sessions.

   This is ugly but seems the best to give the handler access to the session
   manager.
"""

class Handler(BaseHTTPRequestHandler):

    def redirect(self,url):
        self.send_response(301)       
        self.send_header('Location',url)
        self.send_header( 'Connection', 'close' );
        self.end_headers()        
    
    def do_GET(self):
        """Process GET requests

        Handles different requests for
            index page 
            file upload page (with id)
            session page (with id)
            other files
        """
        html='Error 404'

        parsed_url = urlparse.urlparse(self.path)
        path = parsed_url[2]
        if path=='/' or path.upper()=='/INDEX.HTML':
            html = process_html(HTML_INDEX)
        elif 'ID=' in parsed_url.query:
            session_id = urlparse.parse_qs(parsed_url.query)['ID'][0]        
            if path==UPLOAD_FILE:
                html = process_html(HTML_UPLOAD,session_id)
            elif path==SESSION_PAGE:
                html = process_html(HTML_SESSION,session_id)
          
        elif path==NEW_SESSION:            
            new_session_id=session_manager.new_session()
            self.redirect(SERVER_URL+SESSION_PAGE+'?ID='+new_session_id)
        else:
            # FIXME: This is unsafe; there should be a check to prevent requests
            #        for files outside the permissible scope
            #        <LK 2015-06-21 p:1>
            fn = path[1:]
            print 'Name:', fn
            if os.path.exists(fn):
                fil = open(fn)
                html = fil.read()
                fil.close()
            
        self.wfile.writelines(html)
        return
  
    def handle_post_request(self):
        """Handles file upload and other stuff (WiP...)

           Source: Huang, Tao at https://gist.github.com/UniIsland/3346170
        """
        print self.path
        parsed_url = urlparse.urlparse(self.path)
        print parsed_url
        path = parsed_url[2]
        if 'ID=' in parsed_url.query:
            session_id = urlparse.parse_qs(parsed_url.query)['ID'][0]
        else:
            return (False, "No session ID for uploading")            
        print session_id
        if path=='/upload':                
            boundary = self.headers.plisttext.split("=")[1]
            remainbytes = int(self.headers['content-length'])
            line = self.rfile.readline()
            remainbytes -= len(line)
            if not boundary in line:
                return (False, "Content NOT begin with boundary")
            line = self.rfile.readline()
            print line
            remainbytes -= len(line)
            fn = re.findall(r'filename="(.*)"', line)
            if len(fn)==0:
                return (False, "Can't find out file name...")            
            path = session_manager.get_session_path(session_id)
            if path=='':
                return (False, "Invalid session id")
            fn = os.path.join(path, fn[0])            
            line = self.rfile.readline()
            remainbytes -= len(line)
            line = self.rfile.readline()
            remainbytes -= len(line)
            print fn
            try:
                out = open(fn, 'wb')
            except IOError:
                return (False, "Can't create file to write, do you have permission to write?")
                    
            preline = self.rfile.readline()
            remainbytes -= len(preline)
            while remainbytes > 0:
                line = self.rfile.readline()
                remainbytes -= len(line)
                if boundary in line:
                    preline = preline[0:-1]
                    if preline.endswith('\r'):
                        preline = preline[0:-1]
                    out.write(preline)
                    out.close()
                    return (True, session_id)
                else:
                    out.write(preline)
                    preline = line
            return (False, "Unexpect Ends of data.")

    def do_POST(self):
        (res,msg)=self.handle_post_request()        
        if not res:
            # upload failed
            self.send_response(200)       
            self.end_headers()        
            self.wfile.write('Upload failed: %s\n' % msg)
        else:
            #upload OK, redirecting to session page
            self.redirect(SERVER_URL+SESSION_PAGE+'?ID='+msg)
            
        return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

    

if __name__ == '__main__':

    #For safety reasons, server is confined to local host
    #Change 'localhost' to '' to enable remote access
    server = ThreadedHTTPServer(('localhost', 8081), Handler)    
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()
