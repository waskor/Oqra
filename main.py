from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
from PyQt5.uic import loadUi
from PyQt5.QtCore import QThread, pyqtSignal

import cv2
import time
import sys
import numpy as np
from PIL import Image

import placeqr as pqr
import generateqr as gqr

time_limit = 100

class External(QThread):

    countchange = pyqtSignal(int)

    def __init__(self, templatefile, linksfile, amount):
        super(External, self).__init__()
        self.templatefile = templatefile
        self.linksfile = linksfile
        self.amount = amount

    def run(self):
        
        self.find_squares(self.templatefile)
        self.place_qr_codes(self.templatefile, self.linksfile, self.amount)

    def find_squares(self, templatefile):

        #global squares_sort
        self.template = cv2.imread(self.templatefile)
        self.squares_list = []
        self.templategray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
        
        self.ret, self.thresh = cv2.threshold(self.templategray,127,255,cv2.THRESH_BINARY_INV)

        self.contours, self.hierarchy = cv2.findContours(self.thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in self.contours:    

            self.x,self.y,self.w,self.h = cv2.boundingRect(c)

            if self.w>80:
                
                self.accuracy = 0.01*cv2.arcLength(c,True)
                self.approx = cv2.approxPolyDP(c,self.accuracy,True)
                self.x,self.y,self.w,self.h = cv2.boundingRect(self.approx)
                cv2.rectangle(self.template,(self.x,self.y),(self.x+self.w,self.y+self.h),255,1)
                self.square = [self.x-2,self.y-2,self.w+4,self.h+4]
                self.squares_list.append(self.square)

        self.squares = np.array(self.squares_list)
        self.ind = np.lexsort((self.squares[:,1],self.squares[:,0])) 
        self.squares_sort = self.squares[self.ind]
        #cv2.imwrite('squares.jpg', template)

    def place_qr_codes(self, templatefile, linksfile, amount):

        count = 0

        self.template_qr = Image.open(self.templatefile)
        gqr.initialise(self.linksfile)
        self.pages = gqr.links.shape[0]//self.squares_sort.shape[0]
        self.page = 0
        self.sq = 0

        for i in range(self.amount):
            count+=100/self.amount
            self.countchange.emit(count)

            if i % self.squares_sort.shape[0] == 0 and i != 0:

                self.fileout = "grollz/stickers/templateqr_{}.png".format(self.page)
                self.template_qr.save(self.fileout)
                self.page += 1
                self.sq = 0

                self.template_qr = Image.open(self.templatefile)

                gqr.generate_qr(i)
                gqr.qrimg = gqr.qrimg.rotate(270)
                gqr.qrimg = gqr.qrimg.resize((self.squares_sort[self.sq,3], self.squares_sort[self.sq,2]))
                
                self.template_qr.paste(gqr.qrimg, (self.squares_sort[self.sq,0], self.squares_sort[self.sq,1])) 

                self.sq = 1

            elif i == (self.amount-1):
                
                gqr.generate_qr(i)
                gqr.qrimg = gqr.qrimg.rotate(270)
                gqr.qrimg = gqr.qrimg.resize((self.squares_sort[self.sq,3], self.squares_sort[self.sq,2]))
                
                self.template_qr.paste(gqr.qrimg, (self.squares_sort[self.sq,0], self.squares_sort[self.sq,1])) 
                self.fileout = "grollz/stickers/templateqr_{}.png".format(self.page)
                self.template_qr.save(self.fileout)
                gqr.links.to_csv("links2.csv")

            else:
                gqr.generate_qr(i)
                gqr.qrimg = gqr.qrimg.rotate(270)
                gqr.qrimg = gqr.qrimg.resize((self.squares_sort[self.sq,3], self.squares_sort[self.sq,2]))
                
                self.template_qr.paste(gqr.qrimg, (self.squares_sort[self.sq,0], self.squares_sort[self.sq,1])) 
                
                self.sq += 1

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("grollz/stiqr.ui",self)
        self.browse1.clicked.connect(self.browsepng)
        self.browse2.clicked.connect(self.browsecsv)
        self.checkboxall.stateChanged.connect(self.checkbox)
        self.checkboxcustom.stateChanged.connect(self.checkbox)
        self.runbutton.clicked.connect(self.execute)
        self.customline.setDisabled(True)
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(100)

        
    def browsepng(self):
        filename = QFileDialog.getOpenFileName(self, 'Load template', "C:/", "PNG Files (*.png)")
        self.browsepath1.setText(filename[0])

        self.templatefile = filename[0]

    def browsecsv(self):
        filename = QFileDialog.getOpenFileName(self, 'Load links', "C:/", "CSV Files (*.csv)")
        self.browsepath2.setText(filename[0])

        self.linksfile = filename[0]

    def checkbox(self, state):
        if state == QtCore.Qt.Checked:
            if self.sender() == self.checkboxall:
                self.checkboxcustom.setChecked(False)
                try:
                    self.linksfile
                except:
                    print('no links')
                else:
                    
                    gqr.initialise(self.linksfile)
                    self.amount = gqr.links.shape[0]
                    print(self.amount)

            if self.sender() == self.checkboxcustom:
                print('custom')
                self.checkboxall.setChecked(False)
                self.customline.setDisabled(False)
        else:
            self.customline.setDisabled(True)

    def onCountChanged(self, value):
        self.progressBar.setValue(value)

    def done(self):
        self.loadingline.setText('Complete.')

    def execute(self):

        self.loadingline.setText('Generating...')

        self.calc = External(self.templatefile, self.linksfile, self.amount)
        self.calc.finished.connect(self.done)
        self.calc.countchange.connect(self.onCountChanged)
        self.calc.start()

        #pqr.main(self.templatefile, self.linksfile, self.amount)
      
if __name__ == "__main__":

    app = QApplication(sys.argv)
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec_())
