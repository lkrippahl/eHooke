"""eHooke HTTP server module

This module implements HTTP access to eHooke instances

HTTP request handling based on examples by Doug Hellmann on
Python Module of the Week:
    http://pymotw.com/2/BaseHTTPServer/index.html
"""

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import urlparse
import threading
import uuid
import os
import string
import re
from htmlconstants import *
from params import Parameters, MaskParameters, FluorFrameParameters
from ehooke import EHooke
from skimage.io import imsave, imread

    
class Session:
    """eHooke session

       This class manages the folder with data and report files (in the server path)
       and a EHooke instance for running the computations
    """
    
    def __init__(self):        
        self.id=str(uuid.uuid4())
        """str: Unique identifier for this session"""
        self.folder = SESSION_FOLDER+'/'+self.id
        """str: main session folder with all generated files"""
        self.data_folder = self.folder+'/Data'
        """str: subfolder for session data (phase, fluor and params file)"""
        self.params = Parameters()
        """Parameters: parameters object to share with ehooke instance"""
        self.params_file = None
        """str: parameters file name"""
        self.fluor_file = None
        """str: fluor file name, to override parameters so that params can be imported from other sessions"""
        self.phase_file = None
        """str: phase file name, to override parameters so that params can be imported from other sessions"""
        self.name = 'Session'
        """str: session name, user defined"""
        self.description = ''
        """str: session description, user defined"""

        self.mask_image = None
        """str: filename for the current mask image, none if no mask is computed"""

        
        self.ehooke = None
        """EHooke: to be initialized upon starting the session (only with images and parameters"""
        #TODO change this to work with multiprocessing
        #<LK 2015-06-30>

        

    def setup(self):
        """creates session folder (add other setup stuff here)"""
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)
        if not os.path.exists(self.data_folder):
            os.mkdir(self.data_folder)
            

    def set_phase(self,file_name):
        """sets the phase file without computing anything
           Overrides the file name in the parameters file. This is necessary
           in order to allow importing parameter files to the session
        """
        
        self.phase_file = file_name
        self.params.fluor_frame_params.phase_file = file_name
        

        
    def set_fluor(self,file_name):
        """sets the fluorescence file without computing anything

           Overrides the file name in the parameters file. This is necessary
           in order to allow importing parameter files to the session
        """
        
        self.fluor_file = file_name
        self.params.fluor_frame_params.fluor_file = file_name
        

    def set_parameters_file(self, file_name):
        """sets and reloads parameters
           (but overrides fluor_file and phase_file in order to allow parameter
           updates after uploading the image files
        """
        
        self.params_file = file_name
        self.params.load_parameters(file_name)
        if self.fluor_file != self.params.fluor_frame_params.fluor_file or \
           self.phase_file != self.params.fluor_frame_params.phase_file:
            self.params.fluor_frame_params.fluor_file = self.fluor_file
            self.params.fluor_frame_params.phase_file = self.phase_file
            self.params.save_parameters(file_name)
    
    def start_ehooke(self):
        """Initiates the ehooke process and loads images

           if there is no fluorescence image specified, returns false and error message
           otherwise returns true,''

           if ehooke is not none does nothing and returns ok
        """
        if self.ehooke is not None:
            return (True,'')

        if self.fluor_file is None:
            return (False,'Cannot start eHooke without a fluorescence image')
        self.ehooke = EHooke(self.params)
        self.ehooke.load_images()
        return (True,'')


    def save_overlay(self, back=(1,1,1), fore=(0,1,1), mask='phase',image='phase'):
        """saves the overlay image to overlay.png"""
        
        self.ehooke.save_mask_overlay(self.folder+'/overlay.png',back, fore, mask,image)    
        self.mask_image = self.folder+'/overlay.png'
        
    def recompute_mask(self):
        res,msg = self.start_ehooke()
        if res:
            self.ehooke.create_masks()
            self.save_overlay()
        return (res,msg)
        
        
            

class SessionManager:
    """This is the main class that manages all sessions       
    """
    
    def __init__(self):
        self.sessions={}        
        """dict: dictionary with each session by session ID"""

    def is_valid(self, session_id):
        """Returns True if the session_id is valid, False otherwise"""
        
        return session_id in self.sessions.keys()
    
    def new_session(self):
        """Creates a new session, returning the ID string"""
        new_session=Session()
        self.sessions[new_session.id]=new_session
        new_session.setup()
        return new_session

    def get_session(self,session_id):
        """Returns the session object from id, or None"""
        if session_id in self.sessions.keys():
            return self.sessions[session_id]
        else:
            return None

    def get_session_path(self,session_id):
        """Returns the path to the session folder; includes the path delimiter"""

        session = self.get_session(session_id)
        if session is not None:
            return session.folder+'/'
        else:
            return ''

    def get_session_data_path(self,session_id):
        """Returns the path to the session data folder; includes the path delimiter"""

        session = self.get_session(session_id)
        if session is not None:
            return session.data_folder+'/'
        else:
            return ''


    def update_file(self,session_id,url,file_name):
        """updates the file references for the given session, if valid

        url can be any of: URL_UPPHASE, URL_UPFLUOR, URL_UPPARAMS
        """
        if session_id in self.sessions.keys():
            session = self.sessions[session_id]
            if url == URL_UPPHASE:
                session.set_phase(file_name)
            elif url == URL_UPFLUOR:
                session.set_fluor(file_name)
            elif url == URL_UPPARAMS:
                session.set_parameters_file(file_name)

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
            session = session_manager.get_session(session_id)
            if path == URL_SESSION_PAGE:      
                html = process_html(HTML_SESSION,
                                    {SESSION_ID_TAG:session.id,
                                     SESSION_NAME_TAG:session.name,
                                     SESSION_DESC_TAG:session.description,
                                     FLUOR_TAG:str(session.fluor_file),
                                     PHASE_TAG:str(session.phase_file),
                                     PARAMS_TAG:str(session.params_file)})
            elif path == URL_START:
                session.start_ehooke()
                session.save_overlay()
            elif path == URL_MASK_PAGE:
                print 'ok'
                form = attributes_to_form('maskform',URL_MASK_PARAMETERS[1:]+'?ID='+session_id,
                                          session.params.mask_params,
                                          MaskParameters.exported,
                                          {'algorithm':session.params.mask_params.algorithms})
                html = process_html(HTML_MASK,
                                    {SESSION_ID_TAG:session.id,
                                     SESSION_NAME_TAG:session.name,
                                     FORM_TAG:form})
                
            elif path == URL_MASK_IMAGE:
                if session.mask_image is None:
                    html = open(DEFAULT_MASK,'rb').read()
                else:
                    html = open(session.mask_image,'rb').read()        
        else:
            #if a miscelaneous file is requested, it is only read from the HTML_FOLDER
            html = open(HTML_FOLDER+path.split('/')[-1],'rb').read()
            
        self.send_response(200)
        self.end_headers()  
        self.wfile.writelines(html)
        return
        
    def save_uploaded_file(self,path):
        """Saves a file uploaded (POST) and returns the file name"""

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
                return (True, fn)
            else:
                out.write(preline)
                preline = line
        return (False, "Unexpected end of data.")

    def parse_post_request(self):
        """parses a POST request url (only the url, not the data)

           returns (url, session_id) or (url, None) if id is not valir
        """

        parsed_url = urlparse.urlparse(self.path)
        session_id = None
        url = parsed_url[2]
        if 'ID=' in parsed_url.query:
            session_id = urlparse.parse_qs(parsed_url.query)['ID'][0]
            if not session_manager.is_valid(session_id):
                session_id = None
        return (url, session_id)

    def process_new_session(self):
        """Processes a new session (POST) request
      

        """
        new_session=session_manager.new_session()
        length = int(self.headers.getheader('content-length'))
        postvars = urlparse.parse_qs(self.rfile.read(length))
        if SESSION_NAME in postvars.keys():
            new_session.name = '\n'.join(postvars[SESSION_NAME])
        if SESSION_DESCRIPTION in postvars.keys():
            new_session.description = '\n'.join(postvars[SESSION_DESCRIPTION])
        return new_session.id
    
  
    def handle_post_request(self):
        """Handles file upload and other stuff (WiP...)

           Source: Huang, Tao at https://gist.github.com/UniIsland/3346170

           Returns (True, session_id) if successful, or (False, error_message) otherwise
        """
        (url,session_id) = self.parse_post_request()
        if url == NEW_SESSION:
            session_id = self.process_new_session()
        elif url in URLS_UPLOAD:
            path = session_manager.get_session_data_path(session_id)
            result, msg = self.save_uploaded_file(path)
            if result:                
                session_manager.update_file(session_id,url, msg)
            else:
                return (False, 'Failed to save file: '+msg)
        elif url == URL_MASK_PARAMETERS:
            session = session_manager.get_session(session_id)
            length = int(self.headers.getheader('content-length'))
            postvars = urlparse.parse_qs(self.rfile.read(length))
            form_to_attributes(postvars,
                               MaskParameters.exported,
                               session.params.mask_params)
            res,msg = session.recompute_mask()
            if res:
                return (True, SERVER_URL+URL_MASK_PAGE+'?ID='+session_id)
            else:
                return (False,msg)
            
        #by default, assume ok and return to session page
        return (True, SERVER_URL+URL_SESSION_PAGE+'?ID='+session_id)

    def do_POST(self):
        (res,msg)=self.handle_post_request()
        print res, msg
        if not res:
            # upload failed
            self.send_response(200)       
            self.end_headers()        
            self.wfile.write('Request failed: %s\n' % msg)
        else:
            #upload OK, redirecting to approapriate page
            self.redirect(msg)
            
        return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""



session_manager=SessionManager()
"""Global variable to manage sessions.

   This is ugly but seems the best way to give the http handler
   access to the session manager.
"""

    

if __name__ == '__main__':

    #For safety reasons, server is confined to local host
    #Change 'localhost' to '' to enable remote access
    server = ThreadedHTTPServer(('localhost', 8081), Handler)    
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()
