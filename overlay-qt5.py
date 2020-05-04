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
        # Don't close settings, only hide it
        self.hide()

class ResizingImage(QtWidgets.QLabel):
    image = None
    w=0
    h=0
    def setImage(self, image):
        self.image = image
        self.fillImage()

    def resizeEvent(self,e):
        self.w= e.size().width()
        self.h= e.size().height()
        self.fillImage()

    def fillImage(self):
        if self.image and self.w>0 and self.h>0:
            self.setPixmap(self.image.scaled(int(self.w), int(self.h),QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation))

class AspectRatioWidget(QtWidgets.QWidget):
    def __init__(self, widget, x,y,parent):
        super().__init__(parent)
        self.aspect_ratio = x / y
        self.setLayout(QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight, self))
        #  add spacer, then widget, then spacer
        self.layout().addItem(QtWidgets.QSpacerItem(0, 0))
        self.layout().addWidget(widget)
        self.layout().addItem(QtWidgets.QSpacerItem(0, 0))

    def resizeEvent(self, e):
        w = e.size().width()
        h = e.size().height()

        if w / h > self.aspect_ratio:  # too wide
            self.layout().setDirection(QtWidgets.QBoxLayout.LeftToRight)
            widget_stretch = int(h * self.aspect_ratio)
            outer_stretch =int( (w - widget_stretch) / 2 + 0.5 )
        else:  # too tall
            self.layout().setDirection(QtWidgets.QBoxLayout.TopToBottom)
            widget_stretch = int(w / self.aspect_ratio)
            outer_stretch =int( (h - widget_stretch) / 2 + 0.5 )

        self.layout().setStretch(0, outer_stretch)
        self.layout().setStretch(1, widget_stretch)
        self.layout().setStretch(2, outer_stretch)

class Overlay(QtCore.QObject):
    fileName = ".config/discord-overlay/discordurl"
    configFileName= ".config/discord-overlay/discoverlay.ini"
    url = None

    def getInt(self, config, name, default):
        if config and config.has_option('main', name):
            return config.getint('main', name)
        else:
            return default

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
        config = None
        if os.path.isfile(self.configFileName):
            config = ConfigParser()
            config.read(self.configFileName)
        self.posXL=self.getInt(config, 'xl', 0)
        self.posXR=self.getInt(config, 'xr', 200)
        self.posYT=self.getInt(config, 'yt', 50)
        self.posYB=self.getInt(config, 'yb', 450)
        self.right=(self.getInt(config, 'rightalign', 0) == 1)

        self.createOverlay()
        self.createSettingsWindow()
        self.createPositionWindow()
        self.createSysTrayIcon()
        if not self.url:
            self.settings.show()
            self.position.show()

    def moveOverlay(self):
        print("%i %i, %i %i" % (self.posXL, self.posYT, self.posXR, self.posYB))
        self.overlay.resize(self.posXR-self.posXL,self.posYB-self.posYT)
        self.overlay.move(self.posXL,self.posYT)

    def on_url(self, url):
        self.overlay.load(QtCore.QUrl(url))
        self.url = url
        self.save()

    @pyqtSlot()
    def save(self):
        config = ConfigParser()
        config.add_section('main')
        config.set('main','xl','%d'%(self.posXL))
        config.set('main','xr','%d'%(self.posXR))
        config.set('main','yt','%d'%(self.posYT))
        config.set('main','yb','%d'%(self.posYB))
        config.set('main','rightalign','%d' % (int(self.right)))
        with open(self.configFileName,'w') as file:
            config.write(file)
        with open(self.fileName,'w') as file:
            file.write(self.url)
        self.settings.hide()
        self.position.hide()

    @pyqtSlot()
    def on_click(self):
        self.runJS("document.getElementsByClassName('source-url')[0].value;", self.on_url)

    @pyqtSlot()
    def skip_stream_button(self):
        skipIntro = "buttons = document.getElementsByTagName('button');for(i=0;i<buttons.length;i++){if(buttons[i].innerHTML=='Install for OBS'){buttons[i].click()}}"
        hideLogo = "document.getElementsByClassName('install-logo')[0].style.setProperty('display','none');"
        resizeContents = "document.getElementsByClassName('content')[0].style.setProperty('top','30px');"
        resizeHeader = "document.getElementsByClassName('header')[0].style.setProperty('height','35px');"
        hidePreview = "document.getElementsByClassName('config-link')[0].style.setProperty('height','300px');document.getElementsByClassName('config-link')[0].style.setProperty('overflow','hidden');"
        hideClose = "document.getElementsByClassName('close')[0].style.setProperty('display','none');"

        self.runJS(skipIntro)
        self.runJS(hideLogo)
        self.runJS(resizeContents)
        self.runJS(hidePreview)
        self.runJS(resizeHeader)
        self.runJS(hideClose)

    def runJS(self,string, retFunc=None):
        if retFunc:
            self.settingWebView.page().runJavaScript(string, retFunc)
        else:
            self.settingWebView.page().runJavaScript(string)

    def applyTweaks(self):
        if self.right:
            self.addCSS('cssrightalign','li.voice-state{ direction:rtl; }.avatar{ float:right !important; }.user{ display:flex; }');
        else:
            self.delCSS('cssrightalign')

    def addCSS(self,name,css):
        js = '(function() { css = document.createElement(\'style\');css.type=\'text/css\';css.id=\'%s\';document.head.appendChild(css);css.innerText=\'%s\';})()' % (name,css)
        self.overlay.page().runJavaScript(js)

    def delCSS(self,name):
        js = "(function() { css = document.getElementById('%s'); css.parentNode.removeChild(css); })()" % (name)
        self.overlay.page().runJavaScript(js)

    @pyqtSlot()
    def toggleRightAlign(self,button=None):
        if self.rightAlign.isChecked():
            self.right=True
        else:
            self.right=False
        self.applyTweaks()

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
        self.showAction = self.trayMenu.addAction("Change Style")
        self.showAction.triggered.connect(self.showSettings)
        self.showAction2 = self.trayMenu.addAction("Change Position")
        self.showAction2.triggered.connect(self.showPosition)
        self.exitAction = self.trayMenu.addAction("Close")
        self.exitAction.triggered.connect(self.exit)
        self.trayIcon.setContextMenu(self.trayMenu)
        self.trayIcon.show()

    def createPositionWindow(self):
        self.position = MyWindow()
        self.positionbox = QtWidgets.QVBoxLayout()
        self.settingsGridWidget= QtWidgets.QWidget()
        self.settingsAspectRatio = AspectRatioWidget(self.settingsGridWidget,self.size.width(), self.size.height(),None)
        self.settingsGrid = QtWidgets.QGridLayout()
        self.settingsPreview = ResizingImage()
        self.settingsDistanceFromLeft = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.settingsDistanceFromRight = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.settingsDistanceFromTop = QtWidgets.QSlider(QtCore.Qt.Vertical)
        self.settingsDistanceFromBottom = QtWidgets.QSlider(QtCore.Qt.Vertical)
        self.settingSave = QtWidgets.QPushButton("Save & Exit")

        self.settingsDistanceFromLeft.valueChanged[int].connect(self.changeValueFL)
        self.settingsDistanceFromLeft.setMaximum(self.size.width())
        self.settingsDistanceFromLeft.setValue(self.posXL)
        self.settingsDistanceFromRight.valueChanged[int].connect(self.changeValueFR)
        self.settingsDistanceFromRight.setMaximum(self.size.width())
        self.settingsDistanceFromRight.setValue(self.posXR)
        self.settingsDistanceFromTop.valueChanged[int].connect(self.changeValueFT)
        self.settingsDistanceFromTop.setMaximum(self.size.height())
        self.settingsDistanceFromTop.setInvertedAppearance(True)
        self.settingsDistanceFromTop.setValue(self.posYT)
        self.settingsDistanceFromBottom.valueChanged[int].connect(self.changeValueFB)
        self.settingsDistanceFromBottom.setMaximum(self.size.height())
        self.settingsDistanceFromBottom.setInvertedAppearance(True)
        self.settingsDistanceFromBottom.setValue(self.posYB)
        self.settingSave.clicked.connect(self.save)

        self.settingsGrid.addWidget(self.settingsPreview,0,0)
        self.settingsGrid.addWidget(self.settingsDistanceFromLeft,1,0)
        self.settingsGrid.addWidget(self.settingsDistanceFromRight,2,0)
        self.settingsGrid.addWidget(self.settingsDistanceFromTop,0,1)
        self.settingsGrid.addWidget(self.settingsDistanceFromBottom,0,2)
        self.settingsGridWidget.setLayout(self.settingsGrid)
        self.positionbox.addWidget(self.settingsAspectRatio)
        self.position.setLayout(self.positionbox)
        self.positionbox.addWidget(self.settingSave)
        self.screenShot()

    def createSettingsWindow(self):
        self.settings = MyWindow()
        self.settingsbox = QtWidgets.QVBoxLayout()
        self.settingWebView = QWebEngineView()
        self.rightAlign = QtWidgets.QCheckBox("Right Align")
        self.settingTakeUrl = QtWidgets.QPushButton("Use this overlay")
        
        self.settingTakeUrl.clicked.connect(self.on_click)
        self.settingWebView.loadFinished.connect(self.skip_stream_button)
        self.rightAlign.stateChanged.connect(self.toggleRightAlign)
        self.rightAlign.setChecked(self.right)
        self.settingWebView.load(QtCore.QUrl("https://streamkit.discord.com/overlay"))

        self.settingsbox.addWidget(self.settingWebView)
        self.settingsbox.addWidget(self.rightAlign)
        self.settingsbox.addWidget(self.settingTakeUrl)
        self.settings.setLayout(self.settingsbox)

    def screenShot(self):
        screen = QtWidgets.QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        self.settingsPreview.setImage(screenshot)
        self.settingsPreview.setContentsMargins(0,0,0,0)

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
        self.overlay.loadFinished.connect(self.applyTweaks)
        self.overlay.load(QtCore.QUrl(self.url))

        self.overlay.setStyleSheet("background:transparent;")
        self.moveOverlay()
        self.overlay.show()

    def exit(self):
        app.quit()

    def showSettings(self):
        self.settings.show()

    def showPosition(self):
        self.position.show()

os.chdir(Path.home())
app=QtWidgets.QApplication(sys.argv)
o = Overlay()
o.main()
app.exec_()
