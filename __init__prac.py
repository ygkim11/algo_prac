from kiwoom.kiwoom_prac import *
import sys
from PyQt5.QtWidgets import *

class Main():
    def __init__(self):
        print('실행할 메인 클래스')


        #python 위치참조?
        self.app = QApplication(sys.argv)

        self.login = Kiwoom()

if __name__ == '__main__':
    Main()


