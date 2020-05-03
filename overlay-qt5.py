#!/usr/bin/python
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.  
import sys
import os
from configparser import ConfigParser
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWebEngineWidgets import *
from pathlib import Path


class Overlay(QtCore.QObject):
    fileName = ".discordurl"
    configFileName= ".discoverlay.ini"
    url = None

    def main(self):
        # Get Screen dimensions
        screen = app.primaryScreen()
        self.size = screen.size()

        if os.path.isfile(self.fileName):
            with open(self.fileName) as file:
                self.url = file.readline().rstrip()
        if os.path.isfile(self.configFileName):
            config = ConfigParser()
            config.read(self.configFileName)
            self.posXL=int(config.get('main', 'xl'))
            self.posXR=int(config.get('main', 'xr'))
            self.posYT=int(config.get('main', 'yt'))
            self.posYB=int(config.get('main', 'yb'))
        else:
            self.posXL=0
            self.posXR=self.size.width()
            self.posYT=0
            self.posYB=self.size.height()

        self.createOverlay()
        if not self.url:
            self.createSettingsWindow()



    def moveOverlay(self):
        print("%i %i, %i %i" % (self.posXL, self.posYT, self.posXR, self.posYB))
        self.overlay.resize(self.posXR-self.posXL,self.posYB-self.posYT)
        self.overlay.move(self.posXL,self.posYT)

    def on_url(self, url):
        self.overlay.load(QtCore.QUrl(url))
        self.url = url

    @pyqtSlot()
    def save(self):
        config = ConfigParser()
        config.add_section('main')
        config.set('main','xl','%d'%(self.posXL))
        config.set('main','xr','%d'%(self.posXR))
        config.set('main','yt','%d'%(self.posYT))
        config.set('main','yb','%d'%(self.posYB))
        with open(self.configFileName,'w') as file:
            config.write(file)
        with open(self.fileName,'w') as file:
            file.write(self.url)
        self.settings.hide()

    @pyqtSlot()
    def on_click(self):
        self.settingWebView.page().runJavaScript("document.getElementsByClassName('source-url')[0].value;", self.on_url)

    @pyqtSlot()
    def changeValueFL(self):
        self.posXL=self.settingsDistanceFromLeft.value()
        self.moveOverlay()

    @pyqtSlot()
    def changeValueFR(self):
        self.posXR=self.settingsDistanceFromRight.value()
        self.moveOverlay()

    @pyqtSlot()
    def changeValueFT(self):
        self.posYT=self.settingsDistanceFromTop.value()
        self.moveOverlay()

    @pyqtSlot()
    def changeValueFB(self):
        self.posYB=self.settingsDistanceFromBottom.value()
        self.moveOverlay()

    def createSettingsWindow(self):
        self.settings = QtWidgets.QWidget()
        self.settingsbox = QtWidgets.QVBoxLayout()
        self.settingWebView = QWebEngineView()
        self.settingTakeUrl = QtWidgets.QPushButton("Use this overlay")
        self.settingsDistanceFromLeft = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.settingsDistanceFromRight = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.settingsDistanceFromTop = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.settingsDistanceFromBottom = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.settingSave = QtWidgets.QPushButton("Save & Exit")
        
        self.settingTakeUrl.clicked.connect(self.on_click)
        self.settingWebView.load(QtCore.QUrl("https://streamkit.discord.com/overlay"))
        self.settingsDistanceFromLeft.valueChanged[int].connect(self.changeValueFL)
        self.settingsDistanceFromLeft.setMaximum(self.size.width())
        self.settingsDistanceFromLeft.setValue(self.posXL)
        self.settingsDistanceFromRight.valueChanged[int].connect(self.changeValueFR)
        self.settingsDistanceFromRight.setMaximum(self.size.width())
        self.settingsDistanceFromRight.setValue(self.posXR)
        self.settingsDistanceFromTop.valueChanged[int].connect(self.changeValueFT)
        self.settingsDistanceFromTop.setMaximum(self.size.height())
        self.settingsDistanceFromTop.setValue(self.posYT)
        self.settingsDistanceFromBottom.valueChanged[int].connect(self.changeValueFB)
        self.settingsDistanceFromBottom.setMaximum(self.size.height())
        self.settingsDistanceFromBottom.setValue(self.posYB)
        self.settingSave.clicked.connect(self.save)
    
        self.settingsbox.addWidget(self.settingWebView)
        self.settingsbox.addWidget(self.settingTakeUrl)
        self.settingsbox.addWidget(self.settingsDistanceFromLeft)
        self.settingsbox.addWidget(self.settingsDistanceFromRight)
        self.settingsbox.addWidget(self.settingsDistanceFromTop)
        self.settingsbox.addWidget(self.settingsDistanceFromBottom)
        self.settingsbox.addWidget(self.settingSave)
        self.settings.setLayout(self.settingsbox)
        self.settings.showMaximized()


    def createOverlay(self):
        self.overlay = QWebEngineView()
        self.overlay.page().setBackgroundColor(QtCore.Qt.transparent)
        self.overlay.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.overlay.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.overlay.setWindowFlags(
                QtCore.Qt.X11BypassWindowManagerHint |
                QtCore.Qt.FramelessWindowHint | 
                QtCore.Qt.WindowStaysOnTopHint | 
                QtCore.Qt.WindowTransparentForInput | 
                QtCore.Qt.WindowDoesNotAcceptFocus|
                QtCore.Qt.NoDropShadowWindowHint|
                QtCore.Qt.WindowSystemMenuHint |
                QtCore.Qt.WindowMinimizeButtonHint
                )
        self.overlay.load(QtCore.QUrl(self.url))


        self.overlay.setStyleSheet("background:transparent;")
        self.moveOverlay()
        self.overlay.show()

os.chdir(Path.home())
app=QtWidgets.QApplication(sys.argv)
o = Overlay()
o.main()
app.exec_()
