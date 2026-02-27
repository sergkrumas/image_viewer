First things first, you need to download 64-bit version of Python [from here](https://www.python.org/downloads/) and intall it.

IMPORTANT: As installation wizard showed up, you need to activate checkbox "Add Python 3.XX to PATH", otherwise there will be problems with dependencies installation and it'll take you knowledge and command line skills to tackle and cope with that on your own.

![](docs/python_install.png)

After Python installation success, you need to install all dependencies by double-cliking on **install_dependencies.bat** in Windows Explorer. Once you double-click on file, console window shoes up and you could watch the ongoing progress. As all dependencies downloaded and installed, console window automatically closes and it means that Krumassan Image Viewer is ready to run.

### Registration of VIEWER.PYW as application for Windows Explorer

We need to touch windows registry in order to achieve integration with Windows Explorer.

Follow these steps:
- 1) If you don't like default icons, it's high time to replace it, otherwise just skip that step. When replacing icons with your own ones strictly preserve original .ico-files  names otherwise application couldn't find these. You can extract the canonical Picasa Photo Viewer icon as I did on my computer. I would love to include a Picasa Photo Viewer icon in that open source clone, but I'm not allowed to do so under the terms of the GNU GPL license. The Icon with filename `image_viewer.ico` shows up for every image file in Windows Explorer that has been associated with application, the other icon with filename `image_viewer_lite.ico` shows up on windows taskbar as app icon
- 2) Go to the app folder, then double-click on the file `get_winreg_file.pyw`. As a result the message box shows up informing that reg-file generated and placed to the app folder. Double-click on generated reg-file and then confirm registry operation (this may require to run as administrator to be succeced)

After these steps you could see the app in Windows Explorer context menu for images files: in the menu item "Open with...", and in the opened submenu the program will be called **Krumassan Image Viewer**. From now on you can manually associate the app with images files. Unfortunatly, there's no way to automatically set all these associations due to the Windows security measures taken. Fortunatly, in this repository, in folder **test** you can find all files with common image extensions to set associations manually.

