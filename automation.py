from MainWindow import *

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.setWindowTitle('Task Automation Tool')
    window.setWindowIcon(QtGui.QIcon('assets\\icon.png'))
    window.show()
    sys.exit(app.exec_())