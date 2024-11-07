import os
import sys
import win32con
import win32api
import win32gui
import win32com.client
import pythoncom
from win32com.shell import shell, shellcon



# (7 ноя 24) выдаёт имена файлов в папке, но порядок не соблюдает совсем



# Get list of paths from given Explorer window or from all Explorer windows.
def get_explorer_files( hwndOfExplorer = 0, selectedOnly = False ):
    paths = []

    # Create instance of IShellWindows (I couldn't find a constant in pywin32)
    CLSID_IShellWindows = "{9BA05972-F6A8-11CF-A442-00A0C90A8F39}"
    shellwindows = win32com.client.Dispatch(CLSID_IShellWindows)

    # Loop over all currently open Explorer windows
    for window in shellwindows:
        # Skip windows we are not interested in.
        if hwndOfExplorer != 0 and hwndOfExplorer != window.HWnd:
            continue

        # Get IServiceProvider interface
        sp = window._oleobj_.QueryInterface( pythoncom.IID_IServiceProvider )

        # Query the IServiceProvider for IShellBrowser
        shBrowser = sp.QueryService( shell.SID_STopLevelBrowser, shell.IID_IShellBrowser )

        # Get the active IShellView object
        shView = shBrowser.QueryActiveShellView()

        # Get an IDataObject that contains the items of the view (either only selected or all). 
        aspect = shellcon.SVGIO_SELECTION if selectedOnly else shellcon.SVGIO_ALLVIEW
        items = shView.GetItemObject( aspect, pythoncom.IID_IDataObject )

        # Get the paths in drag-n-drop clipboard format. We don't actually use 
        # the clipboard, but this format makes it easy to extract the file paths.
        # Use CFSTR_SHELLIDLIST instead of CF_HDROP if you want to get ITEMIDLIST 
        # (aka PIDL) format, but you can't use the simple DragQueryFileW() API then. 
        data = items.GetData(( win32con.CF_HDROP, None, pythoncom.DVASPECT_CONTENT, -1, pythoncom.TYMED_HGLOBAL ))

        # # Use drag-n-drop API to extract the individual paths.
        numPaths = shell.DragQueryFileW( data.data_handle, -1 )
        paths.extend([
            shell.DragQueryFileW( data.data_handle, i ) \
                for i in range( numPaths )
        ])

        if hwndOfExplorer != 0:
            break

    return paths

try:
    # Use hwnd value of 0 to list files of ALL explorer windows...
    hwnd = 0  
    # ... or restrict to given window:
    #hwnd = win32gui.GetForegroundWindow()
    selectedOnly = False
    print( *get_explorer_files( hwnd, selectedOnly ), sep="\n" )
except Exception as e:
    print( "ERROR: ", e )
