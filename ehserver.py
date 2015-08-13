"""eHooke HTTP server module

This module implements HTTP access to eHooke instances

HTTP request handling based on examples by Doug Hellmann on
Python Module of the Week:
    http://pymotw.com/2/BaseHTTPServer/index.html
"""

from zipfile import ZipFile
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import urlparse
import uuid
import os
import string
import re
from io import BufferedRandom
from htmlconstants import *
from params import Parameters, MaskParameters,FrameParameters
from ehooke import EHooke
from skimage.io import imsave, imread
from shutil import rmtree

SESSION_DATA = '/data'
"""str: folder where session original data files are stored"""

SESSION_PARAMS = 'params.txt'
"""str: file name in data with the parameters (optional)"""

SESSION_MASKS = 'masks.txt'
"""str: file name in data with the list of value images and
   corresponding masks (optional)
"""
    
class Session(object):
    """eHooke session

       This class manages the folder with data and report files (in the server path)
       and a EHooke instance running as an independent process
    """
    
    def __init__(self):        
        self.id=str(uuid.uuid4())
        """str: Unique identifier for this session"""
        self.folder = SESSION_FOLDER+'/'+self.id
        """str: main session folder with all generated files"""
        self.data_folder = self.folder+SESSION_DATA
        """str: subfolder for session data (phase, fluor and params file)"""
        self.params = Parameters()
        """Parameters: parameters object to share with ehooke instance"""
        self.params_file = None
        """str: parameters file name"""
        self.name = 'Session'
        """str: session name, user defined"""
        self.description = ''
        """str: session description, user defined"""

        self.mask_image = None
        """str: filename for the current mask image, none if no mask is computed"""

        self.images = {}
        """dictionary: image value files as keys, mask or none as values"""

        
        self.ehooke = None
        """process: to be initialized upon starting the session (only with images and parameters)"""
        #TODO change this to work with multiprocessing
        #<LK 2015-06-30>

    def cleanup(self):
        """delete all files and session folder"""
        self.mask_image = None
        self.images = {}
        self.ehooke = None
        try:
            rmtree(self.folder,ignore_errors=True)
        except:
            pass
        

    def setup(self):
        """creates session folder (add other setup stuff here)"""        
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)
        if not os.path.exists(self.data_folder):
            os.mkdir(self.data_folder)


    def process_data_files(self):
        """Sets self.images to value and mask lists from files in data folder
           Also updates parameters, if any parameter file is given
        """

        files_list = [ fil for fil in os.listdir(self.data_folder) \
                       if os.path.isfile(os.path.join(self.data_folder,fil)) ]
        
        if SESSION_PARAMS in files_list:
            self.set_parameters_file(os.path.join(self.data_folder,SESSION_PARAMS))

        self.images = {}
    
        if SESSION_MASKS in files_list:
            masks = open(os.path.join(self.data_folder,SESSION_MASKS)).readlines()
            for line in masks:
                files = line.split(':')
                if len(files)==1:
                    self.images[os.path.join(self.data_folder,files[0])]=None
                else:
                    self.images[os.path.join(self.data_folder,files[0])] = \
                                    os.path.join(self.data_folder,files[1].strip())
        else:
            for fil in files_list:
                if fil != SESSION_PARAMS and fil != SESSION_MASKS:
                    self.images[os.path.join(self.data_folder,fil)] = None
        

    def set_parameters_file(self, file_name):
        """sets and reloads parameters
           (image files in parameters will be overwritten upon session initialization)
        """
        
        self.params_file = file_name
        self.params.load_parameters(file_name)
        
    
    def start_ehooke(self):
        """Initiates the ehooke process and loads images

           if there is no fluorescence image specified, returns false and error message
           otherwise returns true,''

           if ehooke is not none does nothing and returns ok
        """        
        if self.ehooke is not None:
            return (True,'')

        self.process_data_files()
        if len(self.images)==0:
            return (False,'Cannot start eHooke with no value images.')

        self.ehooke = EHooke(self.params)
        self.ehooke.init_frames(self.images)
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
        
            

class SessionManager(object):
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

    def is_running(self,session_id):
        """return True if eHooke for that session has been created"""

        session = self.get_session(session_id)
        return session.ehooke is not None

    def start_session(self,session_id):
        """check data files, start eHooke on session, load data"""

        session = self.get_session(session_id)
        session.start_ehooke()
    
    
   
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
                                     IMAGES_TAG:str(session.images),                                     
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
        
    def save_archived_data(self,data_path,session_path):
        """Saves a zip file uploaded with a POST request, extracting all
           archived files to the current session data folder
        """

        boundary = self.headers.plisttext.split("=")[1]
        
        remainbytes = int(self.headers['content-length'])
        line = self.rfile.readline()
        remainbytes -= len(line)
        if not boundary in line:
            return (False, "Content NOT begin with boundary")
        line = self.rfile.readline()

        remainbytes -= len(line)
        fn = re.findall(r'filename="(.*)"', line)
        if len(fn)==0:
            return (False, "Can't find out file name...")            
        if session_path=='':
            return (False, "Invalid session id")
        fn = os.path.join(session_path, fn[0])            
        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)

        data_file = open(fn,'wb')
        preline = self.rfile.readline()
        remainbytes -= len(preline)
        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            if boundary in line:
                print fn,'\n',preline,'\n',line
                preline = preline[0:-1]
                if preline.endswith('\r'):
                    preline = preline[0:-1]
                data_file.write(preline)
                break  ## file ends here
            else:
                data_file.write(preline)
                preline = line

        data_file.close()

        zf = ZipFile(fn, "r") 
        zf.extractall(data_path)
        zf.close()
        os.unlink(fn)
        return (True, fn)
        

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
        elif url == URL_UPDATA:
            if session_manager.is_running(session_id):
                return(False, 'Cannot upload data to a running session')            
            data_path = session_manager.get_session_data_path(session_id)
            session_path = session_manager.get_session_path(session_id)
            result, msg = self.save_archived_data(data_path,session_path)
            if result:                
                session_manager.start_session(session_id)
            else:
                return (False, 'Failed to process data archive: '+msg)
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




session_manager=SessionManager()
"""Global variable to manage sessions.

   This is ugly but seems the best way to give the http handler class
   access to the session manager.
"""

    

if __name__ == '__main__':

    #For safety reasons, server is confined to local host
    #Change 'localhost' to '' to enable remote access
    #server = ThreadedHTTPServer(('localhost', 8081), Handler)
    server = HTTPServer(('localhost', 8081), Handler)    
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()
