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

from gettext import gettext as _

class ServerOrClient():

    @classmethod
    def server_or_client_via_sockets(
            cls,
            path,
            open_request_callback,
            choose_start_option_callback,
        ):

        print("begin of server_or_client_via_sockets")

        SERVER_NAME = "krumasimageviewer"
        SERVER_STARTED = False

        def start_server():
            global server_obj
            server_obj = QLocalServer()

            def read_data_callback(server_obj):
                clientConnection = server_obj.nextPendingConnection()

                # тут надо каким-то образом выждать
                # пока клиент получит сообщение о коннекте с этим сервером
                # и отправит нам данные, которые мы сейчас должны прочитать
                if True:
                    # или ждём три секунды
                    clientConnection.waitForReadyRead(3000)
                else:
                    # или тянем время отправляя
                    # бессмысленный и ненужный в данном случае ответ
                    block = QByteArray()
                    out = QDataStream(block, QIODevice.WriteOnly)
                    out.setVersion(QDataStream.Qt_5_3)
                    out.writeQString("ping")
                    clientConnection.write(block)
                    clientConnection.flush()

                path = None
                try:
                    data = clientConnection.read(2 ** 14)
                    if data is not None:
                        path = data.decode("utf8")
                except:
                    traceback_lines = traceback.format_exc()
                    traceback_lines += f"\nPath: {path}"
                    QMessageBox.critical(None, "Server", f"Unable to read from socket, {traceback_lines}")

                Globals = cls.globals

                try:
                    # Сначала проверяем, открылось ли приложение полностью и открылось ли окно.
                    # Ведь при первом открытии может прилететь несколько запросов сразу
                    if (Globals.main_window is not None) and (path is not None):
                        open_request_callback(path)
                except:
                    traceback_lines = traceback.format_exc()
                    traceback_lines += f"\nPath: {path}"
                    traceback_lines += f"\nID: {os.getpid()}"
                    QMessageBox.critical(None, "Request Handling Error", f"{traceback_lines}")

                # deleteLater ставим после чтения данных, ибо участились ошибки типа
                # RuntimeError: wrapped C/C++ object of type QLocalSocket has been deleted
                clientConnection.disconnected.connect(clientConnection.deleteLater)
                clientConnection.disconnectFromServer()

            if not server_obj.listen(SERVER_NAME):
                QMessageBox.critical(None, "Server", "Unable to start the server: %s." % server_obj.errorString())
                return False
            else:
                server_obj.newConnection.connect(lambda: read_data_callback(server_obj))
                print("server started")
                return True

        def start_client():
            global client_socket
            client_socket = QLocalSocket()

            def exit_func():
                sys.exit()

            def transfer_data_callback():
                data = str(path).encode("utf8")
                client_socket.writeData(data)

                global transfer_delay_timer
                transfer_delay_timer = QTimer()
                transfer_delay_timer.timeout.connect(exit_func)
                transfer_delay_timer.setInterval(10*1000)
                transfer_delay_timer.start()

            def do_start_server():
                nonlocal SERVER_STARTED
                SERVER_STARTED = start_server()

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
                # если ошибка и произошла, то в нашем случае только из-за QLocalSocket.ServerNotFoundError,
                # и это значит, что сервер не запущен, и тогда нам остаётся лишь запустить этот сервер
                choose_start_option_callback(do_start_server, path)

            def on_ready_read(client_socket):
                # читаем ненужный и бессмысленный в данном случае ответ от сервера
                msg = client_socket.readAll()
                if msg:
                    msg = msg.data().decode("utf8")
                    QMessageBox.critical(None, "Client", "Message from server: %s." % msg)

            client_socket.connected.connect(transfer_data_callback)
            client_socket.error.connect(client_socket_error)
            client_socket.readyRead.connect(lambda: on_ready_read(client_socket))
            client_socket.abort()
            client_socket.connectToServer(SERVER_NAME)

        start_client()

        while not SERVER_STARTED:
            processAppEvents(update_only=False)

        print("end of server_or_client_via_sockets")
        return path


