









## Concrete Object Layer (C API)
- !!!!! ВАЖНО !!!!! While the functions described in this chapter carefully check the type of the objects which are passed in, many of them do not check for NULL being passed instead of a valid object. Allowing NULL to be passed in can cause memory access violations and immediate termination of the interpreter.
- https://docs.python.org/3/c-api/concrete.html
- https://docs.python.org/3/c-api/index.html

## Используемые ресурсы
- https://docs.python.org/3/library/codecs.html#standard-encodings
- wstring to wchar_t https://stackoverflow.com/questions/44985451/how-to-convert-wstring-to-wchar-t-c
- https://cpp.hotexamples.com/examples/-/-/PyUnicode_FromWideChar/cpp-pyunicode_fromwidechar-function-examples.html
- внутреннее устройство CPython http://onreader.mdl.ru/CPythonInternals/content/index.html#Preface
- https://stackoverflow.com/questions/5145394/how-to-get-the-actual-localized-folder-names
- для отображения юникода в коносли https://learn.microsoft.com/ru-ru/cpp/c-runtime-library/reference/setlocale-wsetlocale?view=msvc-170
- https://forum.sources.ru/index.php?showtopic=274112
- https://stackoverflow.com/questions/78270085/make-existing-instance-of-windows-explorer-navigate-to-specific-folder
- https://learn.microsoft.com/en-us/windows/win32/api/exdisp/nn-exdisp-ishellwindows
- https://learn.microsoft.com/en-us/previous-versions/windows/desktop/legacy/dd940376(v=vs.85)
- https://learn.microsoft.com/en-us/previous-versions/windows/desktop/legacy/bb773177(v=vs.85)?redirectedfrom=MSDN
- https://stackoverflow.com/questions/43815932/how-to-get-the-path-of-an-active-file-explorer-window-in-c-winapi/43821628#43821628
- https://stackoverflow.com/questions/43949747/return-a-list-of-all-files-from-the-selected-explorer-window-with-pywin32/43968304#43968304
- https://stackoverflow.com/questions/65064308/getting-the-sorting-order-of-a-folder-as-defined-in-windows-explorer
- тут о том, как написать свой извлекатель имён
  - https://stackoverflow.com/questions/65064308/getting-the-sorting-order-of-a-folder-as-defined-in-windows-explorer
  - https://stackoverflow.com/questions/71365499/how-to-get-a-complete-explorer-listing-related-to-a-file-used-to-launch-an-assoc
  - https://learn.microsoft.com/en-us/uwp/api/windows.applicationmodel.activation.fileactivatedeventargs.neighboringfilesquery?view=winrt-26100
- извлекатель аналогичного приложения на C# (но функция написана на C++)
  - https://github.com/riyasy/FlyPhotos/tree/main/Src/CLIWrapper
  - https://github.com/riyasy/FlyPhotos/blob/main/Src/CLIWrapper/ShellUtility.cpp
- если не работает вывод нелатинских символов в консоль https://cplusplus.com/forum/general/77234/

## Командная строка для C/C++ компилятора cl.exe (Visual Studio 2022) для компиляции С++ Console Project
- /permissive- /ifcOutput "x64\Release\" /GS /GL /W3 /Gy /Zc:wchar_t /Zi /Gm- /O2 /sdl /Fd"x64\Release\vc143.pdb" /Zc:inline /fp:precise /D "NDEBUG" /D "_CONSOLE" /D "_UNICODE" /D "UNICODE" /errorReport:prompt /WX- /Zc:forScope /Gd /Oi /MD /FC /Fa"x64\Release\" /EHsc /nologo /Fo"x64\Release\" /Fp"x64\Release\ConsoleApplication1.pch" /diagnostics:column 
