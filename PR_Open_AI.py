

import sys, time, os
import numpy as np
import cv2
from PyQt5 import QtCore, QtGui, QtWidgets
from Ui_main import Ui_MainWindow

class webcam(QtCore.QThread):   
    rawdata = QtCore.pyqtSignal(np.ndarray) 
    def __init__(self, parent=None):
        rawdata = QtCore.pyqtSignal(np.ndarray)
        super().__init__(parent)
        
        self.camera = cv2.VideoCapture(0)
        self.running = False
        self.mode = 0
        self.save = False
        if self.camera is None or not self.camera.isOpened():
            self.connect = False          
        else:
            self.connect = True
    def run(self):
        while self.running and self.connect:
            ret, self.orgImg = self.camera.read()  
            if ret:
                if self.mode == 0:
                    img = self.orgImg.copy()
                    cv2.putText(img, 'orgin', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1 , (0, 255, 255), 1, cv2.LINE_AA)
                    self.rawdata.emit(img)
                elif self.mode == 1:
                    aiimg = self.imgProcess()
                    cv2.putText(aiimg, 'AI', (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1 , (0, 255, 255), 1, cv2.LINE_AA)
                    self.rawdata.emit(aiimg)
                else:
                    self.rawdata.emit(self.orgImg) 
            else:
                print("Warning!!!")
                self.connect = False
    def imgProcess(self):
        clone = self.orgImg.copy()
        img = cv2.cvtColor(clone, cv2.COLOR_BGR2GRAY) 
        img = cv2.medianBlur(img, 7) 
        img = cv2.Canny(img, 36, 36) 
        cnts, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(clone, cnts, -1, (0, 255, 0), 2)
        return clone
    def open(self):
        if self.connect:
            self.running = True
    def stop(self):
        if self.connect:
            self.running = False
    def saveImg(self, path):
        self.save = True
        if self.save:
            cv2.imwrite(path + '.jpg', self.orgImg)
            self.save = False
    def close(self):
        if self.connect:
            self.running = False
            time.sleep(1)
            self.camera.release()
    def setmode(self, mode):
        self.mode = mode
    def getmode(self):
        return self.mode

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):  
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)        
        # self.viewData.setScaledContents(True)
        self.viewData.setMouseTracking(True)
        # self.viewData.mouseMoveEvent = self.mousemoveEvent
        # self.viewData.mousePressEvent = self.mousepressEvent
        self.frame = QtWidgets.QGraphicsPixmapItem()
        self.line = QtWidgets.QGraphicsLineItem()
        self.line.setPen(QtCore.Qt.yellow)
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addItem(self.frame)
        self.scene.addItem(self.line)
        self.scene.mouseMoveEvent = self.mousemoveEvent
        self.scene.mousePressEvent = self.mousepressEvent
        self.lines = []
        self.view_x = self.view.horizontalScrollBar()
        self.view_y = self.view.verticalScrollBar()
        self.start_point = QtCore.QPointF()
        self.end_point = QtCore.QPointF()
        self.drawing_line = False
        
        self.view.installEventFilter(self)
        self.last_move_x = 0
        self.last_move_y = 0
        self.frame_num = 0
        self.useCam = webcam()
        if self.useCam.connect:
            self.debugBar('camera connect!!')
            self.useCam.rawdata.connect(self.getFrame)
            self.btnCamOpen.setEnabled(True)
        else:
            self.debugBar('camera disconnect!!!')
            self.btnCamOpen.setEnabled(False)
        self.btnCamOpen.clicked.connect(self.openCam)
        self.btnCamStop.clicked.connect(self.stopCam)
        self.btnSave.clicked.connect(self.saveCam)
        self.btnCamAI.clicked.connect(self.ai)
        # self.btnLine.clicked.connect(self.line)
        
        self.btnCamStop.setEnabled(False)
        self.btnCamAI.setEnabled(False)
        
    

    def getFrame(self, data):
        self.showData(data)
    def openCam(self):
        if self.useCam.connect:
            self.useCam.open()
            self.useCam.start()
            self.btnCamOpen.setEnabled(False)
            self.btnCamAI.setEnabled(True)
            self.btnCamStop.setEnabled(True)
            self.cbViewROI.setEnabled(True)
    def stopCam(self):
        if self.useCam.connect:
            self.useCam.stop()
            # self.useCam.start()
            self.btnCamOpen.setEnabled(True)
            self.btnCamStop.setEnabled(False)
            self.btnCamAI.setEnabled(False)
            self.cbViewROI.setEnabled(False)
    def ai(self):
        self.useCam.setmode(1)
    # def line(self):
    #     self.useCam.setmode(0)
    def saveCam(self):
        self.useCam.saveImg(self.txtLot.text())
    def mousemoveEvent(self, event):
        if self.drawing_line:
            self.end_point = event.scenePos()
            
            
            # self.scene.addItem(self.drawing_line)
        # x = event.pos().x()
        # y = event.pos().y() 
        # self.debugBar('Pos: %, %d ' % x % y)
    def mousepressEvent(self, event):
        self.drawing_line = not self.drawing_line
        if self.drawing_line:
            self.start_point = event.scenePos()
            print(self.start_point.x(), self.start_point.y())
            self.end_point = self.start_point
            
            
            # self.viewData.setScene(self.scene)
        else:
            self.end_point = event.scenePos()
            print(self.end_point.x(), self.end_point.y())
            self.lines.append(self.line)
    def showData(self, img):
        self.Ny, self.Nx, _ = img.shape
        img_new = np.zeros_like(img)
        img_new[...,0] = img[...,2]
        img_new[...,1] = img[...,1]
        img_new[...,2] = img[...,0]
        img = img_new
        qimg = QtGui.QImage(img.data, self.Nx, self.Ny, QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(qimg)
        # item = QtWidgets.QGraphicsPixmapItem(pix) 
        self.frame.setPixmap(pix)
        self.line.setLine(self.start_point.x(), self.start_point.y(), self.end_point.x(), self.end_point.y())
        # self.line = QtWidgets.QGraphicsLineItem(self.start_point.x(), self.start_point.y(), self.end_point.x(), self.end_point.y())
               
        # self.scene.addItem(item)
        # self.scene.addItem(self.line)        
        # if self.drawing_line is not None:
        # self.lines_drawing()
           
        
        # if self.drawing_line is not None:
        #     self.scene.addItem(self.drawing_line)
        self.viewData.setScene(self.scene)
        # self.viewData.setScaledContents(True)
        # self.viewData.setPixmap(QtGui.QPixmap.fromImage(qimg))
        if self.cbViewROI.currentIndex() == 0: roi_rate = 0.5
        elif self.cbViewROI.currentIndex() == 1: roi_rate = 0.75
        elif self.cbViewROI.currentIndex() == 2: roi_rate = 1
        elif self.cbViewROI.currentIndex() == 3: roi_rate = 1.25
        elif self.cbViewROI.currentIndex() == 4: roi_rate = 1.5
        else: pass
        self.viewForm.setMinimumSize(int(self.Nx*roi_rate), int(self.Ny*roi_rate))
        self.viewForm.setMaximumSize(int(self.Nx*roi_rate), int(self.Ny*roi_rate))
        self.viewData.setMinimumSize(int(self.Nx*roi_rate), int(self.Ny*roi_rate))
        self.viewData.setMaximumSize(int(self.Nx*roi_rate), int(self.Ny*roi_rate))
        if self.frame_num == 0:
            self.time_start = time.time()
        if self.frame_num >= 0:
            self.frame_num += 1
            self.t_total = time.time() - self.time_start
            if self.frame_num % 100 == 0:
                self.frame_rate = float(self.frame_num) / self.t_total
                self.debugBar('FPS: %0.3f frames/sec' % self.frame_rate)
    def lines_drawing(self):
        for aline in self.lines:
            self.scene.addItem(aline)
            aline.setPen(QtCore.Qt.yellow)
    def eventFilter(self, source, event):
        if source == self.view:
            if event.type() == QtCore.QEvent.MouseMove:
                if self.last_move_x == 0 or self.last_move_y == 0:
                    self.last_move_x = event.pos().x()
                    self.last_move_y = event.pos().y()
                    
                distance_x = self.last_move_x - event.pos().x()
                distance_y = self.last_move_y - event.pos().y()
                self.view_x.setValue(self.view_x.value() + distance_x)
                self.view_y.setValue(self.view_y.value() + distance_y)
                self.last_move_x = event.pos().x()
                self.last_move_y = event.pos().y()            
                
            elif event.type() == QtCore.QEvent.MouseButtonRelease:
                self.last_move_x = 0
                self.last_move_y = 0
            return QtWidgets.QWidget.eventFilter(self, source, event)
        
    def closeEvent(self, event):
        if self.useCam.running:
            self.useCam.close()
            self.useCam.terminate()
        QtWidgets.QApplication.closeAllWindows()
        
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Q:
            if self.useCam.running:
                self.useCam.close()
                time.sleep(1)
                self.ProcessCam.terminate()
            QtWidgets.QApplication.closeAllWindows()
            return QtWidgets.QWidget.eventFilter(self, source, event)
        
    def debugBar(self, msg):
        self.statusbar.showMessage(str(msg), 5000)
if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
    

