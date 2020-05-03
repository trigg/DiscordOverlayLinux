#!/usr/bin/python
import sys
import os
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtWebEngineWidgets import *
from pathlib import Path

os.chdir(Path.home())

def click(event):
    event
fileName = ".discordurl"
url = None
if os.path.isfile(fileName):
    with open(fileName) as file:
        url = file.readline().rstrip()
app=QtWidgets.QApplication(sys.argv)
print ("Using : %s"%(url))
if not url:
    print("Please create the file ~/.discordurl with the URL to show\n\nThis can be obtained from https://streamkit.discord.com/overlay")
    sys.exit(1)
overlay = QWebEngineView()
overlay.page().setBackgroundColor(QtCore.Qt.transparent)
overlay.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
overlay.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
overlay.setWindowFlags(
        QtCore.Qt.X11BypassWindowManagerHint |
        QtCore.Qt.FramelessWindowHint | 
        QtCore.Qt.WindowStaysOnTopHint | 
        QtCore.Qt.WindowTransparentForInput | 
        QtCore.Qt.WindowDoesNotAcceptFocus|
        QtCore.Qt.NoDropShadowWindowHint|
        QtCore.Qt.WindowSystemMenuHint |
        QtCore.Qt.WindowMinimizeButtonHint
        )
overlay.load(QtCore.QUrl(url))


overlay.setStyleSheet("background:transparent;")
overlay.resize(500,1000)
overlay.show()

app.exec_()
