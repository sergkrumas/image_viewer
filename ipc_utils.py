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

class Window(QWidget):

    def __init__(self, color):
        super().__init__()
        self.color = color
        self.servername = ""
        self.random_value = ""
        self.images = defaultdict(list)
        self.images_done = defaultdict(bool)
        self.setMouseTracking(True)

        self.time_start = None

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.fillRect(self.rect(), self.color)
        painter.drawText(self.rect(), Qt.AlignVCenter | Qt.AlignHCenter,
            f'{self.servername}\n{self.random_value}'
        )

        is_servername_set = bool(self.servername)

        WIDTH = 50
        for key_y, worker_list in self.images.items():
            for x, image in enumerate(worker_list):
                if is_servername_set:
                    key_y = 0
                dest_rect = QRect(x*WIDTH, key_y*WIDTH, WIDTH, WIDTH)
                src_width = min(image.width(), image.height())
                source_rect = QRect(0, 0, src_width, src_width)
                painter.drawImage(dest_rect, image, source_rect)
            if self.images_done[key_y]:
                dest_rect = QRect(0, key_y*WIDTH, WIDTH, WIDTH)
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

        if self.time_start is None:
            self.time_start = time.time()

        self.images[worker_index].append(image)
        self.update()

    def addDone(self, worker_index):
        self.images_done[worker_index] = True

        if all(self.images_done.values()):
            ipc_job_time = time.time() - self.time_start

            time2 = time.time()
            for i in range(WORKER_COUNT):
                task_function(None, i)
            non_ipc_job_time = time.time() - time2
            QMessageBox.critical(None, "DONE", f'{ipc_job_time} vs {non_ipc_job_time}')


        self.update()

class Globals:

    INT_SIZE = 8
    MESSAGE_HEADER_SIZE = INT_SIZE*3


class DataType:
    Undefined = 0
    Greeting = 1
    RequestJob = 2
    JobDescription = 3
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

class SocketWrapper():

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
            total_data_length.to_bytes(Globals.INT_SIZE, 'big') + \
            serial_length.to_bytes(Globals.INT_SIZE, 'big') + \
            bin_length_1.to_bytes(Globals.INT_SIZE, 'big') + \
            bin_length_2.to_bytes(Globals.INT_SIZE, 'big')
        data_to_sent = b''.join((header_data, serial_binary, bin_binary_1, bin_binary_2))

        # print('prepare_data_to_write', serial_data)

        return data_to_sent

    def __init__(self, socket):
        self.socket = socket
        self.socket_buffer = bytes()
        self.readState = self.states.readSize

    def sendDone(self, worker_index):
        data = {
            JSONKEYS.MESSAGE_TYPE: DataType.Done,
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

    def processReadyRead(self):

        def retrieve_data(length):
            data = self.socket_buffer
            requested_data = data[:length]
            left_data = data[length:]
            self.socket_buffer = left_data
            return requested_data

        self.socket_buffer = b''.join((self.socket_buffer, self.socket.readAll().data()))

        self.enough_data_to_read = True

        # while len(self.socket_buffer) > Globals.MESSAGE_HEADER_SIZE and self.enough_data_to_read:
        if True:
            if self.readState == self.states.readSize:
                if len(self.socket_buffer) >= Globals.MESSAGE_HEADER_SIZE:
                    self.content_data_size = int.from_bytes(retrieve_data(Globals.INT_SIZE), 'big')
                    self.serial_data_size = int.from_bytes(retrieve_data(Globals.INT_SIZE), 'big')
                    self.binary_data_1_size = int.from_bytes(retrieve_data(Globals.INT_SIZE), 'big')
                    self.binary_data_2_size = int.from_bytes(retrieve_data(Globals.INT_SIZE), 'big')
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
                            parsed_serial_data = pickle.loads(serial_data)

                            if isinstance(parsed_serial_data, dict):
                                self.currentDataType = parsed_serial_data[JSONKEYS.MESSAGE_TYPE]
                                if self.currentDataType == DataType.Greeting:
                                    pass
                                elif self.currentDataType == DataType.Image:
                                    image = QImage(binary_data_1,
                                        parsed_serial_data[JSONKEYS.WIDTH],
                                        parsed_serial_data[JSONKEYS.HEIGHT],
                                        parsed_serial_data[JSONKEYS.FORMAT],
                                    )
                                    global window
                                    # print('take', image, image.width())
                                    window.addImage(image,
                                        parsed_serial_data[JSONKEYS.WORKER_INDEX]
                                    )

                                elif self.currentDataType == DataType.Done:

                                    window.addDone(parsed_serial_data[JSONKEYS.WORKER_INDEX])
                                else:
                                    print(f'Undefined crap has been received {parsed_serial_data}')

                            else:
                                print(f'Undefined crap has been received, and there is no header section within {parsed_serial_data}')

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

        if self.enough_data_to_read and len(self.socket_buffer) > Globals.MESSAGE_HEADER_SIZE:
            self.socket.readyRead.emit()


def ipc_utils_debug_input_data(worker_index):
    with open('ips_utils_debug_input.data', "r", encoding="utf-8") as file:
        path = file.readlines()[worker_index].strip()
        return path





class ServerWrapper():

    def __init__(self, ):
        self.SERVER_NAME = f'kiv_ipc_{time.time()}'
        # self.SERVER_NAME = f'kiv_ips_'

        self.server_obj = QLocalServer()

        self.clients_sockets = []

        def on_ready_read(client_socket):
            data = client_socket.readAll().data()
            # print('from worker:', data)

        def receive_incoming_worker(server_obj, clients_sockets):
            clientConnSocket = server_obj.nextPendingConnection()
            sw = SocketWrapper(clientConnSocket)
            clientConnSocket.readyRead.connect(sw.processReadyRead)
            # clientConnSocket.readyRead.connect(lambda: on_ready_read(clientConnSocket))
            # clientConnSocket.write('hello'.encode('utf8'))


            # ТУТ МОЖНО ОТДАТЬ ТАСКУ


            clients_sockets.append(sw)

            # clientConnSocket.disconnected.connect(clientConnSocket.deleteLater)
            # clientConnSocket.disconnectFromServer()

        if self.server_obj.listen(self.SERVER_NAME):
            self.server_obj.newConnection.connect(lambda: receive_incoming_worker(self.server_obj, self.clients_sockets))
            # print("server started")
        else:
            QMessageBox.critical(None, "Server", "Unable to start the server: %s." % server_obj.errorString())



def task_function(socket, worker_index):

    filepaths = []

    path = ipc_utils_debug_input_data(worker_index)
    window.setWindowTitle(f'{worker_index} {path}')
    for curdir, folders, files in os.walk(path):
        for filename in files:
            filepath = os.path.join(curdir, filename)
            if filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                filepaths.append(filepath)

    for filepath in filepaths:
        qimage = QImage(filepath).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if not qimage.isNull():
            if socket:
                try:
                    socket.sendQImage(qimage, worker_index, filepath)
                except Exception as e:
                    pass
                window.addImage(qimage, worker_index)
            window.update()
            QApplication.processEvents()

def main():

    app = QApplication([])

    parser = argparse.ArgumentParser()
    # parser.add_argument('path', nargs='?', default=None)
    parser.add_argument('-worker', help="", action="store_true")
    parser.add_argument('-servername', help="")
    parser.add_argument('-i', nargs="?", default=0)
    args = parser.parse_args(sys.argv[1:])

    global window

    if args.worker:
        client = True
        SERVER_NAME = args.servername
        window = Window(Qt.blue)
        window.show()
        window.resize(1500, 100)
        worker_index = int(args.i)
        window.move(100, 900+100*worker_index)
        window.setServerName(SERVER_NAME)


        def worker_init():
            global client_socket
            client_socket = QLocalSocket()
            client_socket_wrapper = SocketWrapper(client_socket)

            def connected_to_server():

                window.update()
                QApplication.processEvents()

                task_function(client_socket_wrapper, worker_index)
                client_socket_wrapper.sendDone(worker_index)

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


            def on_ready_read(client_socket):

                msg = client_socket.readAll()
                if msg:
                    msg = msg.data().decode("utf8")
                    QMessageBox.critical(None, "Client", "Message from server: %s." % msg)


            client_socket.connected.connect(connected_to_server)
            client_socket.error.connect(client_socket_error)
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! по идее здесь надо подключать враппер
            client_socket.readyRead.connect(lambda: on_ready_read(client_socket))
            client_socket.abort()
            client_socket.connectToServer(SERVER_NAME)


        # QTimer.singleShot(1000, worker_init)
        worker_init()
        app.exec()


    else:
        server = True
        window = Window(Qt.red)
        window.show()

        servers = []

        global WORKER_COUNT

        WORKER_COUNT = 5
        for i in range(WORKER_COUNT):
            serv = ServerWrapper()
            servers.append(serv)
            # print('!!!! SERVER', serv.SERVER_NAME)
            subprocess.Popen([sys.executable, __file__, '-worker', '-servername', serv.SERVER_NAME, '-i', str(i)])



        app.exec()


if __name__ == '__main__':
    main()
