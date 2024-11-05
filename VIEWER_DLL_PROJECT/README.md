

# Справка
- **!** `.pyd`-файлы это обёрнутые питоном виндовые `.dll`-файлы
- **!** Для формирования pyd-файла из исходного .сс-файла нужно воспользоваться командой `python setup.py build_ext --inplace`. setup.py использует модуль **distutils, который снесли окончательно в Python 3.12** https://stackoverflow.com/questions/77247893/modulenotfounderror-no-module-named-distutils-in-python-3-12
- **!** Если не хочется набирать в консоли команду описанную выше, то достаточно запустить из проводника Windows файл `prepare_pyd.py` 
- **!** Полученный в результате файл `viewer_dll.pyd` может импортироваться как python-модуль и дарует нам на уровне модуля функцию `viewer_dll.getFileListFromExplorerWindow()`, которая возвращает список файлов из активного окна проводника Windows. Если полные пути до файлов не нужны, то функцию можно вызвать так `viewer_dll.getFileListFromExplorerWindow(fullpaths=False)`
- **!** `viewer_dll.getFileListFromExplorerWindow` пока не грабит файлы с рабочего стола Windows, функция вернёт пустой список в таком случае
- **!** Параметры компиляции описываются в файле setup.py, документация доступна через Python:
```python
from distutils.core import Extension
print(help(Extension))
```
- **!** Для доступности модуля viewer_dll в приложении Krumassan Image Viewer, нужно скопировать файл `viewer_dll.pyd` в ту же папку, где лежит файл `viewer.pyw`
- **!** Если .cc-файл нужно изменить, то изменения вносятся, а затем заново выполняется скрипт `prepare_pyd.py`, чтобы сгенерировать обновлённый .pyd-файл

# Былина о ноябрьском внедрении в Python кода на C++, излагается в хронологическом порядке
- Компиляция .cc-файла происходила за счёт команды `setup.py build_ext --inplace`. На компе была установлена Visual Studio 2022, автоматически был найден компилятор, которым пользовалась команда, данные о компиляторе: *оптимизирующий компилятор Microsoft (R) C/C++ версии 19.34.31937 для x64*. Содержание встроенного хэлпа приводится в файле cl.help.txt
- Сам setup-файл был вытащен из рандомного python-модуля, который зависел от сборки на `.c` и `.cc файлов
- В коде пришлось задать целевую платформу `#define _AMD64_`
- Так как я не врубил определения отвечающие за юникод, пришлось заменять `L` у строк на си-шное приведение типа `(LPSTR)` или `(LPCSTR)`, а `g_szItem` пришлось добавлять в динамический массив через прокладку типа `wstring`, иначе оно отказывалось собираться
- TCHAR пришлось заменять на WCHAR
- Пришлось явно прописывать в исходном файле либы для линкера через pragma, хотя по идее либы должны были быть прописаны в самих хэадерах. Без этого отказывалось в линковке
- Написал код, который формирует Python-строки и засовывает их в Python-список и выдаёт наружу
- Забеспокоился о том, будут ли нормально поступать нелатинские символы и возился с превращением wstring в Python-объект строки
- Хотел отлаживать напрямую в Image Viewer заменив тело функции `main`, но в итоге сообразил скрипт, который сразу после своего запуска ставит таймер на три секунды, во время которого надо успеть кликнуть по любому окну проводника
- Убрал баг с помощью memset, когда от прыдудущей строки оставались данные, которые пролезали в конец текущей строки
- После тестов отметил, что в Python приходят строки с иероглифами вместо строк с названиями файлов, в итоге пришлось создавать строки не в С++ коде, а уже в Python, а данные передавать через массивы байтов с помощью функции `PyByteArray_FromStringAndSize` 
- После того как справился с предыдущей проблемой понял, что в `g_szItem` совсем не юникод, хоть и это массив символов wide char. Там были символы под кодовую страницу cp1251, а не юникод. Это стало понятно, когда в названии элемента в папке было "ç", но в итоге выводилось "c" без нижнего хвостика. Непонятно было что делать, и я решил весь код откомпилировать в консольном приложении на С++. Там всё заработало нормально, и в консоли даже отображалась "ç". Изучая интернет, понял, что в настройках проекта на С++ указан набор символов Unicode. Отключив и включив юникодный набор символов я выловил параметры командной строки компилятора, которые отвечали за этот самый юникод, собственно вот они:
`/D "_UNICODE" /D "UNICODE"`
  - зашёл в студию и в свойствах проекта начал искать инфу про charset
    - на вкладке **Configuration Properties** -> **Advanced** увидел параметр **Character Set**
    - играясь с этим параметром стал мониторить что происходит на вкладке **Configuration Properties** -> **С/C++** -> **Command Line**
    - таким образом уяснил какие именно параметры компилятора отвечают за опцию **«Use Unicode Character Set»**
- До того как понять вышеописанную тему, прочитал доки на все функции, которые принимают участие в формировании строки, даже делал распечатку кода каждого символа из массива `g_szItem`, чтобы проверить, что там действительно одинаковые числа для "ç" для "c"
- Попробовал прописать эти параметры в `setup.py`, но эффекта не получил. Вызвал встроенный help компилятора, где было объяснено, что они обозначают следующие соврешенно обыкновенные команды, которые я и вбил в исходный код:
```cpp
    #define _UNICODE
    #define UNICODE
```
- В итоге этих объвлений код стал корректно обрабатывать юникод-символы, и я отказался от `PyByteArray_FromStringAndSize` и вернулся к `PyUnicode_FromWideChar`. К тому же пришлось откатывать вышеописанные замены.
- На всякий случай заменил `MAX_PATH`, который всего 260, на другую константу, которая уже 2048.

## 2 главных статьи, с которых надо начинать 
- https://realpython.com/build-python-c-extension-module/
- https://docs.python.org/3/extending/extending.html

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
- https://stackoverflow.com/questions/69209713/converting-a-tchar-to-wstring
- https://stackoverflow.com/questions/25715127/c-using-stdstring-stdwstring-as-a-buffer

## Командная строка для C/C++ компилятора cl.exe (Visual Studio 2022) для компиляции С++ Console Project
- /permissive- /ifcOutput "x64\Release\" /GS /GL /W3 /Gy /Zc:wchar_t /Zi /Gm- /O2 /sdl /Fd"x64\Release\vc143.pdb" /Zc:inline /fp:precise /D "NDEBUG" /D "_CONSOLE" /D "_UNICODE" /D "UNICODE" /errorReport:prompt /WX- /Zc:forScope /Gd /Oi /MD /FC /Fa"x64\Release\" /EHsc /nologo /Fo"x64\Release\" /Fp"x64\Release\ConsoleApplication1.pch" /diagnostics:column 
