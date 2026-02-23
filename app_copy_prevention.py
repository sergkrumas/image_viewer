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
            open_request_as_IPC_server_callback,
            choose_start_option_callback,
        ):

        print("begin of IPC.via_sockets")

        cls.path = path
        cls.open_request_as_IPC_server_callback = open_request_as_IPC_server_callback
        cls.choose_start_option_callback = choose_start_option_callback

        app = QApplication.instance()

        print('before start client')
        cls.start_client()
        print('after start client, before app.exec')
 
        if not cls.SERVER_STARTED:
            # Про петлю app.exec() ниже важно понимать следующее: она нужна тут только для того,
            # чтобы копии приложения застревали здесь и не пытались открывать своё окно,
            # потому как, если в таком случе выполнение покинет пределы via_sockets,
            # то эти окна появятся, а нам этого не надо.
            # При запуске первой копии приложения все события, в том числе запуск сервера,
            # ВНЕЗАПНО происходят ДО выхода из cls.start_client(), что конечно контринтуитивно,
            # однако поэтому для первой копии приложения петля тут не нужна, потому как ей надо
            # выходить из via_sockets и создавать иконку в трее и окно.
            # Дополнительно надо смотреть комментарий в read_data_callback.
            # Я не знаю в чём корни такого контринтутивного поведения, пока думаю, что 
            # всё дело в том, что на Windows QLocalSocket и QLocalServer штуки реализованы
            # через namedpipes.
            # Но всё же, если я захочу портировать эту программу на Linux, то скорее всего
            # для первой копии здесь тоже нужна будет петля, и в do_start_IPC_server придётся
            # вызывать app.exit(), чтобы из неё выйти. А сейчас этот вызов не даёт ничего,
            # потому как в момент работы функии transfer_data_callback мы ещё не находимся в петле,
            # которая запускается следующей строчкой:
            app.exec()

        print('after app.exec')

        print("end of IPC.via_sockets")

        # здесь возвращаем path чисто символически,
        # и это возвращение происходит только тогда,
        # когда приложение заработает как сервер
        return path

    @classmethod
    def start_client(cls): 

        def exit_func():
            # QMessageBox.warning(None, "Job is done", "Меня выключают")
            # print('data-path is sent')
            sys.exit()

        def transfer_data_callback():
            data = str(cls.path).encode("utf8")
            cls.client_socket.write(data)

            # все эти 10 секунд будет крутиться петля в via_sockets,
            # до тех пор пока не сокет не соединится
            cls._timer = QTimer.singleShot(10*1000, exit_func)

        def do_start_IPC_server():
            cls.client_socket.close()
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
            default_error_msg = f"Client socket error: {cls.client_socket.errorString()}"
            # msg = errors.get(socketError, default_error_msg)
            # QMessageBox.critical(None, "Client Socket Error", f"{traceback.format_exc()}\n{msg}")
            # print(msg)

            # если ошибка и произошла, то в нашем случае только из-за QLocalSocket.ServerNotFoundError,
            # и это значит, что сервер не запущен, и тогда нам остаётся лишь запустить этот сервер
            cls.choose_start_option_callback(do_start_IPC_server, cls.path)

        cls.client_socket = QLocalSocket()
        # disconnected бахает, когда сервер вырубает соеденение со своей стороны через disconnectFromServer.
        # Размещение здесь функции exit_func позволяет нам не ждать пока сработает таймер,
        # заведённый в transfer_data_callback
        cls.client_socket.disconnected.connect(exit_func)

        cls.client_socket.connected.connect(transfer_data_callback)
        cls.client_socket.error.connect(client_socket_error)
        cls.client_socket.abort() #reset socket
        cls.client_socket.connectToServer(cls.SERVER_NAME)

    @classmethod
    def start_server(cls):

        def read_data_callback(clientConnSocket):
            path = None
            try:
                path_bytes = clientConnSocket.readAll().data()
                if path_bytes:
                    path = path_bytes.decode("utf8")
            except:
                QMessageBox.critical(None, "Server",
                            f"Unable to read from socket or decode error, {traceback.format_exc()}")

            # иммитация долгого ответа от сервера. Если её активировать, и при этом 
            # клиент будет работать без локальной петли, то тогда клиент успеет
            # показать окно пока ждёт, пока его отключит сервер,
            # а этого допустить ни в коем случае нельзя
            # time.sleep(5)

            # отключаем связь
            clientConnSocket.disconnected.connect(clientConnSocket.deleteLater)
            if clientConnSocket in cls.clients:
                cls.clients.remove(clientConnSocket)
            clientConnSocket.disconnectFromServer()

            # отправляем запрос на обработку
            cls.open_request_as_IPC_server_callback(path)

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
            QMessageBox.critical(None, "Server",
                                f"Unable to start the server: {cls.server_obj.errorString()}")
            print('unable to start server')
            return False
