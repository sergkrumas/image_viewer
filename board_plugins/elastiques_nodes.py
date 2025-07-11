
import sys
import os
import subprocess
import math
import time
import random
from functools import partial

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

sys.path.append('../')
import _utils





RUN_AS_STANDALONE_PYQT_APP = False

# - исходники https://github.com/Infernno/qt5-examples/tree/master/widgets/graphicsview
# - описание исходников https://doc.qt.io/qt-5/qtwidgets-graphicsview-elasticnodes-example.html

# очень интересные результаты получаются, если выставить INTERVAL = 1
# INTERVAL = int(1000 / 25) # default
INTERVAL = int(1000 / 40)
# INTERVAL = 1
# INTERVAL = 50







if not RUN_AS_STANDALONE_PYQT_APP:
    _QGraphicsItem = QGraphicsItem
    _QGraphicsView = QGraphicsView
    _QGraphicsScene = QGraphicsScene

    class MockAnyQtCallChaine():

        def __new__(cls, *args, **kwargs):
            instance = super(MockAnyQtCallChaine, cls).__new__(cls)
            instance.__dict = dict(**kwargs)
            return instance

        def __call__(self, *args, **kwargs):
            return self._value

        def __getattr__(self, name):
            if name in self.__dict.keys():
                value = self.__dict[name]
            else:
                value = self
            self._value = value
            return self

    class QGraphicsItem(QObject):

        ItemIsMovable = _QGraphicsItem.ItemIsMovable
        ItemSendsGeometryChanges = _QGraphicsItem.ItemSendsGeometryChanges
        DeviceCoordinateCache = _QGraphicsItem.DeviceCoordinateCache

        def __init__(self):
            super().__init__()
            self._pos = QPointF()
            self._scene = None
            self.state = 0

        def setFlag(self, *args):
            pass

        def setCacheMode(self, *args, **kwargs):
            pass

        def setZValue(sefl, *args, **kwargs):
            pass

        def setAcceptedMouseButtons(self, value):
            pass

        def mapFromItem(self, item, x, y):
            return item.pos() - self.pos()

        def mapToItem(self, item, x, y):
            return self.pos() - item.pos()

        def prepareGeometryChange(self):
            pass

        def setPos(self, *args):
            if isinstance(args, tuple):
                pos = QPointF(*args)
            elif isinstance(args, (QPointF, QPoint)):
                pos = QPointF(args)
            self._pos = pos
            # self.scene().invalidate(None, None)
            # an event ItemMoved should be generated here!

        def pos(self):
            return self._pos

        def scene(self):
            return self._scene

        def scenePos(self):
            return board_widget.board_MapToViewport(self.pos())

    class QGraphicsView(QObject):

        CacheBackground = _QGraphicsView.CacheBackground
        BoundingRectViewportUpdate = _QGraphicsView.BoundingRectViewportUpdate
        AnchorUnderMouse = _QGraphicsView.AnchorUnderMouse

        def __init__(self, parent):
            super().__init__()
            self._scene = None
        def setScene(self, scene, *args, **kwargs):
            self._scene = scene

        def setCacheMode(*args, **kwargs):
            pass
        def setViewportUpdateMode(*args, **kwargs):
            pass
        def setRenderHint(*args, **kwargs):
            pass
        def setTransformationAnchor(*args, **kwargs):
            pass
        def scale(self, x, y):
            global board_widget
            if y > 1.0:
                pass
            else:
                y = -y
            board_widget.board_do_scale(y)

        def setMinimumSize(*args, **kwargs):
            pass
        def setWindowTitle(*args, **kwargs):
            pass

        def parent(self):
            class ParentMock():
                def setWindowTitle(self, title):
                    pass
            return ParentMock()

        def sceneRect(self):
            return self._scene.sceneRect()

        def keyPressEvent(self, event):
            board_widget.board_keyPressEventDefault(event)

        def transform(self, *args, **kwargs):
            return MockAnyQtCallChaine(width=1.0)


    class QGraphicsScene(QObject):

        NoIndex = _QGraphicsScene.NoIndex
        BackgroundLayer = _QGraphicsScene.BackgroundLayer

        def __init__(self, widget):
            super().__init__()
            self.widget = widget
            self._items = []
            self._scene_rect = QRectF()

        def setItemIndexMethod(self, *args, **kwargs):
            pass
        def setSceneRect(self, *args, **kwargs):
            self._scene_rect = QRectF(*args)

        def sceneRect(self):
            rect = board_MapRectToViewport(board_widget, self._scene_rect)
            return rect

        def addItem(self, item):
            self.items().append(item)
            item._scene = self

        def removeItem(self, item):
            item._scene = None
            self.items().remove(item)
            if isinstance(item, Node):
                items = self.items()
                for edge in item.edgeList:
                    if edge in items:
                        items.remove(edge)

        def items(self):
            return self._items

        def mouseGrabberItem(self):
            return PluginNodeEditor.drag_node

        def invalidate(self, rect, type):
            board_widget.update()
            self.widget.itemMoved()




class Edge(QGraphicsItem):

    def __init__(self, sourceNode, destNode):
        super().__init__()

        self.source = sourceNode
        self.dest = destNode
        self.arrowSize = 10

        self.setAcceptedMouseButtons(Qt.NoButton)
        self.source.addEdge(self)
        self.dest.addEdge(self)

        self.adjust()

    def sourceNode(self):
        return self.source

    def destNode(self):
        return self.dest

    def adjust(self):
        # укорачивает длину рёбер, в противном случае рёбра будут рисоваться поверх нод, и это будет выглядеть некрасиво
        if not self.source or not self.dest:
            return

        line = QLineF(self.mapFromItem(self.source, 0, 0), self.mapFromItem(self.dest, 0, 0))
        length = line.length()

        self.prepareGeometryChange()

        if length > 10:
            edgeOffset = QPointF((line.dx() * 10.0) / length, (line.dy() * 10.0) / length)
            self.sourcePoint = line.p1() + edgeOffset
            self.destPoint = line.p2() - edgeOffset
        else:
            self.sourcePoint = self.destPoint = line.p1()

    def boundingRect(self):
        if not self.source or not self.dest:
            return QRectF()

        penWidth = 1
        extra = (penWidth + self.arrowSize) / 2.0

        return QRectF(self.sourcePoint, QSizeF(self.destPoint.x() - self.sourcePoint.x(),
                                          self.destPoint.y() - self.sourcePoint.y())).normalized().adjusted(-extra, -extra, extra, extra)

    BLACK = QColor.fromHslF(0.0, 1.0, 0.0, 0.2)

    def paint(self, painter, option, widget, color=BLACK):
        if not self.source or not self.dest:
            return

        line = QLineF(self.sourcePoint, self.destPoint)

        # https://stackoverflow.com/questions/37105308/how-does-qfuzzycompare-work-in-qt
        def qFuzzyCompare(p1, p2):
            return (abs(p1 - p2) * 1000000000000. <= min(abs(p1), abs(p2)))

        # if qFuzzyCompare(line.length(), 0.):
        #     return

        _bool = color is Edge.BLACK

        # if _bool:
        #     color = Qt.yellow

        painter.setPen(QPen(color, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(line)

        angle = math.atan2(-line.dy(), line.dx())

        M_PI = math.pi

        angle2 = M_PI / 2.4 #M_PI / 3.0
        sourceArrowP1 = self.sourcePoint + QPointF(math.sin(angle + angle2) * self.arrowSize, math.cos(angle + angle2) * self.arrowSize)
        sourceArrowP2 = self.sourcePoint + QPointF(math.sin(angle + M_PI - angle2) * self.arrowSize, math.cos(angle + M_PI - angle2) * self.arrowSize)
        destArrowP1 = self.destPoint + QPointF(math.sin(angle - M_PI / 3) * self.arrowSize, math.cos(angle - M_PI / 3) * self.arrowSize)
        destArrowP2 = self.destPoint + QPointF(math.sin(angle - M_PI + M_PI / 3) * self.arrowSize, math.cos(angle - M_PI + M_PI / 3) * self.arrowSize)

        painter.setBrush(color)
        if not _bool:
            polygon1 = QPolygonF()
            polygon1.append(line.p1())
            polygon1.append(sourceArrowP1)
            polygon1.append(sourceArrowP2)

            painter.drawPolygon(polygon1)

        if False:
            polygon2 = QPolygonF()
            polygon2.append(line.p2())
            polygon2.append(destArrowP1)
            polygon2.append(destArrowP2)

            painter.drawPolygon(polygon2)



class Node(QGraphicsItem):

    def __init__(self, graphWidget):
        super().__init__()

        self.edgeList = []

        self.activated = True
        self.excluded = False

        self.newPos = QPointF()
        self.graph = graphWidget

        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setZValue(-1)

        self.pushing_vec = QPointF()
        self.pulling_vec = QPointF()

        self.pushing_list = []
        self.pulling_list = []

    def edges(self):
        return self.edgeList

    def addEdge(self, edge):
        self.edgeList.append(edge)
        edge.adjust()

    def calculateForces(self):
        if not self.scene():
            return

        # Sum up all forces pushing this item away
        xvel = 0.0
        yvel = 0.0

        pushing_xvel = 0.0
        pushing_yvel = 0.0

        self.pushing_list = []
        self.pulling_list = []

        for item in self.scene().items():
            if not isinstance(item, Node):
                continue

            vec = self.mapToItem(item, 0, 0)
            dx = vec.x()
            dy = vec.y()
            l = 2.0 * (dx * dx + dy * dy)
            if l > 0.0:
                yval = (dy * 150.0) / l
                xval = (dx * 150.0) / l
                pushing_xvel += xval
                pushing_yvel += yval
                self.pushing_list.append(QPointF(xval, yval))

        xvel += pushing_xvel
        yvel += pushing_yvel

        self.pushing_vec = QPointF(pushing_xvel, pushing_yvel)


        # Now subtract all forces pulling items together
        weight = (len(self.edgeList) + 1) * 10

        pulling_xvel = 0.0
        pulling_yvel = 0.0
        current_items = self.scene().items()
        for edge in self.edgeList:
            if edge not in current_items:
                # Тут могут оказаться уже удалённые рёбра, поэтому проверяем.
                # Если обрабатывать это здесь, то размер кода будет наименьшим, мне просто лень сейчас заморачиваться.
                continue
            if edge.sourceNode() is self:
                vec = self.mapToItem(edge.destNode(), 0, 0)
            else:
                vec = self.mapToItem(edge.sourceNode(), 0, 0)

            xval = vec.x() / weight
            yval = vec.y() / weight
            pulling_xvel += xval
            pulling_yvel += yval

            self.pulling_list.append(QPointF(xval, yval))

        xvel -= pulling_xvel
        yvel -= pulling_yvel

        self.pulling_vec = QPointF(pulling_xvel, pulling_yvel)

        if abs(xvel) < 0.1 and abs(yvel) < 0.1:
            xvel = yvel = 0.0

        # t = time.time()
        # xvel = xvel*abs(math.sin(t))
        # yvel = yvel*abs(math.cos(t))

        if self.scene().mouseGrabberItem() is self or not self.activated:
            self.newPos = self.pos()
        else:
            self.newPos = self.pos() + QPointF(xvel, yvel)
            if RUN_AS_STANDALONE_PYQT_APP:
                sceneRect = self.scene().sceneRect()
            else:
                sceneRect = self.scene()._scene_rect
            self.newPos = QPointF(
                min(max(self.newPos.x(), sceneRect.left() + 10), sceneRect.right() - 10),
                min(max(self.newPos.y(), sceneRect.top() + 10), sceneRect.bottom() - 10)
            )

    def advancePosition(self):
        if self.newPos == self.pos():
            return False

        self.setPos(self.newPos)
        return True

    def boundingRect(self):
        adjust = 2
        return QRectF( -10 - adjust, -10 - adjust, 23 + adjust, 23 + adjust)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(-10, -10, 20, 20)
        return path

    def paint(self, painter, option, widget):
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.darkGray)
        painter.drawEllipse(-7, -7, 20, 20)

        gradient = QRadialGradient(-3, -3, 10)
        if option.state & QStyle.State_Sunken:
            gradient.setCenter(3, 3)
            gradient.setFocalPoint(3, 3)
            gradient.setColorAt(1, QColor(Qt.yellow).lighter(120))
            gradient.setColorAt(0, QColor(Qt.darkYellow).lighter(120))
        else:
            gradient.setColorAt(0, Qt.yellow)
            gradient.setColorAt(1, Qt.darkYellow)
        painter.setBrush(gradient)

        painter.setPen(QPen(Qt.black, 0))
        painter.drawEllipse(-10, -10, 20, 20)

    def itemChange(self, change, value):
        if change == self.ItemPositionHasChanged:
            for edge in self.edgeList:
                edge.adjust()
            self.graph.itemMoved()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.update()
        super().mouseReleaseEvent(event)

    def moveBy(self, x, y):
        pos = self.pos()

        pos.setX(pos.x()+x)
        pos.setY(pos.y()+y)

        self.setPos(pos)

class GraphWidget(QGraphicsView):

    def __init__(self, parent):
        super().__init__(parent)

        self.timerId = 0

        self.scene = scene = QGraphicsScene(self)
        scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        scene.setSceneRect(-400, -400, 600, 600)
        self.setScene(scene)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.scale(0.8, 0.8)
        self.setMinimumSize(600, 600)
        self.setWindowTitle("Elastic Nodes")

        node1 = Node(self)
        node2 = Node(self)
        node3 = Node(self)
        node4 = Node(self)
        self.centerNode = Node(self)
        node6 = Node(self)
        node7 = Node(self)
        node8 = Node(self)
        node9 = Node(self)
        scene.addItem(node1)
        scene.addItem(node2)
        scene.addItem(node3)
        scene.addItem(node4)
        scene.addItem(self.centerNode)
        scene.addItem(node6)
        scene.addItem(node7)
        scene.addItem(node8)
        scene.addItem(node9)
        scene.addItem(Edge(node1, node2))
        scene.addItem(Edge(node2, node3))
        scene.addItem(Edge(node2, self.centerNode))
        scene.addItem(Edge(node3, node6))
        scene.addItem(Edge(node4, node1))
        scene.addItem(Edge(node4, self.centerNode))
        scene.addItem(Edge(self.centerNode, node6))
        scene.addItem(Edge(self.centerNode, node8))
        scene.addItem(Edge(node6, node9))
        scene.addItem(Edge(node7, node4))
        scene.addItem(Edge(node8, node7))
        scene.addItem(Edge(node9, node8))

        node1.setPos(-50, -50)
        node2.setPos(0, -50)
        node3.setPos(50, -50)
        node4.setPos(-50, 0)
        self.centerNode.setPos(0, 0)
        node6.setPos(50, 0)
        node7.setPos(-50, 50)
        node8.setPos(0, 50)
        node9.setPos(50, 50)

        self.itemMoved()

    def itemMoved(self):
        if not self.timerId:
            self.timerId = self.startTimer(INTERVAL)

        # print('started')

    def keyPressEvent(self, event):
        key = event.key()

        MOVE_DIST = 50
        if key == Qt.Key_Up:
            self.centerNode.moveBy(0, -MOVE_DIST)
        elif key == Qt.Key_Down:
            self.centerNode.moveBy(0, MOVE_DIST)
        elif key == Qt.Key_Left:
            self.centerNode.moveBy(-MOVE_DIST, 0)
        elif key == Qt.Key_Right:
            self.centerNode.moveBy(MOVE_DIST, 0)
        elif key == Qt.Key_Plus:
            self.zoomIn()
        elif key == Qt.Key_Minus:
            self.zoomOut()
        elif key in [Qt.Key_Space, Qt.Key_Enter]:
            self.shuffle()
        else:
            super().keyPressEvent(event)

    def timerEvent(self, event):
        items = self.scene.items()
        nodes = []

        for item in items:
            if isinstance(item, Node):
                nodes.append(item)

        # print('timer event')
        for node in nodes:
            # print('calculate forces for node', node)
            node.calculateForces()

        itemsMoved = False
        for node in nodes:
            if node.activated and node.advancePosition():
                itemsMoved = True

        if not itemsMoved:
            self.killTimer(self.timerId)
            # print('killed', time.time())
            self.timerId = 0

        self.parent().setWindowTitle(str(time.time()))

        self.scene.invalidate(self.sceneRect(), QGraphicsScene.BackgroundLayer)

    def wheelEvent(self, event):
        self.scaleView(math.pow(2., event.angleDelta().y() / 240.0))

    def scaleView(self, scaleFactor):
        factor = self.transform().scale(scaleFactor, scaleFactor).mapRect(QRectF(0, 0, 1, 1)).width()
        if factor < 0.07 or factor > 100:
            return
        self.scale(scaleFactor, scaleFactor)

    def zoomIn(self):
        self.scaleView(1.2)

    def zoomOut(self):
        self.scaleView(1/1.2)

    def shuffle(self):
        # взбесить ноды
        items = self.scene.items()
        for item in items:
            if isinstance(item, Node):
                item.setPos(-150 + random.randint(0, 300), -150 + random.randint(0, 300))

    def drawBackground(self, painter, rect):
        sceneRect = self.sceneRect()
        rightShadow = QRectF(sceneRect.right(), sceneRect.top() + 5, 5, sceneRect.height())
        bottomShadow = QRectF(sceneRect.left() + 5, sceneRect.bottom(), sceneRect.width(), 5)

        if rightShadow.intersects(rect) or rightShadow.contains(rect):
            painter.fillRect(rightShadow, Qt.darkGray)
        if bottomShadow.intersects(rect) or bottomShadow.contains(rect):
            painter.fillRect(bottomShadow, Qt.darkGray)

        gradient = QLinearGradient(sceneRect.topLeft(), sceneRect.bottomRight())
        gradient.setColorAt(0, Qt.white)
        gradient.setColorAt(1, Qt.lightGray)
        painter.fillRect(rect.intersected(sceneRect), gradient)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(sceneRect)

        textRect = QRectF(sceneRect.left() + 4, sceneRect.top() + 4, sceneRect.width() - 4, sceneRect.height() - 4)

        message = "Click and drag the nodes around, and zoom with the mouse wheel or the '+' and '-' keys"

        font = painter.font()
        font.setBold(True)
        font.setPointSize(14)
        painter.setFont(font)
        painter.setPen(Qt.lightGray)
        painter.drawText(textRect.translated(2, 2), message)
        painter.setPen(Qt.black)
        painter.drawText(textRect, message)

        b = type('Base', (), {})()
        def draw_vector(item, vector, color, scale=20.0):
            b.sourcePoint = vector*scale
            b.destPoint = QPointF(0, 0)
            b.sourcePoint += item.scenePos()
            b.destPoint += item.scenePos()
            b.dest = True
            b.source = True
            b.arrowSize = 10
            painter.save()
            Edge.paint(b, painter, None, None, color)
            painter.restore()

        for item in self.scene.items():
            if not isinstance(item, Node):
                continue

            a = -item.pulling_vec
            b = item.pushing_vec
            if PluginNodeEditor.show_pullling_sum:
                draw_vector(item, a, Qt.red)
            if PluginNodeEditor.show_pushing_sum:
                draw_vector(item, b, Qt.green)

            if PluginNodeEditor.show_all_sum:
                sum_vector = a + b
                draw_vector(item, sum_vector, Qt.black)

            if PluginNodeEditor.show_pushing_list:
                for v in item.pushing_list:
                    draw_vector(item, v, Qt.blue, 100.0)
            if PluginNodeEditor.show_pulling_list:
                for v in item.pulling_list:
                    draw_vector(item, -v, Qt.cyan)




class PluginNodeEditor():

    TYPE_NODE = 1
    TYPE_EDGE = 2
    OPERATION_ADD = 3
    OPERATION_REMOVE = 4
    OPERATION_VIEW = 5

    type_state = TYPE_NODE
    op_state = OPERATION_VIEW
    
    ############################

    drag_node = None

    near_mouse_node = None
    near_mouse_edge = None
    magazin = []

    show_pullling_sum = True
    show_pushing_sum = True
    show_pulling_list = True
    show_pushing_list = True
    show_all_sum = True

    @staticmethod
    def mouse_global_pos():
        return board_widget.board_MapToBoard(board_widget.mapFromGlobal(QCursor().pos()))

    @classmethod
    def change_editing_state(cls, key, board_widget):

        global widget

        if False:
            pass

        elif key == Qt.Key_V:

            if cls.type_state != cls.TYPE_NODE:
                cls.type_state = cls.TYPE_NODE

            if cls.op_state == cls.OPERATION_VIEW:
                pass

            elif cls.op_state == cls.OPERATION_ADD:

                node = Node(widget)
                node.setPos(PluginNodeEditor.mouse_global_pos())
                node.activated = True
                widget.scene.addItem(node)

            elif cls.op_state == cls.OPERATION_REMOVE:

                nearest_node = PluginNodeEditor.find_nearest_node()
                if nearest_node is not None:
                    widget.scene.removeItem(nearest_node)

        elif key == Qt.Key_E:

            if cls.type_state != cls.TYPE_EDGE:
                cls.type_state = cls.TYPE_EDGE

            if cls.op_state == cls.OPERATION_VIEW:
                pass

            elif cls.op_state == cls.OPERATION_ADD:

                nearest_node = PluginNodeEditor.find_nearest_node()
                if nearest_node is not None:
                    PluginNodeEditor.magazin.append(nearest_node)
                    nearest_node.excluded = True
                else:
                    board_widget.show_center_label('empty')

                if len(PluginNodeEditor.magazin) > 1:
                    node1, node2 = PluginNodeEditor.magazin
                    node1.excluded = False
                    node2.excluded = False
                    if node1 is not node2:
                        widget.scene.addItem(Edge(node1, node2))
                    else:
                        board_widget.show_center_label('the same node added twice')
                    PluginNodeEditor.magazin.clear()

            elif cls.op_state == cls.OPERATION_REMOVE:

                nearest_edge = PluginNodeEditor.find_nearest_edge()
                if nearest_edge is not None:
                    widget.scene.removeItem(nearest_edge)

        elif key == Qt.Key_T:
            if cls.op_state == cls.OPERATION_ADD:
                cls.op_state = cls.OPERATION_REMOVE
                st = 'removing mode'
            elif cls.op_state == cls.OPERATION_REMOVE:
                cls.op_state = cls.OPERATION_VIEW
                st = 'viewing mode'
            elif cls.op_state == cls.OPERATION_VIEW:
                cls.op_state = cls.OPERATION_ADD
                st = 'adding mode'
            board_widget.show_center_label(st)

        elif key == Qt.Key_A:

            nearest_node = PluginNodeEditor.find_nearest_node()
            if nearest_node is not None:
                nearest_node.activated = not nearest_node.activated


        elif key in [Qt.Key_F, Qt.Key_G, Qt.Key_H, Qt.Key_J, Qt.Key_K]:


            keys = [Qt.Key_F, Qt.Key_G, Qt.Key_H, Qt.Key_J, Qt.Key_K]
            attrs = [
                'show_pullling_sum',
                'show_pushing_sum',
                'show_pulling_list',
                'show_pushing_list',
                'show_all_sum',
            ]
            # toggle corresponding attribute
            for _key, attr_name in zip(keys, attrs):
                if _key == key: 
                    value = not getattr(PluginNodeEditor, attr_name)
                    setattr(PluginNodeEditor, attr_name, value)
                    status = 'on' if value else 'off'
                    content = attr_name[len('show_'):].replace('_', ' ')
                    s = f'{content} {status}'
                    board_widget.show_center_label(s)
                    break


    @classmethod
    def status(cls):
        if cls.op_state == cls.OPERATION_REMOVE:
            st = 'removing'
        elif cls.op_state == cls.OPERATION_ADD:
            st = 'adding'
        else:
            st = ''
        if st:
            if cls.type_state == cls.TYPE_NODE:
                st += ' node'
            elif cls.type_state == cls.TYPE_EDGE:
                st += ' edge'

        return st


    @staticmethod
    def find_nearest_node():
        cursor_pos = board_widget.mapFromGlobal(QCursor.pos())
        nodes = []
        for item in widget.scene.items():
            if isinstance(item, Node) and not item.excluded:
                nodes.append(item)
        if not nodes:
            return None
        def min_dist(x):
            return QVector2D(x.scenePos() - cursor_pos).length()
        return min(nodes, key=min_dist)

    @staticmethod
    def find_nearest_edge():
        cursor_pos = board_widget.mapFromGlobal(QCursor.pos())
        edges = []
        for item in widget.scene.items():
            if isinstance(item, Edge):
                edges.append(item)
        if not edges:
            return None
        def min_dist(x):
            a = board_widget.board_MapToViewport(x.sourcePoint)
            b = board_widget.board_MapToViewport(x.destPoint)
            c = (a + b)/2.0
            return QVector2D(c - cursor_pos).length()
        return min(edges, key=min_dist)

    @staticmethod
    def find_node_under_mouse(event):
        cursor_pos = event.pos()
        for item in widget.scene.items():
            if isinstance(item, Node):
                point = item.scenePos()
                rect = build_rect_from_point(board_widget, point)
                if rect.contains(cursor_pos):
                    return item
        return None




def board_MapRectToViewport(self, rect):
    return QRectF(
        self.board_MapToViewport(rect.topLeft()),
        self.board_MapToViewport(rect.bottomRight())
    )

def get_plugin_data_filepath(self):
    return self.get_user_data_filepath('elastiques_nodes.data.txt')

def paintEvent(self, painter, event):
    self.board_draw_main_default(painter, event)

    painter.save()
    pen = QPen(Qt.black, 1)
    painter.setPen(pen)
    rect = QRectF(self.rect())
    painter.save()
    widget.drawBackground(painter, rect)
    painter.restore()

    painter.save()
    painter.setPen(QPen(Qt.black, 1, Qt.DashLine))
    if len(PluginNodeEditor.magazin) == 1:
        curpos = self.mapFromGlobal(QCursor().pos())
        m1_node = PluginNodeEditor.magazin[0]
        _node = PluginNodeEditor.find_nearest_node()
        painter.drawLine(_node.scenePos(), m1_node.scenePos())
    painter.restore()

    for item in widget.scene.items():
        if isinstance(item, Node):
            if PluginNodeEditor.near_mouse_node is item:
                painter.setBrush(QBrush(Qt.green))
            elif item.activated:
                painter.setBrush(QBrush(Qt.red))
            else:
                painter.setBrush(QBrush(Qt.gray))
            rect = QRectF(0, 0, 20, 20)
            rect.moveCenter(item.scenePos())
            painter.drawEllipse(rect)


    for item in widget.scene.items():
        if isinstance(item, Edge):
            item.adjust()
            # print(item.destPoint, item.sourcePoint)
            item._sourcePoint = item.sourcePoint
            item._destPoint = item.destPoint
            item.sourcePoint = board_widget.board_MapToViewport(item.sourcePoint)
            item.destPoint = board_widget.board_MapToViewport(item.destPoint)
            item.paint(painter, None, None)
            item.sourcePoint = item._sourcePoint
            item.destPoint = item._destPoint

            if PluginNodeEditor.near_mouse_edge is item:
                a = self.board_MapToViewport(item.destPoint)
                b = self.board_MapToViewport(item.sourcePoint)
                pos = (a + b) / 2.0
                painter.save()
                painter.setBrush(QBrush(Qt.blue))
                rect = QRectF(0, 0, 20, 20)
                rect.moveCenter(pos)
                painter.drawEllipse(rect)
                painter.restore()

    painter.setPen(QPen(Qt.black, 1))

    pos = self.mapFromGlobal(QCursor().pos())
    painter.drawText(pos, PluginNodeEditor.status())

    painter.restore()

def get_pixels_in_radius_unit(self):
    CONST = 10
    return CONST*max(self.canvas_scale_x, self.canvas_scale_y)
    # return CONST

def build_rect_from_point(self, point, r=1.0):
    offset = QPointF(get_pixels_in_radius_unit(self)*r, get_pixels_in_radius_unit(self)*r)
    return QRectF(point-offset, point+offset)

def mousePressEvent(self, event):
    PluginNodeEditor.drag_node = node = PluginNodeEditor.find_node_under_mouse(event)
    if node is not None:
        PluginNodeEditor.start_pos = event.pos()
        PluginNodeEditor.oldpos = QPointF(node.pos())

    if not PluginNodeEditor.drag_node:
        self.board_mousePressEventDefault(event)
    self.update()

def mouseMoveEvent(self, event):
    if PluginNodeEditor.drag_node is not None:
        delta = QPointF(PluginNodeEditor.start_pos - event.pos())
        delta.setX(delta.x()/self.canvas_scale_x)
        delta.setY(delta.y()/self.canvas_scale_y)
        PluginNodeEditor.drag_node.setPos(PluginNodeEditor.oldpos - delta)

    else:
        self.board_mouseMoveEventDefault(event)
        PluginNodeEditor.near_mouse_node = PluginNodeEditor.find_nearest_node()
        PluginNodeEditor.near_mouse_edge = PluginNodeEditor.find_nearest_edge()

    if not self.corner_buttons_cursor_glitch_fixer():
        is_over_node = PluginNodeEditor.find_node_under_mouse(event) or PluginNodeEditor.drag_node is not None
        if is_over_node:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
    self.update()

def mouseReleaseEvent(self, event):
    if False:
        pass
    else:
        self.board_mouseReleaseEventDefault(event)
    PluginNodeEditor.drag_node = None
    self.update()

def mouseDoubleClickEvent(self, event):
    self.board_mouseDoubleClickEventDefault(event)

def wheelEvent(self, event):
    self.board_wheelEventDefault(event)

def contextMenu(self, event, contextMenu, checkboxes):
    self.board_contextMenuDefault(event, contextMenu, checkboxes)

def keyPressEvent(self, event):
    key = event.key()
    if False:
        pass
    elif key in [Qt.Key_V, Qt.Key_E, Qt.Key_T, Qt.Key_A, Qt.Key_F, Qt.Key_G, Qt.Key_H, Qt.Key_J, Qt.Key_K]:
        if not event.isAutoRepeat():
            PluginNodeEditor.change_editing_state(key, self)
    else:
        widget.keyPressEvent(event)

def keyReleaseEvent(self, event):
    key = event.key()
    if False:
        pass
    elif key in [Qt.Key_V, Qt.Key_E, Qt.Key_T, Qt.Key_A, Qt.Key_F, Qt.Key_G, Qt.Key_H, Qt.Key_J, Qt.Key_K]:
        pass
    else:
        self.board_keyReleaseEventDefault(event)

def dragEnterEvent(self, event):
    self.board_dragEnterEventDefault(event)

def dragMoveEvent(self, event):
    self.board_dragMoveEventDefault(event)

def dropEvent(self, event):
    self.board_dropEventDefault(event)

def getBoardFilepath(self):
    return self.board_getBoardFilepathDefault()

def dumpNonAutoSerialized(self, data):
    return self.board_dumpNonAutoSerializedDefault(data)

def loadNonAutoSerialized(self, data):
    return self.board_loadNonAutoSerializedDefault(data)


def preparePluginBoard(self, plugin_info):
    global widget, board_widget
    board_widget = self
    widget = GraphWidget(None)

    # centering viewport
    self.canvas_origin += self.rect().center() - self.canvas_origin
    self.update()


def register(board_obj, plugin_info):

    plugin_info.name = 'ELASTIQUES NODES PLUGIN'

    # plugin_info.add_to_menu = False

    plugin_info.preparePluginBoard = preparePluginBoard

    plugin_info.paintEvent = paintEvent

    plugin_info.mousePressEvent = mousePressEvent
    plugin_info.mouseMoveEvent = mouseMoveEvent
    plugin_info.mouseReleaseEvent = mouseReleaseEvent

    plugin_info.mouseDoubleClickEvent = mouseDoubleClickEvent

    plugin_info.keyPressEvent = keyPressEvent
    plugin_info.keyReleaseEvent = keyReleaseEvent

    plugin_info.wheelEvent = wheelEvent
    plugin_info.contextMenu = contextMenu

    plugin_info.dragEnterEvent = dragEnterEvent
    plugin_info.dragMoveEvent = dragMoveEvent
    plugin_info.dropEvent = dropEvent

    plugin_info.getBoardFilepath = getBoardFilepath

    plugin_info.dumpNonAutoSerialized = dumpNonAutoSerialized
    plugin_info.loadNonAutoSerialized = loadNonAutoSerialized









def main():
    app = QApplication(sys.argv)
    widget = GraphWidget(None)
    mainWindow = QMainWindow()
    mainWindow.setCentralWidget(widget)

    mainWindow.show()
    app.exec()

if __name__ == '__main__':
    if RUN_AS_STANDALONE_PYQT_APP:
        # Standalone PyQt Version
        main()
    else:
        # Boards Plugin Version
        subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw", "-board", os.path.basename(__file__)])
        sys.exit()



