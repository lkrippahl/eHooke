@mainpage eHooke: Microscopy Image Processing

Code documentation
------------------

This document covers the eHooke code. For user instructions consult the user manual.

Main points:
------------

eHooke is run running the ehserver module. This creates a http server on port
8081, by default accessible only on the machine where it is running.

The ehserver module creates a ehserver.SessionManager object that manages all sessions.

Each Session object creates an independent process with a ehooke.EHooke object using the function ehooke.run_ehooke.

Each session has a unique folder in the sessions folder. Each session receives all data and additional files
in a zip file uploaded through the http interface. The zip is extracted to the data folder in the session folder.

The html folder has the templates for the pages, image placeholders and javascript files.

Modules
-------

- ehserver: http server for managing eHooke sessions
- htmlconstants: constants for handling the html interface 
- ehooke: encapsulates all computation
- params: classes for defining parameters objects
- preprocessor: loads images and applies preprocessing options (e.g. noise reduction; not implemented)
- frames: handles value images and (optionally) their associated mask images (e.g. fluorescence and phase files)
- masks: mask computations
- (TODO)
