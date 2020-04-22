from kiwoom.kiwoom_prac import *


import sys
from PyQt5.QtWidgets import *

class UI_class():
    def __init__(self):
        print("is UI_class")

        #python 위치참조?
        self.app = QApplication(sys.argv)

        self.kiwoom_prac = Kiwoom()


        #주식시장 장열린동안 프로그램이 꺼지지 않고 Keep Running 하게 해주는 Event-Loop
        self.app.exec_()
