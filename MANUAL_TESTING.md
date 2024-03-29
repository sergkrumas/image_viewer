# Программа рукопашного тестирования Image Viewer перед релизом
Ниже представлена инфа для проверки программы перед релизом, которого ещё не было. Здесь все очень сумбурно описано и я боюсь, что контекст некоторых моментов недостаточно раскрыт для понимания со стороны. Поэтому, что есть, то есть - вас предупредили.

- общее
    - вьювер должен нормально открываться на всех мониторах в системе
    - должны работать красные кнопки в углах вверху
    - по центру должен выводиться информационный лейбл
        - надо прятать этот лейбл, если перелеснули на другую картинку
    - система устранения запущенных копий программы через сокеты
    - появление картинки после загрузки папки
        - картинка должна позиционироваться по центру и появляться через анимацию увеличения при включённых анимационых эффектах
    - предувеличение или предуменьшение картинок, чтобы пони поместились в окне приложения
    - выводить сообщения, если
        - в избранном нет ни одного файла при переключении на просмотр
        - нет ни одной папки кроме избранного

- юзабилити
    - при повороте не должно случиться такого, что картинка полностью вывалится из вида.
        - такое может получится, если очень сильно приблизил картинку и повернул её
              INFO: Можно чуть уменьшить по габаритам прямоугольник окна и проверять не пересекается ли он с прямоугольником изображения. И если да, То надо будет как-то втянуть картинку ближе к центру. Наверное, нужно сделать это так - перенести картинку на разницу между ближайшим из углов и центром окна
    - когда упрёшься в конец или в начало списка, то надо принудительно показывать панель управления
    - в библиотеке количество колонок должно динамически изменятся при изменени размера окна
    - превьюшки во вьювере должны создаваться только после показа главной картинки
    - превьюшка не должна выделяться, если я кликаю по управляющим кнопкам в области пересечения превьюшки и управляющей кнопки

- наставления
    - код, пишущий в файлы сессии и избранное, не должен содержать циклов или вызовов функций внутри контекстного менеджера файла, иначе при любом краше внутри контекстного менеджа старые данные будут затёрты, а новые не смогут быть записаны из-за всё того же краша.

- анимационные эффекты
    - easeOut при закрытии программы
    - easeOut при открытии программы
    - проверить все эффекты найдя их в коде программы через функцию `animate_property`

- эффективность
    - при обновлении папок надо брать уже имеющиеся превьюшки из имеющегося списка, а не просто его отчищать
        - проверять изменился ли файл надо по хэшу или пути!
        - это пригодится при обновлении больших папок

- функционал и проверка на баги
    - при потере фокуса окном панель управления может залипать на одном уровне прозрачности и не отлипать обратно
    - при переключении из полноэкранного режима в оконный на странице библиотеки неправильно работает прокрутка списка папок в левом столбце
    - прога не должна выводить ошибок при выделении нескольких картинок в Проводнике и последующем нажатии Enter
    - максимально приближаться ко краям и углам картинки. Не должно быть отскока
    - анимированные картинки должны нормально отрабатывать переход между оконным и полноэкранными режимами
    - повороты картинки на фиксированные значения
        - повороты должны работать на анимированном контенте
    - миниатюрки для изображения
        - работает отдельный тред для создания
        - отрисовка
            - отражение миниатюрок в нижней панели
        - смещение миниатюр при перелистывании такое, что выбранная миниатюрка выбранной картинки была по центру
        - при клике на миниатюрку картинки она должна быть выбрана
        - всё должно правильно работать на всех мониторах
    - причина краша обязательно выводится в файл
    - прога должна пытаться открыть неоткрываемый файл через попытку его конвертации средствами PIL
    - не должно быть проблем со скейлом при переходе из библиотеки в просмоторщик
    - при перемещении картинки мышкой (pannig) нельзя чтобы курсор определял прозрачность панели миниатюр
    - при масштабировании картинок через клаву тоже должно отображаться текущее значение масштаба
    - если курсор мыши за пределами картинки, то картинка должна зумиться относительно ЦЕНТРА ОКНА
    - под прозрачными png должен рисоваться шахматный фон, иначе прозрачные области будут прокликиваться насквозь и окна других приложений станут активным
        - это косяк не выставленного специального режима отрисовки, благодаря которому альфа окна не должна быть испорчена альфой картинки
    - удаление из избранного последнего файла не должно крашить прогу
    - у красных угловых верхних кнопок курсор должен меняться на указательный палец
    - должны читаться все заявленные форматы
    - программа должна без сбоя принимать запросы на открытие файлов через несколько часов после запуска этой программы
    - на анимированном контенте как и на статическом должны отрисовываться как ТРЕТИ так и ЦЕНТР ИЗОБРАЖЕНИЯ
    - трети должны вращаться вместе с изображением
    - в случае фейла при чтении файла должно появляться сообщение "невозможно отобразить" вместе с питоновским трейсбэком
    - если удаляется папка, то нужно остановить поток, который делает ей превьюшки, если он работает
    - баг: при удалении большого числа папок из библиотеки на странице библиотеки отключается скролл, практически не работает
    - введение id-шников для таймера анимациии, чтобы при наличии таймера по текущему
        - id была вызвана завершающая фунция и не нужно было плодить кучу таймеров и держать их постоянно работающими
            БАГ РЕШЁН ЗА СЧЁТ БЛОКИРОВКИ ФУНКЦИЙ на время анимации
            [ Комментарий от: Пятница, 22 сентябрь 2023 21:06:23 | лол, а ведь надо было сразу вводить id-шники, ведь без них оказалось никак, ввёл эти айдишники только в сентябре]
    - когда окно настроек открыто надо менять курсор
    - фотки с фотика должны грузится с правильной ориентацией
    - баг: масштаб анимированных объектов начинает глючить после того как даблкликом переводишь его несколько раз туда-сюда обратно
    - сообщения в случае ненайденной картинки должны выводится в нормальном масштабе, а не в том масштабе, который был выставлен у удалённой картинки
    - центральный лейбл должен исчезать когда идёт перелистывание на другую картинку
    - библиотека (страница)
        - элементы из левой части библиотеки должны быть кликабельными
        - при листании папок в библиотеке не должны выставляться картинки в просмоторщике - это тормозит листание
        - при удалении картинки из избранного или из списка нужно обновлять колонки для правой части библиотеки
        - проверить случай когда папка с избранным будет пустая и на неё произойдёт переключение
        - должны работать стрелки вверх и вниз для переключения между папками в библиотеке
        - на странице библиотеки мышка не должна скейлить или перемещать картинку, что была на вьювере, и курсор не должен колбасится
    - нижняя панель упраления с кнопками и миниатюрками
        - должна реагировать на изменение главного окна - т.е, адаптироваться по размеру и центрироваться заново
        - должна реагировать на приближение мышки
    - НЕ НАДО ПРОВЕРЯТЬ: сочетания должны работать независимо от языка клавиатуры, для этого надо работать со сканкодами
    - внизу в области миниатюр мышка не реагирует на превьюшки на странице библиотеки (потому что там находится панель управления и она скрыта)
    - проверять фичу для прятания окна в трей при закрытии
    - клавиша esc должна закрывать аппликуху (или прятать в трей - в зависимости от настроек)
    - перемещать картинку можно не только с помощью стрелок, но и с помощью WASD
        - работает вместе с модификатором Shift
    - взаимодействие с картинкой
        - перемещение картинки через левую кнопку мыши (panning)
        - увеличение-уменьшение картинки через колесо мыши (zooming)
            - масштабирование и перемещение главной картинки в зависимости от положения курсора
                - наименьший масштаб - 1%
                - максимальный масштаб 10 000%
        - даблклик по картинке, которая утащена из центра и не в нативном масштабе, сразу летит в центр и масштаб её сбрасывается.
            Если картинка уже в центре, то она увеличивается до размеров, чтобы занимать вообще всю доступную площадь минус площадь панели и миниатюрами
    - управление воспроизведением анимированной картинки
        - вместо кликабельного прогресс-бара используется колесо мыши + зажатая левая кнопка мыши
        - на пробел воспроизведение и оставновка
        - задать скорость - Shift+Ctrl+колесо мыши
        - поддержка анимированных GIF и WEBP
            - пассивный прогрессбар для показа прогресса анимации
            - различать статические webp от анимированных webp
    - клавиша Tab для входа и выхода со страницы библиотеки
    - режим слайдшоу
        - непременное завершение сладшоу после того как
            - окно/приложение становится неактивным/теряет фокус
            - нажаты любые клавиши
        - пронаблюдать как происходит переключение с последнего изображения на первое
        - пронаблюдать что будет если в папке всего один или два файла изображений
        - подумать о поддержке анимационных файлов
    - при запуске в обычном режиме должна быть иконка в трее
    - добавление и удаление из избранного
    - сортировка по дате и по имени в обоих направлениях
        - через меню по миниатюрам
        - меню сортировки показывает какая сортировка в данный момент применена
    - функция кадрирования
        - Shift + R - сделать кадр в масштабе окна
        - R - сделать кадр в масштабе исходной картинки
    - клавиша F - удаление и добавление из и в избранное
    - всплывающее окно с настройками
    - функция отражения по горизонтали через клавишу M
    - смена курсоров
        - над картинкой
        - при перетаскивании
        - над кнопками
        - в библиотеке над превьюшками должен быть нормальный курсор
    - работа с буфером обмена
        - копирование неанимированного изображения в буфер обмена
        - копирование из буфера обмена в текущую картинку
        - интересно что делать с анимированными изображениями, ведь их поддержки пока в этой части программы нет
    - пройтись по всей справке F1
    - Shift+Tab - переключение папок без захода на страницу библиотеки
    - показывать содержимое файла deep_secrets.txt истины при многкратном увеличении картинки
    - должен создаваться файл viewer.ini для запоминания поворота картинок
    - перелистывание картинок через клавиши Влево и Вправо
        - также через мышку с зажатым Ctrl
        - или через колесо мыши при находящемся поверх миниатюрок курсоре
    - клавиша Вверх и Вниз управляют масштабом на странице вьювера
    - задавать заголовок окна в зависимости от файла открытого при перелистывании и при открытии
    - для каждой открытой папки (или картинки всё-таки?) запоминаются скейл и расположение картинки
    - для картинки и для панели управления своё отдельное контестное меню
        - для элементов из избранного на странице библиотеки
          - пункт в контексном меню - "открыть папку, что содержит эту пикчу"
    - созранение и загрузка сессий открытых файлов
        - в сохранённой сессии открытых папок надо запоминать текущую открытую картинку для каждой папки
    - нормально отрабатывать переход из полноэкранного режима в оконный и обратно
        - в неполноэкранный режим можно войти, если кликнуть на прозрачную область за пределы изображения
        - в полноэкранный режим входим через двойной клик на изображении
        - проверить на других экранах, если их больше 1
        - проверить на адекватность вообще всё
        - нужно так же менять относительную позицию картинки, чтобы визуально она оставалась на месте
    - генерация превьюшек
        - тред создания превьюшек не должен быть запущен для конкретной папки ещё раз, если он УЖЕ запущен по какой-то папке
            - инфа о запущенных тредах показывается внизу сбоку мелким шрифтом
    - двойной клик на странице библиотеки по папке переключает обратно в просмоторщик
    - библиотека
        - превьшки должны появляться в левой части при наведении на них указателя
    - клавиши Home и End переключают к начальной и конечной пикче списка соответственно во вьювере
    - открывать файлы и папки перетаскиванием их в окно
    - клавиша Delete для удаления картинок в корзину и из списка
          - когда удалишь все картинки, то переключение пойдёт на библиотеку и будет выбрана другая папка
                  а ту папку скорее всего надо будет удалить из библиотеки
          - показывать сообщение через центральный всплывающий лейбл
    - при переходе из библиотеки в просмоторщик должна высвечиваться надпись "загрузка"
    - режим лупы через задание интересующей области с помощью Ctrl - Region Zoom In
        - смена курсора над изображением во время зажатия Ctrl
        - отменяется через клавишу ESC восстанавливая масштаб и позицию

- способность отделятся в дубликат - лайтовый (упрощённый) режим через кнопку "открыть папку в копии приложения" в библиотеке
    - без прослушивающего сервера
    - без сброса аргумента в файл для сервера
    - менять иконку на панели задач
        - для обычных иконка будет image_viewer.ico
        - для отделившихся (упрощённых) иконка будет image_viewer.lite
    - без иконки в трее


- проверка на баги стартовой плашки
    - если вьювер уже открыт и ему подают ссылку на несуществующую картинку,
        то он может зависнуть на надписи "загрузка"
    - проверить на открытие заведомо битого файла, единственного в папке
    - проверить на открытие файла в заведомо несуществующей папке, в которой вообще нет изображений


- анимация ряда миниатюрок внизу вьювера при перелистывании изображений и при клике на миниатюру кнопкой мыши
    - во время этой анимации при перелистывании тригетрится ещё анимация скейла и положения самой картинки, так что нужно чтобы они не мешали друг другу, чтобы у них был разный anim_id
    - может быть дрожание в анимации как раз из-за того, что таймеры друг другу мешают - либо не согласованы, либо новый таймер начал работать не выключив все старые таймеры, которые ещё не выключились


- модальность окон
    - форма тегов и комментов должны быть модальными
    - форма настроек может быть модальной, но лучше ей не быть такой, чтобы при настройке параметров можно было увидеть их влияние без закрытия окна настроек

- фича перестановки миниатюр (смена порядка следования изображений)
    - Ctrl + клик - мультивыделение
    - выделение может начинаться с территории главного окна
    - на время всех этих манипуляций ряд минатюрок становится полностью видимым
    - клике по миниатюрам без зажатого Ctrl не должны приводить к переключению на изображение миниатюры
    - красный курсор вставки не должен появлятся между выбранными миниатюрами

- переключение страниц через угловое меню
   - запустил в тестовом режиме прогу без каких-либо данных, со стартовой страницы перешёл сразу во вьювер. Прога не упала, потому что первой загрузилась папка с коментами и она была пустая, о чём и сообщил вьювер. Никаких крашей

- при использовании инструментов типа лупа надо как-то блокировать ввод, чтобы не сбить эту лупу, или при взаимодействии (любом или конкретных) пользователя с программой отменять режим лупы


- проверка системы комментирования (папки для тегов в библиотеке)
  - создание новых папок
  - добавление изображений в папки
  - удаление изображений из папок
