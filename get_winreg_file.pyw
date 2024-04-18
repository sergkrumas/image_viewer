

import sys, os

import ctypes


data = r"""Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\Applications\viewer.pyw]

[HKEY_CLASSES_ROOT\Applications\viewer.pyw\DefaultIcon]
@="%s\\image_viewer.ico"

[HKEY_CLASSES_ROOT\Applications\viewer.pyw\shell]

[HKEY_CLASSES_ROOT\Applications\viewer.pyw\shell\open]
@="View"
"FriendlyAppName"="Krumassan Image Viewer"

[HKEY_CLASSES_ROOT\Applications\viewer.pyw\shell\open\command]
@="%s \"%s\\viewer.pyw\" \"%%1\""

[HKEY_CLASSES_ROOT\Applications\viewer.pyw\SupportedTypes]
".jpg"=""
".jpeg"=""
".bmp"=""
".gif"=""
".png"=""
".tif"=""
".tiff"=""
".webp"=""
".jfif"=""
".svg"=""
".svgz"=""
".tga"=""




[HKEY_CLASSES_ROOT\.board]
@="KrumassanImageViewerBoard"

[HKEY_CLASSES_ROOT\KrumassanImageViewerBoard]
@="Board File (Krumassan Image Viewer)"

[HKEY_CLASSES_ROOT\KrumassanImageViewerBoard\DefaultIcon]
@="%s\\image_viewer_lite.ico\""

[HKEY_CLASSES_ROOT\KrumassanImageViewerBoard\shell]

[HKEY_CLASSES_ROOT\KrumassanImageViewerBoard\shell\open]
@="Open board"

[HKEY_CLASSES_ROOT\KrumassanImageViewerBoard\shell\open\command]
@="%s \"%s\\viewer.pyw\" -board \"%%1\""


"""




def main():
    global data

    PYTHON_EXECUTABLE_DIR = os.path.dirname(sys.executable)
    PYTHON_EXECUTABLE_PATH = os.path.join(PYTHON_EXECUTABLE_DIR, "pythonw.exe").replace("\\", "\\\\")
    APP_FOLDER = os.path.dirname(__file__).replace("\\", "\\\\")

    filepath = os.path.join(os.path.dirname(__file__), "register_image_viewer.reg")

    with open(filepath, "w+", encoding="utf8") as file:
        data = data % (
            APP_FOLDER,
            PYTHON_EXECUTABLE_PATH, APP_FOLDER,
            APP_FOLDER,
            PYTHON_EXECUTABLE_PATH, APP_FOLDER
        )
        file.write(data)

    MessageBox = ctypes.windll.user32.MessageBoxW
    MessageBox(None, 'Your .reg-file has been generated and now located in \n\n%s\n\nNow double click on the reg-file to register viewer.pyw as Windows Application' % filepath, 'Done!', 0)


if __name__ == '__main__':
    main()
