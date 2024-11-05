


#define _AMD64_
#define _UNICODE
#define UNICODE

#include <windows.h>
// #include <windowsx.h>
#include <winuser.h>
// #include <WinDef.h>

#include <time.h>
#include <cstring>
#include <vector>
#include <string>
#include <iostream>


#include <ole2.h>
#include <shlwapi.h>
#include <shlobj.h>
#include <exdisp.h>

#include <Python.h>

#pragma comment(lib, "user32.lib")
#pragma comment(lib, "Ole32.lib")
#pragma comment(lib, "Shlwapi.lib")

using namespace std;

#if PY_MAJOR_VERSION != 3
#error "This library only supports Python 3"
#endif

#define KRUMASSAN_IMAGE_VIEWER_MAX_PATH 2048 //replacing MAX_PATH which is too small: 260


HRESULT GetFileListFromExplorerWindow(vector<wstring>& arr, int fullpaths)
{
    WCHAR g_szItem[KRUMASSAN_IMAGE_VIEWER_MAX_PATH];
    g_szItem[0] = TEXT('\0');

    int SHGDN_CONST_VALUE = (fullpaths > 0) ? SHGDN_FORPARSING : SHGDN_NORMAL;

    // Get the handle to the foreground window (the currently active window).
    HWND hwndFind = GetForegroundWindow();

    // Try to find the active tab window in the foreground window.
    // First, look for "ShellTabWindowClass", then "TabWindowClass".
    HWND hwndActiveTab = FindWindowEx(hwndFind, nullptr, L"ShellTabWindowClass", nullptr);
    if (hwndActiveTab == nullptr)
    {
        // cout << "ShellTabWindowClass not found, trying find TabWindowClass..." << endl;
        hwndActiveTab = FindWindowEx(hwndFind, nullptr, L"TabWindowClass", nullptr);
    }

    // If no active tab was found, return an error code.
    if (hwndActiveTab == nullptr)
    {
        // cout << "no active tab found!!!" << endl;
        return E_FAIL; // No active tab found
    }

    // cout << "active tab found!!!" << endl;

    // Create an instance of IShellWindows to enumerate all open shell windows.
    IShellWindows* psw = nullptr;

    HRESULT hr = CoInitialize(NULL); //this should be called first or we will fail at ShellWindows instance creation
    if (FAILED(hr))
    {
        // cout << "failed to CoInitialize" << endl;
        return hr; // Failed to CoInitialize
    }

    hr = CoCreateInstance(CLSID_ShellWindows, nullptr, CLSCTX_ALL, IID_IShellWindows, (void**)&psw);
    if (FAILED(hr))
    {
        // cout << "failed to create ShellWindows instance" << endl;
        return hr; // Failed to create ShellWindows instance
    }

    VARIANT v;
    V_VT(&v) = VT_I4;
    IDispatch* pdisp = nullptr;

    // Iterate through all shell windows to find the one matching the foreground window.
    for (V_I4(&v) = 0; psw->Item(v, &pdisp) == S_OK; V_I4(&v)++)
    {
        // cout << "iteration started" << endl;
        IWebBrowserApp* pwba = nullptr;
        hr = pdisp->QueryInterface(IID_IWebBrowserApp, (void**)&pwba);
        pdisp->Release(); // Release IDispatch as it's no longer needed.
        if (FAILED(hr))
        {
            continue; // Skip to the next shell window if QueryInterface fails.
        }

        // Get the window handle of the current IWebBrowserApp.
        HWND hwndWBA;
        hr = pwba->get_HWND((LONG_PTR*)&hwndWBA);
        if (FAILED(hr) || hwndWBA != hwndFind)
        {
            pwba->Release(); // Release IWebBrowserApp if not the target window.
            continue; // Skip to the next shell window.
        }

        // Query for the IServiceProvider interface.
        IServiceProvider* psp = nullptr;
        hr = pwba->QueryInterface(IID_IServiceProvider, (void**)&psp);
        pwba->Release(); // Release IWebBrowserApp as it's no longer needed.
        if (FAILED(hr))
        {
            continue; // Skip to the next shell window if IServiceProvider query fails.
        }

        // Use IServiceProvider to get the IShellBrowser interface.
        IShellBrowser* psb = nullptr;
        hr = psp->QueryService(SID_STopLevelBrowser, IID_IShellBrowser, (void**)&psb);
        psp->Release(); // Release IServiceProvider as it's no longer needed.
        if (FAILED(hr))
        {
            continue; // Skip to the next shell window if IShellBrowser query fails.
        }

        // Get the window handle of the shell browser.
        HWND hwndShellBrowser;
        hr = psb->GetWindow(&hwndShellBrowser);
        if (FAILED(hr) || hwndShellBrowser != hwndActiveTab)
        {
            psb->Release(); // Release IShellBrowser if not the active tab.
            continue; // Skip to the next shell window.
        }

        // Retrieve the active shell view from the shell browser.
        IShellView* psv = nullptr;
        hr = psb->QueryActiveShellView(&psv);
        psb->Release(); // Release IShellBrowser as it's no longer needed.
        if (FAILED(hr))
        {
            continue; // Skip to the next shell window if IShellView query fails.
        }

        // Query for the IFolderView interface from the active shell view.
        IFolderView* pfv = nullptr;
        hr = psv->QueryInterface(IID_IFolderView, (void**)&pfv);
        psv->Release(); // Release IShellView as it's no longer needed.
        if (FAILED(hr))
        {
            continue; // Skip to the next shell window if IFolderView query fails.
        }

        // Get the IShellFolder interface from the folder view.
        IShellFolder* psf = nullptr;
        hr = pfv->GetFolder(IID_IShellFolder, (void**)&psf);
        if (FAILED(hr))
        {
            pfv->Release(); // Release IFolderView if IShellFolder query fails.
            continue; // Skip to the next shell window.
        }

        // Enumerate the items in the folder view.
        IEnumIDList* pEnum = nullptr;
        hr = pfv->Items(SVGIO_FLAG_VIEWORDER, IID_IEnumIDList, (LPVOID*)&pEnum);
        pfv->Release(); // Release IFolderView as it's no longer needed.
        if (FAILED(hr))
        {
            psf->Release(); // Release IShellFolder if enumeration fails.
            continue; // Skip to the next shell window.
        }

        LPITEMIDLIST pidl;
        ULONG fetched = 0;
        STRRET str;

        // Iterate through the items and get their display names.
        while (pEnum->Next(1, &pidl, &fetched) == S_OK && fetched)
        {
            hr = psf->GetDisplayNameOf(pidl, SHGDN_CONST_VALUE, &str);
            if (SUCCEEDED(hr))
            {
                memset( g_szItem, 0, sizeof(g_szItem) );
                // Convert STRRET to a string and add it to the output array.
                StrRetToBuf(&str, pidl, g_szItem, KRUMASSAN_IMAGE_VIEWER_MAX_PATH);
                arr.push_back(g_szItem);
            }
            CoTaskMemFree(pidl); // Free the PIDL after processing.
        }

        pEnum->Release(); // Release the item enumerator.
        psf->Release(); // Release IShellFolder.
        break; // Exit the loop since we've found the active tab.
    }

    // cout << "end of function reached!" << endl;

    psw->Release(); // Release IShellWindows.
    return hr; // Return the result.
}


#ifdef __cplusplus
extern "C" {
#endif

static PyObject* getFileListFromExplorerWindow(PyObject* self, PyObject *args, PyObject *keywds) {
    vector<wstring> out_array;

    int fullpaths = 1;
    static char *kwlist[] = {"fullpaths", NULL};

    PyObject *empty = PyTuple_New(0);

    if (!PyArg_ParseTupleAndKeywords(empty, keywds, "|p", kwlist, &fullpaths)){
        Py_XDECREF(empty);
        return NULL;
    }

    // cout << fullpaths << endl;

    HRESULT hr = GetFileListFromExplorerWindow(out_array, fullpaths);

    PyObject *list = PyList_New(0);
    if (SUCCEEDED(hr))
    {
        for (int i = 0; i < out_array.size(); ++i)
        {
            wstring temp = out_array[i];
            const wchar_t* wcs = &temp[0];
            PyObject *item = PyUnicode_FromWideChar(wcs, wcslen(wcs));
            PyList_Append(list, item);
        };
    };

    Py_XDECREF(empty);
    return list;
}

static PyMethodDef KIVExtensionMethods[] =
{
    {"getFileListFromExplorerWindow", (PyCFunction)getFileListFromExplorerWindow, METH_VARARGS | METH_KEYWORDS, "Gets files list from Explorer window"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef KrumassanImageViewerExtensionModule = {
   PyModuleDef_HEAD_INIT,
   "KrumassanImageViewerExtensionModule",
   NULL, /* TODO: add docs */
   -1,
   KIVExtensionMethods
};

PyMODINIT_FUNC PyInit_viewer_dll(void)
{
    PyObject* m;

    m = PyModule_Create(&KrumassanImageViewerExtensionModule);
    if (m == NULL)
        return NULL;

    return m;
}

#ifdef __cplusplus
}
#endif
