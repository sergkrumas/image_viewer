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

class ServerOrClient():

    @classmethod
    def retrieve_server_data(cls, open_request):
        Globals = cls.globals
        path_str = None
        if os.path.exists(Globals.NO_SOCKETS_CLIENT_DATA_FILENAME):
            try:
                with open(Globals.NO_SOCKETS_CLIENT_DATA_FILENAME, "r") as file:
                    file.seek(0)
                    path_str = file.read()
                os.remove(Globals.NO_SOCKETS_CLIENT_DATA_FILENAME)
                open_request(path_str)
            except:
                pass

    @classmethod
    def remove_server_data(cls):
        Globals = cls.globals
        if os.path.exists(Globals.NO_SOCKETS_SERVER_FILENAME):
            os.remove(Globals.NO_SOCKETS_SERVER_FILENAME)

    @classmethod
    def server_or_client_via_files(cls, path, input_path_dialog_callback):
        Globals = cls.globals
        # КОД ПЕРЕДАЧИ ДАННЫХ ОТ ВТОРОЙ КОПИИ ПРИЛОЖЕНИЯ К ПЕРВОЙ
        if os.path.exists(Globals.NO_SOCKETS_SERVER_FILENAME) and os.path.exists(Globals.NO_SOCKETS_CLIENT_DATA_FILENAME):
            # в случае, если пошло что-то не так,
            # эти два файла останутся.
            # Нужно их обязательно удалить
            os.remove(Globals.NO_SOCKETS_SERVER_FILENAME)
            os.remove(Globals.NO_SOCKETS_CLIENT_DATA_FILENAME)
            sys.exit()
        # становимся второй копией приложения
        if os.path.exists(Globals.NO_SOCKETS_SERVER_FILENAME):
            if os.path.exists(Globals.NO_SOCKETS_CLIENT_DATA_FILENAME):
                # что-то пошло не так:
                # удаляем файл и сразу закрываемся
                os.remove(Globals.NO_SOCKETS_CLIENT_DATA_FILENAME)
                print("removing crash traces")
                sys.exit()
            else:
                # передаём входящие данные к первой копии приложения и сразу закрываемся
                if not path:
                    path = str(QFileDialog.getExistingDirectory(None, "Выбери папку с пикчами"))
                if path:
                    with open(Globals.NO_SOCKETS_CLIENT_DATA_FILENAME, "w+") as file:
                        file.write(path)
                    print("data trasferred")
                else:
                    print("nothing to open")
                sys.exit()
        # становимся первой копией, создав специальный файл
        else:
            open(Globals.NO_SOCKETS_SERVER_FILENAME, "w+").close()
            # если мы не запущены из отладчика,
            # то заправшиваем у пользователя папку для просмотра
            path = input_path_dialog_callback(path)
        return path





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
                block = QByteArray()
                out = QDataStream(block, QIODevice.WriteOnly)
                out.setVersion(QDataStream.Qt_5_3)
                out.writeQString("ping")
                clientConnection = server_obj.nextPendingConnection()
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
                        "The host was not found. Please check the host name and port "
                        "settings.",
                    QLocalSocket.ConnectionRefusedError:
                        "The connection was refused by the peer. Make sure the "
                        "fortune server is running, and check that the host name and "
                        "port settings are correct.",
                    QLocalSocket.PeerClosedError:
                        None,
                }
                msg = errors.get(socketError, "The following error occurred: %s." % client_socket.errorString())

                choose_start_option_callback(do_start_server, path)

            client_socket.connected.connect(transfer_data_callback)
            client_socket.error.connect(client_socket_error)
            client_socket.abort()
            client_socket.connectToServer(SERVER_NAME)

        start_client()

        app = QApplication.instance()
        while not SERVER_STARTED:
            processAppEvents(update_only=False)

        print("end of server_or_client_via_sockets")
        return path


