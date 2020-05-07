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
import logging
import base64
from configparser import ConfigParser
from PyQt5 import QtWidgets,QtGui,QtCore
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWebEngineWidgets import *
from pathlib import Path
from xdg.BaseDirectory import xdg_config_home

logger = logging.getLogger(__name__)


class MyWindow(QtWidgets.QWidget):
    def closeEvent(self,data):
        # Don't close settings, only hide it
        self.hide()

class ResizingImage(QtWidgets.QLabel):
    def __init__(self):
        super().__init__()
        self.image = None
        self.w = 0
        self.h = 0

    def setImage(self, image):
        self.image = image
        self.fillImage()

    def resizeEvent(self,e):
        self.w= e.size().width()
        self.h= e.size().height()
        self.fillImage()

    def sizeHint(self):
        return QtCore.QSize(self.image.width() // 2, self.image.height() // 2)

    def fillImage(self):
        if self.image and self.w>0 and self.h>0:
            self.setPixmap(self.image.scaled(int(self.w), int(self.h),QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation))

class AspectRatioWidget(QtWidgets.QWidget):
    def __init__(self, widget):
        super().__init__()
        self.aspect_ratio = 1
        self.setLayout(QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight, self))
        #  add spacer, then widget, then spacer
        self.layout().addItem(QtWidgets.QSpacerItem(0, 0))
        self.layout().addWidget(widget)
        self.layout().addItem(QtWidgets.QSpacerItem(0, 0))
        self.w = 0
        self.h = 0

    def updateScreen(self, x, y):
        # A different screen with a different aspect ratio
        self.aspect_ratio = x / y
        self.changePadding()

    def resizeEvent(self, e):
        self.w = e.size().width()
        self.h = e.size().height()
        self.changePadding()

    def changePadding(self):
        if self.w < 1 or self.h < 1:
            return
        if self.w / self.h > self.aspect_ratio:  # too wide
            self.layout().setDirection(QtWidgets.QBoxLayout.LeftToRight)
            widget_stretch = int(self.h * self.aspect_ratio)
            outer_stretch =int( (self.w - widget_stretch) / 2 + 0.5 )
        else:  # too tall
            self.layout().setDirection(QtWidgets.QBoxLayout.TopToBottom)
            widget_stretch = int(self.w / self.aspect_ratio)
            outer_stretch =int( (self.h - widget_stretch) / 2 + 0.5 )

        self.layout().setStretch(0, outer_stretch)
        self.layout().setStretch(1, widget_stretch)
        self.layout().setStretch(2, outer_stretch)

class Overlay(QtCore.QObject):

    def __init__(self,app):
        super().__init__()
        self.app = app
        self.url = None
        self.size = None

        self.configDir =  os.path.join(xdg_config_home, "discord-overlay")
        self.streamkitUrlFileName = os.path.join(self.configDir, "discordurl")
        self.configFileName = os.path.join(self.configDir, "discoverlay.ini")

    def main(self):
        os.makedirs(self.configDir, exist_ok=True)
        try:
            with open(self.streamkitUrlFileName) as file:
                self.url = file.readline().rstrip()
        except (OSError, IOError):
            self.url = None
        config = ConfigParser()
        config.read(self.configFileName)

        self.posXL=config.getint('main', 'xl', fallback=0)
        self.posXR=config.getint('main', 'xr', fallback=200)
        self.posYT=config.getint('main', 'yt', fallback=50)
        self.posYB=config.getint('main', 'yb', fallback=450)
        self.right=config.getboolean('main','rightalign', fallback=False)
        self.mutedeaf=config.getboolean('main','mutedeaf', fallback=False)
        self.screenName=config.get('main', 'screen', fallback='None')

        self.createOverlay()
        self.createSettingsWindow()
        self.createPositionWindow()
        self.createSysTrayIcon()
        if not self.url:
            self.settings.show()
            self.position.show()
        self.moveOverlay()

    def moveOverlay(self):
        self.overlay.resize(self.posXR-self.posXL,self.posYB-self.posYT)
        self.overlay.move(self.posXL + self.screenOffset.left(),self.posYT + self.screenOffset.top())

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
        config.set('main','mutedeaf', '%d' % (int(self.mutedeaf)))
        config.set('main', 'screen', self.screenName)

        with open(self.configFileName,'w') as file:
            config.write(file)
        if self.url:
            with open(self.streamkitUrlFileName,'w') as file:
                file.write(self.url)
        

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
        chooseVoice = "for( let button of document.getElementsByTagName('button')){ if(button.getAttribute('value') == 'voice'){ button.click(); } }"
        chooseChat = "for( let button of document.getElementsByTagName('button')){ if(button.getAttribute('value') == 'chat'){ button.click(); } }"

        self.runJS(skipIntro)
        self.runJS(hideLogo)
        self.runJS(resizeContents)
        self.runJS(hidePreview)
        self.runJS(resizeHeader)
        self.runJS(hideClose)
        if self.url:
            if 'overlay/voice' in self.url:
                self.runJS(chooseVoice)
            else:
                self.runJS(chooseChat)

    def enableMuteDeaf(self):
        tweak = "if(typeof console.oldlog === 'undefined'){console.oldlog=console.log;}console.log = function(text,input){if(typeof input !== 'undefined'){if(input.evt == 'VOICE_STATE_UPDATE'){name=input.data.nick;uState = input.data.voice_state;muteicon = '';if(uState.self_mute || uState.mute){muteicon='<img src=\\'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAABhMAAAYJQE8CCw1AAAAB3RJTUUH5AUGCx0VMm5EjgAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeBDhcAAABzSURBVDjLxZIxCsAwCEW/oT1P7z93zZJjeIYMv0sCIaBoodTJDz6/JgJfBslOsns1xYONvK66JCeqAC4ALTz+dJvOo0lu/zS87p2C98IdHlq9Buo5D62h17amScMk78hBWXB/DUdP2fyBaINjJiJy4o94AM8J8ksz/MQjAAAAAElFTkSuQmCC\\' style=\\'height:0.9em;\\'>';}deaficon = '';if(uState.self_deaf || uState.deaf){deaficon='<img src=\\'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAABhMAAAYJQE8CCw1AAAAB3RJTUUH5AUGCx077rhJQQAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeBDhcAAACNSURBVDjLtZPNCcAgDIUboSs4iXTGLuI2XjpBz87g4fWiENr8iNBAQPR9ef7EbfsjAEQAN4A2UtCcGtyMzFxjwVlyBHAwTRFh52gqHDVnF+6L1XJ/w31cp7YvOX/0xlOJ254qYJ1ZLTAmPWeuDVxARDurfBFR8jovMLEKWxG6c1qB55pEuQOpE8vKz30AhEdNuXK0IugAAAAASUVORK5CYII=\\' style=\\'height:0.9em;\\'>';}spans = document.getElementsByTagName('span');for(i=0;i<spans.length;i++){if(spans[i].innerHTML.startsWith(name)){text = name + muteicon + deaficon;spans[i].innerHTML = text;}}}}else{console.oldlog(text);}};"
        self.overlay.page().runJavaScript(tweak)

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
        if self.mutedeaf:
            self.enableMuteDeaf()
        self.addCSS('cssflexybox', 'div.chat-container { width: 100%; height: 100%; top: 0; left: 0; position: fixed; display: flex; flex-direction: column; } div.chat-container > .messages { box-sizing: border-box; width: 100%; flex: 1; }')

    def addCSS(self,name,css):
        js = '(function() { css = document.createElement(\'style\');css.type=\'text/css\';css.id=\'%s\';document.head.appendChild(css);css.innerText=\'%s\';})()' % (name,css)
        self.overlay.page().runJavaScript(js)

    def delCSS(self,name):
        js = "(function() { css = document.getElementById('%s'); if(css!=null){ css.parentNode.removeChild(css);} })()" % (name)
        self.overlay.page().runJavaScript(js)

    @pyqtSlot()
    def toggleMuteDeaf(self,button=None):
        self.mutedeaf = self.muteDeaf.isChecked()
        if self.muteDeaf.isChecked():
            self.enableMuteDeaf()

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

        self.trayIcon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(pm), self.app)
        self.trayMenu = QtWidgets.QMenu()
        self.showAction = self.trayMenu.addAction("Change Style")
        self.showAction.triggered.connect(self.showSettings)
        self.showAction2 = self.trayMenu.addAction("Change Position")
        self.showAction2.triggered.connect(self.showPosition)
        self.exitAction = self.trayMenu.addAction("Close")
        self.exitAction.triggered.connect(self.exit)
        self.trayIcon.setContextMenu(self.trayMenu)
        self.trayIcon.show()

    def fillPositionWindowOptions(self):
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

    def populateScreenList(self):
        self.ignoreScreenComboBox = True
        screenList = self.app.screens()
        self.settingsScreen.clear()
        for i, s in enumerate(screenList):
            self.settingsScreen.addItem(s.name())
            if s.name() == self.screenName:
                self.settingsScreen.setCurrentIndex(i)

        self.ignoreScreenComboBox = False
        self.chooseScreen()

    def changeScreen(self, index):
        if not self.ignoreScreenComboBox:
            self.screenName = self.settingsScreen.currentText()
            self.chooseScreen()

    def chooseScreen(self):
        screen = None
        screenList = self.app.screens()
        logger.debug("Discovered screens: %r", [s.name() for s in screenList])

        for s in screenList:
            if s.name() == self.screenName:
                 screen = s
                 logger.debug("Chose screen %s", screen.name())
                 break
        # The chosen screen is not in this list. Drop to primary
        else:
            screen = self.app.primaryScreen()
            logger.warning("Chose screen %r as fallback because %r could not be matched", screen.name(), self.screenName)

        # Fill Info!
        self.size = screen.size()
        self.screenName = s.name()
        self.screenOffset = screen.availableGeometry()
        self.settingsAspectRatio.updateScreen(self.size.width(), self.size.height())
        self.fillPositionWindowOptions()
        self.moveOverlay()
        self.screenShot(screen)

    def createPositionWindow(self):
        # Positional Settings Window
        self.position = MyWindow()
        self.positionbox = QtWidgets.QVBoxLayout()

        # Use a grid to lay out screen & sliders
        self.settingsGridWidget= QtWidgets.QWidget()
        self.settingsGrid = QtWidgets.QGridLayout()

        # Use the custom Aspect widget to keep the whole thing looking
        # as close to the user experience as possible
        self.settingsAspectRatio = AspectRatioWidget(self.settingsGridWidget)

        # Grid contents
        self.settingsPreview = ResizingImage()
        self.settingsPreview.setMinimumSize(1, 1)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.settingsPreview.setSizePolicy(sizePolicy)
        self.settingsDistanceFromLeft = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.settingsDistanceFromRight = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.settingsDistanceFromTop = QtWidgets.QSlider(QtCore.Qt.Vertical)
        self.settingsDistanceFromBottom = QtWidgets.QSlider(QtCore.Qt.Vertical)

        # Screen chooser
        self.settingsScreen = QtWidgets.QComboBox()

#        self.position.setMinimumSize(600,600)
        # Save button
        self.settingSave = QtWidgets.QPushButton("Save")

        # Fill Screens, Choose the screen if config is set
        self.populateScreenList()

        self.settingSave.clicked.connect(self.save)
        self.settingsScreen.currentIndexChanged.connect(self.changeScreen)

        self.settingsGrid.addWidget(self.settingsPreview,0,0)
        self.settingsGrid.addWidget(self.settingsDistanceFromLeft,1,0)
        self.settingsGrid.addWidget(self.settingsDistanceFromRight,2,0)
        self.settingsGrid.addWidget(self.settingsDistanceFromTop,0,1)
        self.settingsGrid.addWidget(self.settingsDistanceFromBottom,0,2)
        self.settingsGridWidget.setLayout(self.settingsGrid)
        self.positionbox.addWidget(self.settingsScreen)
        self.positionbox.addWidget(self.settingsAspectRatio)
        self.position.setLayout(self.positionbox)
        self.positionbox.addWidget(self.settingSave)

    def createSettingsWindow(self):
        self.settings = MyWindow()
        self.settingsbox = QtWidgets.QVBoxLayout()
        self.settingWebView = QWebEngineView()
        self.rightAlign = QtWidgets.QCheckBox("Right Align")
        self.muteDeaf = QtWidgets.QCheckBox("Show mute and deafen")
        self.settingTakeUrl = QtWidgets.QPushButton("Save")
        
        self.settings.setMinimumSize(400,400)
        self.settingTakeUrl.clicked.connect(self.on_click)
        self.settingWebView.loadFinished.connect(self.skip_stream_button)
        self.rightAlign.stateChanged.connect(self.toggleRightAlign)
        self.rightAlign.setChecked(self.right)
        self.muteDeaf.stateChanged.connect(self.toggleMuteDeaf)
        self.muteDeaf.setChecked(self.mutedeaf)
      
        self.settingWebView.load(QtCore.QUrl("https://streamkit.discord.com/overlay"))

        self.settingsbox.addWidget(self.settingWebView)
        self.settingsbox.addWidget(self.rightAlign)
        self.settingsbox.addWidget(self.muteDeaf)
        self.settingsbox.addWidget(self.settingTakeUrl)
        self.settings.setLayout(self.settingsbox)

    def screenShot(self, screen):
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
        self.overlay.show()

    def exit(self):
        self.app.quit()

    def showSettings(self):
        self.settings.show()

    def showPosition(self):
        self.position.show()

if __name__ == '__main__':
    def main(app):
        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s')
        try:
            logging.getLogger().setLevel(os.environ.get("LOGLEVEL", "INFO").upper())
        except ValueError as exc:
            logger.warning("Can't set log level: %s", exc)

        o = Overlay(app)
        o.main()
        app.exec()

    app = QtWidgets.QApplication(sys.argv)
    main(app)
