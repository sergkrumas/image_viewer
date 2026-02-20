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

from _utils import *

from PyQt5.QtNetwork import QLocalServer
from PyQt5.QtNetwork import QLocalSocket

import traceback, os

__import__('builtins').__dict__['_'] = __import__('gettext').gettext

class ServerOrClient():

    SERVER_NAME = "krumassanimageviewer"
    SERVER_STARTED = False

    server_obj = None
    client_socket = None

    @classmethod
    def ipc_via_sockets(
            cls,
            path,
            open_request_callback,
            choose_start_option_callback,
        ):

        print("begin of ServerOrClient.ipc_via_sockets")

        cls.path = path
        cls.open_request_callback = open_request_callback
        cls.choose_start_option_callback = choose_start_option_callback

        cls.start_client()

        while not cls.SERVER_STARTED:
            processAppEvents(update_only=False)

        print("end of ServerOrClient.ipc_via_sockets")
        return path

    @classmethod
    def start_server(cls):
        cls.server_obj = QLocalServer()

        def read_data_callback():
            clientConnSocket = cls.server_obj.nextPendingConnection()

            # TODO: (19 фев 26) тут, по идее, надо только сокеты ловить,
            # а не стремиться читать данные от них,
            # тогда не придётся ждать готовности к чтению

            # тут надо каким-то образом выждать
            # пока клиент получит сообщение о коннекте с этим сервером
            # и отправит нам данные, которые мы сейчас должны прочитать
            if True:
                # или ждём три секунды
                clientConnSocket.waitForReadyRead(3000)
            else:
                # или тянем время отправляя
                # бессмысленный и ненужный в данном случае ответ
                block = QByteArray()
                out = QDataStream(block, QIODevice.WriteOnly)
                out.setVersion(QDataStream.Qt_5_3)
                out.writeQString("ping")
                clientConnSocket.write(block)
                clientConnSocket.flush()

            path = None
            try:
                qbytearray_obj = clientConnSocket.readAll()
                if qbytearray_obj.data():
                    path = qbytearray_obj.data().decode("utf8")
            except:
                traceback_lines = traceback.format_exc()
                traceback_lines += f"\nPath: {path}"
                QMessageBox.critical(None, "Server", f"Unable to read from socket, {traceback_lines}")

            try:
                # Сначала проверяем, открылось ли приложение полностью и открылось ли окно.
                # Ведь при первом открытии может прилететь несколько запросов сразу
                if (cls.globals.main_window is not None) and (path is not None):
                    cls.open_request_callback(path)
            except:
                traceback_lines = traceback.format_exc()
                traceback_lines += f"\nPath: {path}"
                traceback_lines += f"\nID: {os.getpid()}"
                QMessageBox.critical(None, "Request Handling Error", f"{traceback_lines}")

            # deleteLater ставим после чтения данных, ибо участились ошибки типа
            # RuntimeError: wrapped C/C++ object of type QLocalSocket has been deleted
            clientConnSocket.disconnected.connect(clientConnSocket.deleteLater)
            clientConnSocket.disconnectFromServer()

        if cls.server_obj.listen(cls.SERVER_NAME):
            cls.server_obj.newConnection.connect(read_data_callback)
            print("server started")
            return True
        else:
            QMessageBox.critical(None, "Server", "Unable to start the server: %s." % cls.server_obj.errorString())
            return False

    @classmethod
    def start_client(cls): 
        cls.client_socket = QLocalSocket()

        def exit_func():
            sys.exit()

        def transfer_data_callback():
            data = str(cls.path).encode("utf8")
            cls.client_socket.write(data)

            # TODO: (19 фев 26) тут по смыслу больше подошёл бы oneshot-таймер
            global transfer_delay_timer
            transfer_delay_timer = QTimer()
            transfer_delay_timer.timeout.connect(exit_func)
            transfer_delay_timer.setInterval(10*1000)
            transfer_delay_timer.start()

        def do_start_server():
            cls.SERVER_STARTED = cls.start_server()

        def client_socket_error(socketError):
            errors = {
                QLocalSocket.ServerNotFoundError:
                    "The host was not found. Please check the host name and port settings.",
                QLocalSocket.ConnectionRefusedError:
                    "The connection was refused by the peer. Make sure the server is running,"
                    "and check that the host name and port settings are correct.",
                QLocalSocket.PeerClosedError:
                    "The remote socket closed the connection.",
            }
            default_error_msg = "The following error occurred on client socket: %s." % cls.client_socket.errorString()
            msg = errors.get(socketError, default_error_msg)
            print(msg)
            # если ошибка и произошла, то в нашем случае только из-за QLocalSocket.ServerNotFoundError,
            # и это значит, что сервер не запущен, и тогда нам остаётся лишь запустить этот сервер
            cls.choose_start_option_callback(do_start_server, cls.path)

        def on_ready_read(client_socket):
            # читаем ненужный и бессмысленный в данном случае ответ от сервера
            msg = cls.client_socket.readAll()
            if msg.data():
                msg = msg.data().decode("utf8")
                QMessageBox.critical(None, "Client", "Message from server: %s." % msg)

        cls.client_socket.connected.connect(transfer_data_callback)
        cls.client_socket.error.connect(client_socket_error)
        cls.client_socket.readyRead.connect(lambda: on_ready_read(cls.client_socket))
        cls.client_socket.abort() #reset socket
        cls.client_socket.connectToServer(cls.SERVER_NAME)
