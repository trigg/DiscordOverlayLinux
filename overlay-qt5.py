#!/usr/bin/python3
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
import base64
from configparser import ConfigParser
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWebEngineWidgets import *
from pathlib import Path

class MyWindow(QtWidgets.QWidget):
    def closeEvent(self,data):
        self.hide()

class Overlay(QtCore.QObject):
    fileName = ".config/discord-overlay/discordurl"
    configFileName= ".config/discord-overlay/discoverlay.ini"
    url = None

    def main(self):
        # Get Screen dimensions
        screen = app.primaryScreen()
        self.size = screen.size()
        #Check for existing Dir
        if not os.path.exists(".config/discord-overlay/"):
            os.makedirs(".config/discord-overlay/")
            
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
        self.createSettingsWindow()
        self.createSysTrayIcon()
        if not self.url:
            self.settings.show()

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

    def createSysTrayIcon(self):
        self.trayImgBase64 = "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAC4jAAAuIwF4pT92AAAAB3RJTUUH5AUEDxsTIFcmagAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeBDhcAAAN+SURBVFjDzZcxaCJpGIafmTuyisVgsDCJiyApR3FAokmjsT5juuC0l2BzjVyfwv5Ic43EW0ijWCb2JtMEZxFGximDMKzhLIaYKcK4zeaKM8ux5A5vN8Pmbef/53t4v3/+eT+B5fUGSAKbwAawCgQXzzzgDrgFboAR8HGZlwpLrFkD8sBWo9EQ0+k0sViMcDhMIBAAYD6fM5vNmEwmDIdDqtXqJ+A9oAF/fgvAXqFQKB4fH5PL5ZhOp1iWhWmaGIaBYRgAKIqCoiikUilkWSYajdLv96nX61xdXfWAi/8LsAao7Xb7bblcxrIsWq0WkiSRz+dJJBJEIhGCwb874HkejuMwHo/RNA3XdVFVFVmWOT8/p1KpfABaz7nxHEAC+FnX9VA8HqfZbCJJEqVSiXg8vtRhsW2bbreL67ocHh5i2zbZbPYB+AMY/xfAGvDLaDQKCYLA3t4enU6HTCbD12gwGHBwcMDFxQWPj48kk8kH4Pd/OiF+sUfVdT0kCAK1Wo1er/fVxQEymQy9Xo9arYYgCOi6HgLUf3Ngr91uF3d3d9nZ2aHX6y1t+TItKRaLXF9fc3l5SaVS+XwwnxxYKxQKxXK5TLPZpNPpvFhxgHg8TqfTodlsUi6XKRQKxUW7+WGx5qd3797F7u/vcRyH/f19Xlrr6+uYpsnKygrb29ucnZ39CFji4obbyuVytFotSqUSfqlUKtFqtcjlcgBbwBsRSDYaDXE6nSJJ0ota/1wrJEliOp3SaDREICkCm+l0GsuyyOfz+K18Po9lWaTTaYBNEdiIxWKYpkkikfAdIJFIYJomsVgMYEMEVsPhMIZhEIlEfAeIRCIYhkE4HAZYFYFgIBDAMIzPd7ufCgaDGIbx9CcNinxniYA3n89RFAXP83wv6HkeiqIwn88BPBG4m81mKIqC4zi+AziOg6IozGYzgDsRuJ1MJqRSKcbjse8A4/GYVCrFZDIBuBWBm+FwiCzLaJrmO4CmaciyzHA4BLgRgVG1Wv0UjUZxXRfbtn0rbts2rusSjUafcuNIXKTX9/1+H1VV6Xa7vgF0u11UVaXf77MIrR+fPkOtXq8jyzKu6zIYDF68+GAwwHVdZFmmXq+zSMzfP5B8mQl/1XX9bSgUolarcXp6+s0Qtm1zdHTEyckJDw8PZLPZD8BvryaUvrpY/ioGk1cxmr2a4dT38fwv9cLeiMwLuMsAAAAASUVORK5CYII="
        pm = QtGui.QPixmap()
        pm.loadFromData(base64.b64decode(self.trayImgBase64))

        self.trayIcon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(pm), app)
        self.trayMenu = QtWidgets.QMenu()
        self.showAction = self.trayMenu.addAction("Settings")
        self.showAction.triggered.connect(self.showSettings)
        self.exitAction = self.trayMenu.addAction("Close")
        self.exitAction.triggered.connect(self.exit)
        self.trayIcon.setContextMenu(self.trayMenu)
        self.trayIcon.show()

    def createSettingsWindow(self):
        self.settings = MyWindow()
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

    def exit(self):
        sys.exit(0)

    def showSettings(self):
        self.settings.show()

    def hideSettings(self):
        self.settings.hide()

os.chdir(Path.home())
app=QtWidgets.QApplication(sys.argv)
o = Overlay()
o.main()
app.exec_()
