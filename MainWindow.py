import sys
import os
from PyQt5.QtWidgets import QVBoxLayout,QMessageBox,QProgressBar
from PyQt5 import QtWidgets, uic, QtCore, QtGui
import tempfile
from alive_progress import alive_bar
from multiprocessing import Process, Queue
import math
import shutil

file_types = {
'Images': ['.apng','.png','.avif','.gif','.jpg','.jpeg','.jfif','.pjpeg','.pjp','.svg','.webp','.bmp','.ico','.cur','.tif','.tiff','.icns','.ai','.ps','.psd','.scr'],
'Documents': ['.doc','.docx','.odt','.pdf','.rtf','.tex','.txt','.wpd'],
'Videos': ['.3g2','.3gp','.avi','.flv','.h264','.m4v','.mkv','.mov','.mp4','.mpg','.mpeg','.rm','.swf','.vob','.webm','.wmv'],
'Spreadsheets': ['.ods','.xls','.xlsm','.xlsx'],
'Windows-related': ['.bat','.com','.exe','.gadget','.msi','.wsf','.bak','.cab','.cfg','.cpl','.cur','.dll','.dmp','.drv','.ini','.ink','.msi','.sys','.tmp'],
'Programming': ['.apk','.c','.cgi','.pl','.class','.cpp','.cs','.h','.jar','.java','.php','.py','.sh','.swift','.vb','.asp','.aspx','.cer','.cfm','.cgi','.css','.htm','.html','.js','.jsp','.part','.php','.rss','.xhtml'],
'Presentation': ['.key','.odp','.pps','.ppt','.pptx'],
'Fonts': ['.fnt','.fon','.otf','.ttf'],
'Email': ['.email','.eml','.emlx','.msg','.oft','.ost','.pst','.vcf'],
'Database': ['.csv','.dat','.db','.dbf','.log','.mdb','.sav','.sql','.tar','.xml'],
'Disc and Media': ['.bin','.dmg','.iso','.toast','.vcd'],
'Compressed': ['.7z','.arj','.deb','.pkg','.rar','.rpm','.tar','.gz','.z','.zip'],
'Audio': ['.aif','.cda','.mid','.midi','.mp3','.mpa','.ogg','.wav','.wma','.wpl'],
'Others': []}

def showDialog(msg):
    msgBox = QMessageBox()
    msgBox.setIcon(QMessageBox.Information)
    msgBox.setText(msg)
    msgBox.setWindowTitle("Warning")
    msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    returnValue = msgBox.exec()
    return returnValue


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("mainGUI.ui", self)
        self.pbar = PopUpProgressB(self)
        self.pbar.setWindowModality(QtCore.Qt.ApplicationModal)
        self.ui.clean.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(1))
        self.ui.organize.clicked.connect(self.organizeFiles)
        self.ui.temp.clicked.connect(lambda: self.deleteTempFiles(1))
        self.ui.choose.clicked.connect(lambda: self.deleteTempFiles(2))
        self.queue = Queue()  # Create a Queue for inter-process communication
        self.progress = [0]

    def organizeFiles(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')
        try:
            os.listdir(folder)
        except:
            QMessageBox.warning(self, "Error", "Please select a valid folder")
            return
        else:
            for name in file_types.keys():
                newFolder = os.path.join(folder,name)
                try:
                    os.makedirs(newFolder)
                except:
                    pass
        
        for filename in os.listdir(folder):
            found = False
            path = os.path.join(folder,filename)
            if os.path.isfile(path):
                file_extension = os.path.splitext(filename)[1].lower()
                for i in file_types.keys():
                    if file_extension in file_types[i]:
                        shutil.move(path, os.path.join(folder,i))
                        found = True
                        break
                if not found:
                    shutil.move(path, os.path.join(folder,'Others'))



    def deleteTempFiles(self, mode):
        if mode == 1:
            self.folder = tempfile.gettempdir()
        elif mode == 2:
            self.folder = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')
        folder = self.folder
        try:
            os.listdir(folder)
        except:
            QMessageBox.warning(self, "Error", "Please select a valid folder")
            return
        else:
            response = showDialog(f'Are you sure about deleting every file in {folder}?')
            if response == QMessageBox.Ok:
                pass
            elif response == QMessageBox.Cancel:
                return
            self.pbar.show()

            # Start the deletion process
            self.tempdir = tempfile.TemporaryDirectory()
            print(self.tempdir.name)
            temp_file_path = os.path.join(self.tempdir.name, 'temp_file.txt')
            with open(temp_file_path, 'w') as f:
                f.write('0')
            process = Process(target=self.deletionThread, args=(folder, temp_file_path))
            process.start()
            # Start monitoring the queue for progress updates
            self.monitorQueue()

    def monitorQueue(self):
        """Poll the queue for updates from the process and update the progress bar"""
        temp_file_path = os.path.join(self.tempdir.name, 'temp_file.txt')
        f = open(temp_file_path,'r')
        try:
            prog = int(f.read())
        except:
            pass
        else:
            # print(f'received: {prog}')
            if prog == 100:
                self.pbar.updateProgress(prog)
                self.pbar.completed()
                f.close()
                self.tempdir.cleanup()
                self.tempdir = ''
                return
            else:
                self.pbar.updateProgress(prog)
        f.close()
        # Continue polling the queue
        QtCore.QTimer.singleShot(100, self.monitorQueue)

    @staticmethod
    def deletionThread(folder, tempfoname):
        """Function that runs in a separate process to delete files and update progress"""
        if folder != '':
            files = os.listdir(folder)
            total_files = len(files)
            with alive_bar(len(os.listdir(folder))) as bar:
                for i, filename in enumerate(files):
                    file_path = os.path.join(folder, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                        	os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print(f'Failed to delete {file_path}. Reason: {e}')
                    prog = math.floor((i + 1) / total_files * 100)
                    f = open(tempfoname, 'w')
                    f.write(str(prog))
                    f.close()
                    bar()
            # f = open(tempfoname, 'w')
            # f.write(str(100))
            # f.close()


class PopUpProgressB(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setWindowTitle('Loading...')
        self.setGeometry(100, 100, 300, 50)
        self.layout = QVBoxLayout()
        self.progress = QProgressBar()
        self.layout.addWidget(self.progress)
        self.setLayout(self.layout)
        self.progress.setValue(0)

    def updateProgress(self, value):
        self.progress.setValue(value)

    def completed(self):
        self.close()