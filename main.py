from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QDialog
from PyQt5.uic import loadUi
from PyQt5.QtCore import QThread, pyqtSignal

import cv2
import time
import sys
import fitz
import numpy as np
from PIL import Image

from about import Ui_Dialog

import generateqr as gqr

class External(QThread):

    countchange = pyqtSignal(int)

    def __init__(self, templatefile, linksfile, amount):
        super(External, self).__init__()
        self.templatefile = templatefile
        self.linksfile = linksfile
        self.amount = amount

    def run(self):
        
        start_time = time.time()
        self.find_squares(self.templatefile)
        self.place_qr_codes(self.templatefile, self.linksfile, self.amount)
        print("--- %s seconds ---" % (time.time() - start_time))

    def find_squares(self, templatefile):

        self.squares_list = []

        self.template_pdf = fitz.open(templatefile)
        self.pdfpage = self.template_pdf[0]

        self.pix = self.pdfpage.getPixmap(matrix = fitz.Matrix(5, 5))
        self.pix.writePNG('pdfpng.png')

        self.template_img = cv2.imread('pdfpng.png')
        self.height_img, self.width_img, self.channels = self.template_img.shape
        
        
        self.width_pdf = self.pdfpage.MediaBox[2]
        self.height_pdf = self.pdfpage.MediaBox[3]

        self.ratio_pdf = self.width_img/self.width_pdf
                
        self.templategray = cv2.cvtColor(self.template_img, cv2.COLOR_BGR2GRAY)
        
        self.ret, self.thresh = cv2.threshold(self.templategray,140,255,cv2.THRESH_BINARY_INV)
        #self.thresh = cv2.adaptiveThreshold(self.templategray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,11,2)
        #cv2.imwrite('thresh.jpg',self.thresh)
        self.contours, self.hierarchy = cv2.findContours(self.thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for c in self.contours:    

            self.x,self.y,self.w,self.h = cv2.boundingRect(c)
            self.ratio = self.w/self.h

            if min(1.01,0.99) < self.ratio < max(1.01,0.99) and self.width_img/self.w<24:
                
                self.accuracy = 0.01*cv2.arcLength(c,True)
                self.approx = cv2.approxPolyDP(c,self.accuracy,True)
                self.x,self.y,self.w,self.h = cv2.boundingRect(self.approx)
                #cv2.rectangle(self.template_img,(self.x,self.y),(self.x+self.w,self.y+self.h),255,1)
                self.square = [self.x-1,self.y-1,self.w+2,self.h+2]
                self.squares_list.append(self.square)

        self.squares = np.array(self.squares_list)
        self.ind = np.lexsort((self.squares[:,1],self.squares[:,0])) 
        self.squares_sort = self.squares[self.ind]

        self.squares_sort = self.squares_sort[:,:]/self.ratio_pdf
        

    def place_qr_codes(self, templatefile, linksfile, amount):

        count = 0
        gqr.initialise(self.linksfile)
        self.pages = gqr.links.shape[0]//self.squares_sort.shape[0]
        self.page = 0
        self.sq = 0

        if templatefile.endswith('.pdf'):
            self.template_pdf = fitz.open(templatefile)
            #self.template_pdf.set_layer(-1, on=[244])
            
            self.pdfpage = self.template_pdf[0]

            for i in range(self.amount):
                count+=101/self.amount
                self.countchange.emit(int(count))

                if i % self.squares_sort.shape[0] == 0 and i != 0:

                    
                    #for item in self.template_pdf.layer_configs(): print(item)
                    #self.template_pdf.set_layer_config(-1,as_default=True)
                    # self.pdfpage.cleanContents()  # clean the syntax, join multiple contetns objects
                    # xref = self.pdfpage.getContents()[0]  # get xref of resulting single object
                    # cont_lines = self.template_pdf.xrefStream(xref).splitlines()  # read it, break up into lines
                    # for k in range(len(cont_lines)):
                    #     if cont_lines[k].startswith((b"/OC", b"EMC")):
                    #         cont_lines[k] = b""
                    # cont = b"\n".join(cont_lines)
                    # self.template_pdf.updateStream(xref, cont)
                    #self.template_pdf.set_layer(-1, on=[244])

                    self.fileout = str(mainwindow.outputfolder) + "/page{}.pdf".format(self.page+1)
                    self.template_pdf.save(self.fileout)
                    self.page += 1
                    self.sq = 0

                    self.template_pdf = fitz.open(self.templatefile)
                    self.pdfpage = self.template_pdf[0]

                    gqr.generate_qr(i)
                    self.qr_rectangle = fitz.Rect(self.squares_sort[self.sq,0],self.squares_sort[self.sq,1],self.squares_sort[self.sq,0]+self.squares_sort[self.sq,2],self.squares_sort[self.sq,1]+self.squares_sort[self.sq,3])
                    self.pix = fitz.Pixmap(gqr.buf)
                    self.pdfpage.insertImage(self.qr_rectangle, pixmap = self.pix, overlay=True)
                    #gqr.qrimg = gqr.qrimg.rotate(270)
                    #gqr.qrimg = gqr.qrimg.resize((self.squares_sort[self.sq,3], self.squares_sort[self.sq,2] 

                    self.sq = 1

                elif i == (self.amount-1):
                    
                    gqr.generate_qr(i)
                    self.qr_rectangle = fitz.Rect(self.squares_sort[self.sq,0],self.squares_sort[self.sq,1],self.squares_sort[self.sq,0]+self.squares_sort[self.sq,2],self.squares_sort[self.sq,1]+self.squares_sort[self.sq,3])
                    self.pix = fitz.Pixmap(gqr.buf)
                    self.pdfpage.insertImage(self.qr_rectangle, pixmap = self.pix, overlay=True)

                    self.fileout = str(mainwindow.outputfolder) + "/page{}.pdf".format(self.page+1)
                    self.template_pdf.save(self.fileout)

                    self.links_unused = gqr.links[gqr.links['status'] == 'unused'] 
                    self.links_unused.to_csv('unused_links.csv',index = False)
                    gqr.links.to_csv('all_links.csv', index = False)

                else:

                    gqr.generate_qr(i)
                    self.qr_rectangle = fitz.Rect(self.squares_sort[self.sq,0],self.squares_sort[self.sq,1],self.squares_sort[self.sq,0]+self.squares_sort[self.sq,2],self.squares_sort[self.sq,1]+self.squares_sort[self.sq,3])
                    self.pix = fitz.Pixmap(gqr.buf)
                    self.pdfpage.insertImage(self.qr_rectangle, pixmap = self.pix, overlay=True)
                    #gqr.qrimg = gqr.qrimg.rotate(270)
                    #gqr.qrimg = gqr.qrimg.resize((self.squares_sort[self.sq,3], self.squares_sort[self.sq,2] 

                    self.sq += 1

                
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("oqra.ui",self)
        self.browse1.clicked.connect(self.browsepng)
        self.browse2.clicked.connect(self.browsecsv)
        self.browse3.clicked.connect(self.browsefolder)
        self.checkboxall.stateChanged.connect(self.checkbox)
        self.checkboxcustom.stateChanged.connect(self.checkbox)
        self.runbutton.clicked.connect(self.execute)
        self.resetbutton.clicked.connect(self.reset)
        self.customline.setDisabled(True)
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(100)
        self.checkboxall.setDisabled(True)
        self.checkboxcustom.setDisabled(True)
        self.actionAbout.triggered.connect(self.openabout)
        self.loadingline.setText('Welcome to Oqra v1.0.0')

    def openabout(self):
        self.aboutdialog = QDialog()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self.aboutdialog)
        self.aboutdialog.show()
         
    def reset(self):
        self.templatefile = None
        self.linksfile = None
        self.outputfolder = None
        self.amount = None
        self.browsepath1.setText('')
        self.browsepath2.setText('')
        self.browsepath3.setText('')
        self.checkboxall.setDisabled(True)
        self.checkboxcustom.setDisabled(True)
        self.checkboxall.setChecked(False)
        self.checkboxcustom.setChecked(False)
        self.progressBar.setValue(0)
        self.loadingline.setText('')
        self.customline.setText('')
    
    def browsepng(self):

        filename = QFileDialog.getOpenFileName(self, 'Load template', "C:/", "Template files (*.pdf)")

        if filename[0].endswith('.pdf'):

            self.browsepath1.setText(filename[0])
            self.templatefile = filename[0]
            self.checkboxall.setDisabled(False)
            self.checkboxcustom.setDisabled(False)
            self.loadingline.setText('')
        else:
            self.loadingline.setText('Please select a PDF template.')

    def browsecsv(self):

        filename = QFileDialog.getOpenFileName(self, 'Load links', "C:/", "CSV Files (*.csv)")

        if filename[0].endswith('.csv'):

            self.browsepath2.setText(filename[0])
            self.linksfile = filename[0]
            self.checkboxall.setDisabled(False)
            self.checkboxcustom.setDisabled(False)
            self.loadingline.setText('')
        else:
            self.loadingline.setText('Please select a correct links file.')


    def browsefolder(self):
        filename = QFileDialog.getExistingDirectory(self, 'Output folder', "C:/", QFileDialog.ShowDirsOnly)
        self.browsepath3.setText(filename)
        self.outputfolder = filename

        
    def checkbox(self, state):
        if state == QtCore.Qt.Checked:
            if self.sender() == self.checkboxall:

                self.checkboxcustom.setChecked(False)
                self.customline.setText('')

                try:
                    self.linksfile
                except:
                    self.loadingline.setText('Please set links file first.')
                    self.checkboxall.setChecked(False)

                else:
                    
                    gqr.initialise(self.linksfile)
                    self.amount = gqr.links.shape[0]
 
            if self.sender() == self.checkboxcustom:

                self.checkboxall.setChecked(False)

                try:
                    self.linksfile
                except:
                    self.loadingline.setText('Please set links file first.')
                    self.checkboxcustom.setChecked(False)
                else:
                    self.customline.setDisabled(False)

        else:
            self.customline.setDisabled(True)

    def progressbar(self, value):
        self.progressBar.setValue(value)

    def done(self):

        self.timetaken = (time.time() - self.start_time)

        if int(self.timetaken) > 60:
            self.minutes = int(self.timetaken/60)
            self.seconds = int(self.timetaken%60)

            self.minstring = str(self.minutes) + ' minute and ' if self.minutes == 1 else str(self.minutes) + ' minutes and '
            self.secstring = str(self.seconds) + ' second. ' if self.seconds == 1 else str(self.seconds) + ' seconds. '
           
            self.donetext = 'Complete! Time taken: ' + self.minstring + self.secstring
            self.loadingline.setText(self.donetext)
        else:
            self.timetaken = "{:.2f}".format(self.timetaken)
            self.donetext = 'Complete! Time taken: ' + str(self.timetaken) + ' seconds'
            self.loadingline.setText(self.donetext)

        self.runbutton.setDisabled(False)

    def execute(self):

        if not self.checkboxcustom.isChecked() and not self.checkboxall.isChecked():
            self.loadingline.setText('Please select the amount of links.')

        if self.checkboxcustom.isChecked():
            self.amount = int(self.customline.text())

        try:
            self.templatefile
        except:
            self.loadingline.setText('Please select template file.')
        
        else:

            try:
                self.linksfile
            except:
                self.loadingline.setText('Please select link file.')

            else:

                try:
                    self.outputfolder
                except:
                    self.loadingline.setText('Please select output folder.')

                else:
                    
                    try:
                        self.amount
                    except:
                        self.loadingline.setText('Please select amount of links.')
                    
                    else:
                        
                        self.runbutton.setDisabled(True)
                        self.loadingline.setText('Generating...')
                        self.start_time = time.time()
                        self.calc = External(self.templatefile, self.linksfile, self.amount)
                        self.calc.finished.connect(self.done)
                        self.calc.countchange.connect(self.progressbar)
                        self.calc.start()


if __name__ == "__main__":

    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec_())
