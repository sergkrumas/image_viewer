# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#  Author: Sergei Krumas (github.com/sergkrumas)
#
# ##### END GPL LICENSE BLOCK #####

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from PyQt5.QtNetwork import QLocalServer
from PyQt5.QtNetwork import QLocalSocket

import traceback, os, sys
import time, random
import subprocess
import argparse
import pickle
from collections import defaultdict




# ПРОТОКОЛ ТЕСТОВОГО СТЕНДА
# воркер подключается к серверу и шлёт сообщение, что он готов к работе
# сервер получает сообщение о готовности к работе и посылает воркеру его таску
# воркер принимает таску
# воркер вынимает очередную подтаску из таски и делает её, результат подтаски отправляет по сокету
# когда все подтаски выполнены, воркер отправляет сигнал серверу о том, что он выполнил работу

class Window(QWidget):

    def __init__(self, color):
        super().__init__()
        self.color = color
        self.servername = ""
        self.random_value = ""
        self.images = defaultdict(list)
        self.images_done = defaultdict(bool)
        self.setMouseTracking(True)

        self.finish_calc_done = False

        self.time_start = None

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.fillRect(self.rect(), self.color)
        painter.drawText(self.rect(), Qt.AlignVCenter | Qt.AlignHCenter,
            f'{self.servername}\n{self.random_value}'
        )

        is_servername_set = bool(self.servername)
        x_offset = int(not is_servername_set)

        WIDTH = 50
        for y_co, worker_list in self.images.items():
            for x, image in enumerate(worker_list):
                if is_servername_set:
                    y_co = 0
                dest_rect = QRect((x+x_offset)*WIDTH, y_co*WIDTH, WIDTH, WIDTH)
                src_width = min(image.width(), image.height())
                source_rect = QRect(0, 0, src_width, src_width)
                painter.drawImage(dest_rect, image, source_rect)
            if self.images_done[y_co]:
                dest_rect = QRect(0, y_co*WIDTH, WIDTH, WIDTH)
                painter.setPen(QPen(Qt.white, 1))
                painter.drawText(dest_rect, Qt.AlignLeft, 'DONE')

        painter.end()

    def mousePressEvent(self, event):
        app = QApplication.instance()
        app.exit()

    def mouseMoveEvent(self, event):
        pass

    def mouseReleaseEvent(self, event):
        pass

    def setServerName(self, name):
        self.servername = name

    def setRandomValue(self, value):
        self.random_value = value

    def addImage(self, image, worker_index):
        # IPC time init
        if self.time_start is None:
            self.time_start = time.time()

        self.images[worker_index].append(image)
        self.update()

    def calc_ipc_and_non_ipc_job_time_when_all_finished(self):
        # может показаться, что можно убрать первое условие,
        # однако оно необходимо из-за того,
        # что значения self.images_done опрашиваются в отрисовке,
        # а как раз после опрашивания значение становится False, поэтому
        # надо обяазательно проверять, что все они выставлены в True 
        if all(self.images_done.values()) and len(self.images_done) == Globals.WORKER_COUNT and not self.finish_calc_done:
            self.finish_calc_done = True
            # IPC time
            ipc_job_time = time.time() - self.time_start

            # non IPC time
            # time2 = time.time()
            # for i in range(Globals.WORKER_COUNT):
            #     task_function(None, i)
            # non_ipc_job_time = time.time() - time2
            non_ipc_job_time = 0.0

            # information
            QMessageBox.critical(None, "DONE", f'{ipc_job_time} vs {non_ipc_job_time}')

    def markAsFinished(self, worker_index):
        self.images_done[worker_index] = True

        self.calc_ipc_and_non_ipc_job_time_when_all_finished()

        self.update()


class TaskThread(QThread):

    update_signal = pyqtSignal(object)

    def __init__(self, task_data, worker_index, socket_wrapper):
        QThread.__init__(self)

        self.task_data = task_data
        self.worker_index = worker_index
        self.socket_wrapper = socket_wrapper

        self.update_signal.connect(lambda data: _globals.main_window.update_signal_from_threads(data))

    def start(self):
        super().start(QThread.IdlePriority)

    def run(self):
        for filepath in self.task_data:
            qimage = QImage(filepath).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if not qimage.isNull():
                try:
                    self.socket_wrapper.sendQImage(qimage, self.worker_index, filepath)
                except Exception as e:
                    pass
                Globals.window.addImage(qimage, self.worker_index)
                Globals.window.update()
                QApplication.processEvents()

        self.socket_wrapper.sendDone(self.worker_index)



class Globals:
    window = None
    WORKER_COUNT = None
    worker_socket = None

class Consts:
    INT_SIZE = 8
    MESSAGE_HEADER_SIZE = INT_SIZE*3

class DataType:
    Undefined = 0
    ReadyForWork = 1
    TaskDescription = 3
    TaskResult = 4

    Image = 5

    Done = 6

class JSONKEYS():
    MESSAGE_TYPE = 0
    WIDTH = 1
    HEIGHT = 2
    FORMAT = 3
    WORKER_INDEX = 4
    FILEPATH = 5
    TASK_DATA = 6

class SocketWrapper(QObject):

    task_received = pyqtSignal(object)

    class states():
        readSize = 0
        readData = 1

    qt_images_formats_dict = dict()
    for attr_name in dir(QImage):
        if attr_name.startswith('Format') and not attr_name == 'Format':
            qt_images_formats_dict[getattr(QImage, attr_name)] = attr_name

    @staticmethod
    def prepare_data_to_write(serial_data, binary_attachment_data_1, binary_attachment_data_2):

        if serial_data is not None:
            serial_binary = pickle.dumps(serial_data)
            serial_length = len(serial_binary)
        else:
            serial_binary = b''
            serial_length = 0

        if binary_attachment_data_1 is not None:
            bin_binary_1 = binary_attachment_data_1
            bin_length_1 = len(binary_attachment_data_1)
        else:
            bin_binary_1 = b''
            bin_length_1 = 0

        if binary_attachment_data_2 is not None:
            bin_binary_2 = binary_attachment_data_2
            bin_length_2 = len(binary_attachment_data_2)
        else:
            bin_binary_2 = b''
            bin_length_2 = 0

        total_data_length = serial_length + bin_length_1 + bin_length_2
        header_data = \
            total_data_length.to_bytes(Consts.INT_SIZE, 'big') + \
            serial_length.to_bytes(Consts.INT_SIZE, 'big') + \
            bin_length_1.to_bytes(Consts.INT_SIZE, 'big') + \
            bin_length_2.to_bytes(Consts.INT_SIZE, 'big')
        data_to_sent = b''.join((header_data, serial_binary, bin_binary_1, bin_binary_2))

        # print('prepare_data_to_write', serial_data)

        return data_to_sent

    def __init__(self, socket):
        super().__init__()

        self.socket = socket
        self.socket_buffer = bytes()
        self.readState = self.states.readSize

        self.task_received.connect(self.do_task)

    def sendDone(self, worker_index):
        data = {
            JSONKEYS.MESSAGE_TYPE: DataType.Done,
            JSONKEYS.WORKER_INDEX: worker_index,
        }
        self.socket.write(self.prepare_data_to_write(data, None, None))

    def sendReadyForWork(self, worker_index):
        data = {
            JSONKEYS.MESSAGE_TYPE: DataType.ReadyForWork,
            JSONKEYS.WORKER_INDEX: worker_index,
        }
        self.socket.write(self.prepare_data_to_write(data, None, None))

    def sendQImage(self, image, worker_index, filepath):
        if image.format() not in [QImage.Format_RGB32, QImage.Format_ARGB32]:
            # На практике у изображения может может быть формат Index8,
            # который не даёт ничего отправить,
            # да и ещё сервер бахается при попытке ему такое отправить,
            # а клиент почему-то нет.
            # Именно поэтому здесь все нестандартные форматы переводим в стандартные,
            # чтобы избежать крашей, глюков, зависаний.
            image = image.convertToFormat(QImage.Format_RGB32)

        ptr = image.constBits()
        ptr.setsize(image.sizeInBytes())
        barray = bytes(ptr)
        data = {
            JSONKEYS.MESSAGE_TYPE: DataType.Image,
            JSONKEYS.WIDTH: image.width(),
            JSONKEYS.HEIGHT: image.height(),
            JSONKEYS.FORMAT: image.format(),
            JSONKEYS.WORKER_INDEX: worker_index,
            JSONKEYS.FILEPATH: filepath,
        }
        # format_str = self.qt_images_formats_dict[image.format()]
        # print(format_str, filepath)

        self.socket.write(self.prepare_data_to_write(data, barray, None))

    def sendTaskToWorker(self, worker_index):
        path = ipc_utils_debug_input_data(worker_index)

        task_filepaths = []
        for curdir, folders, files in os.walk(path):
            for filename in files:
                filepath = os.path.join(curdir, filename)
                if filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    task_filepaths.append(filepath)

        data = {
            JSONKEYS.MESSAGE_TYPE: DataType.TaskDescription,
            JSONKEYS.TASK_DATA: task_filepaths,
        }
        self.socket.write(self.prepare_data_to_write(data, None, None))

    def prepare_task(self, task_data):
        self.task_received.emit(task_data)

    def do_task(self, task_data):

        TaskThread(task_data, worker_index, self).start()


    def processReadyRead(self):

        def retrieve_data(length):
            data = self.socket_buffer
            requested_data = data[:length]
            left_data = data[length:]
            self.socket_buffer = left_data
            return requested_data

        self.socket_buffer = b''.join((self.socket_buffer, self.socket.readAll().data()))

        self.enough_data_to_read = True

        # while len(self.socket_buffer) > Consts.MESSAGE_HEADER_SIZE and self.enough_data_to_read:
        if True:
            if self.readState == self.states.readSize:
                if len(self.socket_buffer) >= Consts.MESSAGE_HEADER_SIZE:
                    self.content_data_size = int.from_bytes(retrieve_data(Consts.INT_SIZE), 'big')
                    self.serial_data_size = int.from_bytes(retrieve_data(Consts.INT_SIZE), 'big')
                    self.binary_data_1_size = int.from_bytes(retrieve_data(Consts.INT_SIZE), 'big')
                    self.binary_data_2_size = int.from_bytes(retrieve_data(Consts.INT_SIZE), 'big')
                    self.readState = self.states.readData
                    # print('content_data_size', self.content_data_size, 'socket_buffer_size', len(self.socket_buffer))
                    # print('size read', self.content_data_size)
                else:
                    pass
                    # print('not enough data to read the data size')

            # здесь обязательно, чтобы было if, и не было else if
            # это нужно для того, чтобы сразу прочитать данные,
            # если они уже есть и не ставить сообщение в очередь через emit
            if self.readState == self.states.readData:
                if self.content_data_size < 0:
                    raise Exception('Fuck!')

                if len(self.socket_buffer) >= self.content_data_size:
                    serial_data = retrieve_data(self.serial_data_size)
                    binary_data_1 = retrieve_data(self.binary_data_1_size)
                    binary_data_2 = retrieve_data(self.binary_data_2_size)

                    try:
                        if serial_data:
                            data = pickle.loads(serial_data)

                            if isinstance(data, dict):
                                self.currentDataType = data[JSONKEYS.MESSAGE_TYPE]

                                if self.currentDataType == DataType.ReadyForWork:
                                    # worker wants to work
                                    self.sendTaskToWorker(data[JSONKEYS.WORKER_INDEX])

                                elif self.currentDataType == DataType.TaskDescription:
                                    # worker receives task
                                    self.prepare_task(data[JSONKEYS.TASK_DATA])

                                elif self.currentDataType == DataType.Image:
                                    # worker sends image
                                    image = QImage(binary_data_1,
                                        data[JSONKEYS.WIDTH],
                                        data[JSONKEYS.HEIGHT],
                                        data[JSONKEYS.FORMAT],
                                    )
                                    # print('take', image, image.width())
                                    Globals.window.addImage(image,
                                        data[JSONKEYS.WORKER_INDEX]
                                    )

                                elif self.currentDataType == DataType.Done:
                                    # worker finsihes his work
                                    Globals.window.markAsFinished(data[JSONKEYS.WORKER_INDEX])

                                else:
                                    print(f'Undefined crap has been received {data}')

                            else:
                                print(f'Undefined crap has been received, and there is no header section within {data}')

                    except Exception as e:
                        raise
                        print(e, 'aborting...')
                        self.socket.abort()

                        if not self.socket.isValid():
                            self.socket.abort()
                            return

                    self.content_data_size = 0
                    self.readState = self.states.readSize

                else:
                    self.enough_data_to_read = False
                    print('not enough data to read', len(self.socket_buffer), self.content_data_size)

        if self.enough_data_to_read and len(self.socket_buffer) > Consts.MESSAGE_HEADER_SIZE:
            self.socket.readyRead.emit()






def ipc_utils_debug_input_data(worker_index):
    with open('ips_utils_debug_input.data', "r", encoding="utf-8") as file:
        path = file.readlines()[worker_index].strip()
        return path


def worker_init(window, SERVER_NAME, worker_index):

    def connected_to_server():
        window.update()
        QApplication.processEvents()
        cli_sock_wrapper = Globals.cli_sock_wrapper
        cli_sock_wrapper.sendReadyForWork(worker_index)

    def client_socket_error(socketError):
        errors = {
            QLocalSocket.ServerNotFoundError:
                "The host was not found. Please check the host name and port settings.",
            QLocalSocket.ConnectionRefusedError:
                "The connection was refused by the peer. Make sure the server is running,"
                "and check that the host name and port settings are correct.",
            QLocalSocket.PeerClosedError:
                None,
        }
        default_error_msg = "The following error occurred on client socket: %s." % client_socket.errorString()
        msg = errors.get(socketError, default_error_msg)
        print(msg)

    Globals.worker_index = worker_index

    cli_sock = QLocalSocket()
    Globals.cli_sock_wrapper = sw = SocketWrapper(cli_sock)
    cli_sock.connected.connect(connected_to_server)
    cli_sock.error.connect(client_socket_error)
    cli_sock.readyRead.connect(sw.processReadyRead)
    cli_sock.abort()
    cli_sock.connectToServer(SERVER_NAME)


class ServerWrapper():

    def __init__(self, ):
        self.SERVER_NAME = f'kiv_ipc_{time.time()}'
        self.server_obj = QLocalServer()
        self.clients_sockets = []

        def receive_incoming_worker(server_obj, clients_sockets):
            cli_sock_conn = server_obj.nextPendingConnection()
            sw = SocketWrapper(cli_sock_conn)
            cli_sock_conn.readyRead.connect(sw.processReadyRead)
            # таска воркеру отдаётся через sendTaskToWorker
            clients_sockets.append(sw)

            # cli_sock_conn.disconnected.connect(cli_sock_conn.deleteLater)
            # cli_sock_conn.disconnectFromServer()

        if self.server_obj.listen(self.SERVER_NAME):
            self.server_obj.newConnection.connect(lambda: receive_incoming_worker(self.server_obj, self.clients_sockets))
            # print("server started")
        else:
            QMessageBox.critical(None, "Server", "Unable to start the server: %s." % server_obj.errorString())


def set_system_tray_icon(app, icon):
    sti = QSystemTrayIcon(app)

    app.setProperty("stray_icon", sti)

    if True:
        opm = QPixmap(icon.pixmap(icon.actualSize(QSize(64, 64))))

        pm = QPixmap(opm.width(), opm.height())
        pm.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pm)
        painter.drawPixmap(QPoint(0, 0), opm)
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(40)
        painter.setFont(font)
        painter.drawText(QPoint(0, pm.height()), "W")
        painter.end()

        icon_frame = QIcon(pm)
        sti.setIcon(icon_frame)

    @pyqtSlot()
    def on_trayicon_activated(reason):
        if reason == QSystemTrayIcon.Trigger:
            pass

        if reason == QSystemTrayIcon.Context:
            menu = QMenu()
            menu.addSeparator()
            menu.addAction('Krumassan Image Viewer Worker').setEnabled(False)
            quit = menu.addAction('Quit')
            action = menu.exec_(QCursor().pos())
            if action == quit:
                app = QApplication.instance()
                app.exit()

    sti.activated.connect(on_trayicon_activated)
    sti.setToolTip('Krumassan Image Viewer Worker')
    sti.show()



def main():

    app = QApplication([])

    parser = argparse.ArgumentParser()
    # parser.add_argument('path', nargs='?', default=None)
    parser.add_argument('-worker', help="", action="store_true")
    parser.add_argument('-servername', help="")
    parser.add_argument('-i', nargs="?", default=0)
    args = parser.parse_args(sys.argv[1:])

    if args.worker:
        # client
        SERVER_NAME = args.servername
        Globals.window = window = Window(Qt.black)
        window.show()
        window.resize(1500, 100)
        worker_index = int(args.i)
        window.move(100, 900+100*worker_index)
        window.setServerName(SERVER_NAME)

        path_icon = os.path.join(os.path.dirname(__file__), "image_viewer_lite.ico")
        icon = QIcon()
        icon.addFile(path_icon)
        sti = set_system_tray_icon(app, icon)

        worker_init(window, SERVER_NAME, worker_index)
        app.exec()

        if sti:
            sti.hide()

    else:
        # server
        Globals.window = window = Window(Qt.gray)
        window.show()

        servers = []
        Globals.WORKER_COUNT = 1
        for i in range(Globals.WORKER_COUNT):
            serv = ServerWrapper()
            servers.append(serv)
            subprocess.Popen([sys.executable, __file__, '-worker', '-servername', serv.SERVER_NAME, '-i', str(i)])
        app.exec()

if __name__ == '__main__':
    main()
