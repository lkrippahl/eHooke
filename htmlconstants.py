"""Constants and utilities for rendering eHooke html pages
"""
import string

SESSION_FOLDER='sessions'
"""str: base folder for sessions

   This folder should exist when executing the server.
"""

SERVER_URL='http://127.0.0.1:8081'
"""str: url for the server"""

SESSION_ID_TAG='[SESSIONID]'
"""str: id tag to be replaced by session id in html source"""
SESSION_NAME_TAG='[SESSIONNAME]'
"""str: id tag to be replaced by session name in html source"""
SESSION_DESC_TAG='[SESSIONDESC]'
"""str: id tag to be replaced by session description in html source"""
FLUOR_TAG = '[FLUORFILE]'
"""str: id tag to be replaced by fluorescence file name in html source"""
PHASE_TAG = '[PHASEFILE]'
"""str: id tag to be replaced by phase file name in html source"""
PARAMS_TAG = '[PARAMSFILE]'
"""str: id tag to be replaced by parameters file name in html source"""
FORM_TAG = '[FORM]'
"""str: id tag to be replaced by a <form> ... </form> block in html source"""

HTML_FOLDER_TAG='[HTML]'
"""str: id tag to be replaced by the html folder"""
SESSION_FOLDER_TAG='[SESSION]'
"""str: id tag to be replaced by the current session folder"""

SESSION_NAME = 'session_name'
"""str: field with session name in new session post requests"""
SESSION_DESCRIPTION = 'session_description'
"""str: field with session description in new session post requests"""


NEW_SESSION='/newsession'
"""str: url path indicating a new session request"""
UPLOAD_FILE='/upload'
"""str: url path for the upload page for a session indicated by an ?ID=id param"""

HTML_FOLDER='html/'
"""str: path for html, css, js files"""

DEFAULT_MASK=HTML_FOLDER+'default_mask.png'
"""str: filename for the image when mask not computed"""

HTML_UPLOAD=HTML_FOLDER+'upload.html'
"""str: html file for the upload page"""
HTML_SESSION = HTML_FOLDER+'session.html'
"""str: html file for the session template page"""
HTML_MASK = HTML_FOLDER+'mask.html'
"""str: html file for the mask template page"""
HTML_INDEX=HTML_FOLDER+'index.html'
"""str: html file for the main page"""

URL_START = '/start'
"""str: url for starting ehooke"""
URL_UPPHASE = '/upphase'
"""str: url for uploading phase image (POST)"""
URL_UPFLUOR = '/upfluor'
"""str: url for uploading fluorescence image (POST)"""
URL_UPPARAMS = '/upparams'
"""str: url for uploading parameters file (POST)"""
URLS_UPLOAD = [URL_UPPHASE, URL_UPFLUOR, URL_UPPARAMS]
"""list: urls for uploading"""
URL_MASK_PARAMETERS = '/maskparameters'
"""str: url for updating mask parameters from form(POST)"""


URL_SESSION_PAGE='/session'
"""str: url path for the page of a session indicated by an ?ID=id param"""
URL_MASK_PAGE = '/mask'
"""str: url for the mask page"""
URL_MASK_IMAGE = '/maskimage'
"""str: url for requesting the current mask image (get)"""


def attributes_to_form(name, action,obj,attributes,
                       drop_lists={}, submit = 'Submit'):
    """returns a string with an html form for all attributes listed
    name is the name of the form
    action is the action url for the form
    obj is any object    
    attributes is a list of tuples for the attributes to include in form
        (attribute name, form label)
    drop_lists is a dictionary with attribute_name and list of strings for
      options"""
    
    res = '<form name="{0}" action="{1}" method="post" enctype="multipart/form-data">\n'.format(name,action)
    for a in attributes:
        at_name,at_label = a
        attr = getattr(obj,at_name)
        if at_name in drop_lists.keys():
            res = res + '<p><label>{0}:</label> <select form="{1}" name="{2}">\n'.format(at_label,name,at_name)
            for option in drop_lists[at_name]:
                res = res + '<option value="'+option+'"'
                print attr,option
                if option == attr:
                    res = res + ' selected'
                res = res + '>'+option+'</option>\n'
            res = res + '</select>\n'
        elif type(attr) is bool:
            res = res + '<p><label>{0}:</label><input name="{1}" type="checkbox" value="{2}"></p>\n'.format(at_label,at_name,attr)
        else:
            res = res + '<p><label>{0}:</label><input name="{1}" type="text" value="{2}"></p>\n'.format(at_label,at_name,attr)

    res = res + '<input type="submit" value="{0}">\n</form>\n'.format(submit)
    return res

def form_to_attributes(form_data,attributes,obj):
    """updates the object attributes with the form data
    form data is a dictionary with attribute names and values
    attributes is a list of tuples for all exported attributes of the class (name, label)
    obj is the object to update.
    """

    for a in attributes:
        at_name = a[0]
        if at_name in form_data.keys():
            attr = getattr(obj,at_name)
            if type(attr) is bool:
                attr = bool(form_data[at_name])
            elif type(attr) is int:
                attr = int(form_data[at_name])
            elif type(attr) is float:
                attr = float(form_data[at_name])
            else:
                attr = form_data[at_name]               
            

def process_html(html_source,replacements=None):
    """reads the html source file and replaces tags
       replacements is a dictionary with tag:text_to_replace
    """
    fil = open(html_source)
    source = fil.read()
    fil.close()
    source=string.replace(source,HTML_FOLDER_TAG,HTML_FOLDER)        

    if replacements is not None:
        for key in replacements.keys():            
            source=string.replace(source,key,replacements[key])        
    return source
