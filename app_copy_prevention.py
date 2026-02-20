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

class IPC():

    SERVER_NAME = "krumassanimageviewer"
    SERVER_STARTED = False

    server_obj = None
    client_socket = None

    clients = []

    @classmethod
    def via_sockets(
            cls,
            path,
            open_request_callback,
            choose_start_option_callback,
        ):

        print("begin of IPC.via_sockets")

        cls.path = path
        cls.open_request_callback = open_request_callback
        cls.choose_start_option_callback = choose_start_option_callback

        cls.start_client()

        while not cls.SERVER_STARTED:
            processAppEvents(update_only=False)

        print("end of IPC.via_sockets")
        return path

    @classmethod
    def start_client(cls): 

        def exit_func():
            # QMessageBox.critical(None, "Job is done", "Меня выключают")
            sys.exit()

        def transfer_data_callback():
            data = str(cls.path).encode("utf8")
            cls.client_socket.write(data)

            # TODO: все эти 10 секунд будет крутиться петля в via_sockets,
            # и она грузит проц до 25%, надо придумать что-нибудь поэлегантней,
            # может, в qt можно несколько раз запускать петлю app._exec()?
            # Повторый запуск пригодился бы только для запуска сервера, для клиента такое не нужно.
            cls._timer = QTimer.singleShot(10*1000, exit_func)

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
            # msg = errors.get(socketError, default_error_msg)
            # QMessageBox.critical(None, "Client Socket Error", f"{traceback.format_exc()}\n{msg}")
            # print(msg)

            # если ошибка и произошла, то в нашем случае только из-за QLocalSocket.ServerNotFoundError,
            # и это значит, что сервер не запущен, и тогда нам остаётся лишь запустить этот сервер
            cls.choose_start_option_callback(do_start_server, cls.path)

        cls.client_socket = QLocalSocket()


        cls.client_socket.disconnected.connect(exit_func) # когда сервер вырубает соеденение через disconnectFromServer
        cls.client_socket.connected.connect(transfer_data_callback)
        cls.client_socket.error.connect(client_socket_error)
        # cls.client_socket.readyRead.connect(lambda: on_ready_read(cls.client_socket))
        cls.client_socket.abort() #reset socket
        cls.client_socket.connectToServer(cls.SERVER_NAME)

    @classmethod
    def start_server(cls):

        def read_data_callback(clientConnSocket):
            path = None
            try:
                qbytearray_obj = clientConnSocket.readAll()
                if qbytearray_obj.data():
                    path = qbytearray_obj.data().decode("utf8")
            except:
                QMessageBox.critical(None, "Server",
                            f"Unable to read from socket, {traceback.format_exc()}\nPath: {path}")

            try:
                # Сначала проверяем, открылось ли приложение полностью и открылось ли окно.
                # Ведь при первом открытии может прилететь несколько запросов сразу
                if (cls.globals.main_window is not None) and (path is not None):
                    cls.open_request_callback(path)
            except:
                QMessageBox.critical(None, "Request Handling Error",
                                    f"{traceback.format_exc()}\nPath: {path}\nID: {os.getpid()}")

            # deleteLater ставим после чтения данных, ибо участились ошибки типа
            # RuntimeError: wrapped C/C++ object of type QLocalSocket has been deleted
            clientConnSocket.disconnected.connect(clientConnSocket.deleteLater)
            if clientConnSocket in cls.clients:
                cls.clients.remove(clientConnSocket)
            clientConnSocket.disconnectFromServer()

        def new_connection_callback():
            clientConnSocket = cls.server_obj.nextPendingConnection()
            clientConnSocket.readyRead.connect(lambda: read_data_callback(clientConnSocket))
            cls.clients.append(clientConnSocket)

        cls.server_obj = QLocalServer()

        if cls.server_obj.listen(cls.SERVER_NAME):
            cls.server_obj.newConnection.connect(new_connection_callback)
            print("server started")
            return True
        else:
            QMessageBox.critical(None, "Server", "Unable to start the server: %s." % cls.server_obj.errorString())
            return False

