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
import re
import json
from configparser import ConfigParser
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from pathlib import Path
from xdg.BaseDirectory import xdg_config_home

logger = logging.getLogger(__name__)


class ResizingImage(QtWidgets.QLabel):
    def __init__(self):
        super().__init__()
        self.image = None
        self.w = 0
        self.h = 0

    def setImage(self, image):
        self.image = image
        self.fillImage()

    def resizeEvent(self, e):
        self.w = e.size().width()
        self.h = e.size().height()
        self.fillImage()

    def sizeHint(self):
        if self.image:
            return QtCore.QSize(self.image.width() // 2, self.image.height() // 2)
        return QtCore.QSize(0, 0)

    def fillImage(self):
        if self.image and self.w > 0 and self.h > 0:
            self.setPixmap(self.image.scaled(int(self.w), int(
                self.h), QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation))


class AspectRatioWidget(QtWidgets.QWidget):
    def __init__(self, widget):
        super().__init__()
        self.aspect_ratio = 1
        self.setLayout(QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.LeftToRight, self))
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
            outer_stretch = int((self.w - widget_stretch) / 2 + 0.5)
        else:  # too tall
            self.layout().setDirection(QtWidgets.QBoxLayout.TopToBottom)
            widget_stretch = int(self.w / self.aspect_ratio)
            outer_stretch = int((self.h - widget_stretch) / 2 + 0.5)

        self.layout().setStretch(0, outer_stretch)
        self.layout().setStretch(1, widget_stretch)
        self.layout().setStretch(2, outer_stretch)


class App(QtCore.QObject):

    def __init__(self, our_app):
        super().__init__()
        self.app = our_app
        self.overlays = []
        self.configDir = os.path.join(xdg_config_home, "discord-overlay")
        self.streamkitUrlFileName = os.path.join(self.configDir, "discordurl")
        self.configFileName = os.path.join(self.configDir, "discoverlay.ini")
        self.settings = None
        self.presets = None

    def main(self):
        os.makedirs(self.configDir, exist_ok=True)
        config = ConfigParser(interpolation=None)
        config.read(self.configFileName)
        for section in config.sections():
            if not section == 'core':
                url_list = config.get(
                    section, 'url', fallback=None)
                if url_list:
                    for url in url_list.split(","):

                        overlay = Overlay(
                            self, self.configFileName, section, url)
                        overlay.load()
                        self.overlays.append(overlay)
        if len(self.overlays) == 0:
            overlay = Overlay(self, self.configFileName, 'main', None)
            overlay.load()
            self.overlays.append(overlay)
            self.showPresetWindow()
        self.app.setQuitOnLastWindowClosed(False)
        self.createSysTrayIcon()

    def reinit(self):
        for overlay in self.overlays:
            overlay.delete()
        self.trayIcon.hide()
        self.__init__(self.app)
        self.main()

    def createSysTrayIcon(self):
        trayImgBase64 = "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAC4jAAAuIwF4pT92AAAAB3RJTUUH5AUEDxsTIFcmagAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeBDhcAAAN+SURBVFjDzZcxaCJpGIafmTuyisVgsDCJiyApR3FAokmjsT5juuC0l2BzjVyfwv5Ic43EW0ijWCb2JtMEZxFGximDMKzhLIaYKcK4zeaKM8ux5A5vN8Pmbef/53t4v3/+eT+B5fUGSAKbwAawCgQXzzzgDrgFboAR8HGZlwpLrFkD8sBWo9EQ0+k0sViMcDhMIBAAYD6fM5vNmEwmDIdDqtXqJ+A9oAF/fgvAXqFQKB4fH5PL5ZhOp1iWhWmaGIaBYRgAKIqCoiikUilkWSYajdLv96nX61xdXfWAi/8LsAao7Xb7bblcxrIsWq0WkiSRz+dJJBJEIhGCwb874HkejuMwHo/RNA3XdVFVFVmWOT8/p1KpfABaz7nxHEAC+FnX9VA8HqfZbCJJEqVSiXg8vtRhsW2bbreL67ocHh5i2zbZbPYB+AMY/xfAGvDLaDQKCYLA3t4enU6HTCbD12gwGHBwcMDFxQWPj48kk8kH4Pd/OiF+sUfVdT0kCAK1Wo1er/fVxQEymQy9Xo9arYYgCOi6HgLUf3Ngr91uF3d3d9nZ2aHX6y1t+TItKRaLXF9fc3l5SaVS+XwwnxxYKxQKxXK5TLPZpNPpvFhxgHg8TqfTodlsUi6XKRQKxUW7+WGx5qd3797F7u/vcRyH/f19Xlrr6+uYpsnKygrb29ucnZ39CFji4obbyuVytFotSqUSfqlUKtFqtcjlcgBbwBsRSDYaDXE6nSJJ0ota/1wrJEliOp3SaDREICkCm+l0GsuyyOfz+K18Po9lWaTTaYBNEdiIxWKYpkkikfAdIJFIYJomsVgMYEMEVsPhMIZhEIlEfAeIRCIYhkE4HAZYFYFgIBDAMIzPd7ufCgaDGIbx9CcNinxniYA3n89RFAXP83wv6HkeiqIwn88BPBG4m81mKIqC4zi+AziOg6IozGYzgDsRuJ1MJqRSKcbjse8A4/GYVCrFZDIBuBWBm+FwiCzLaJrmO4CmaciyzHA4BLgRgVG1Wv0UjUZxXRfbtn0rbts2rusSjUafcuNIXKTX9/1+H1VV6Xa7vgF0u11UVaXf77MIrR+fPkOtXq8jyzKu6zIYDF68+GAwwHVdZFmmXq+zSMzfP5B8mQl/1XX9bSgUolarcXp6+s0Qtm1zdHTEyckJDw8PZLPZD8BvryaUvrpY/ioGk1cxmr2a4dT38fwv9cLeiMwLuMsAAAAASUVORK5CYII="
        pm = QtGui.QPixmap()
        pm.loadFromData(base64.b64decode(trayImgBase64))

        self.trayIcon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(pm), self.app)
        self.trayMenu = QtWidgets.QMenu()
        self.showAction3 = self.trayMenu.addAction("Settings")
        self.showAction3.triggered.connect(self.showPresetWindow)
        self.exitAction = self.trayMenu.addAction("Close")
        self.exitAction.triggered.connect(self.exit)
        self.trayIcon.setContextMenu(self.trayMenu)
        self.trayIcon.show()

    def showPresetWindow(self):
        self.presets = QtWidgets.QMainWindow()
        self.presets.setWindowTitle('Configure overlays')
        self.fillPresetWindow()
        self.presets.show()

    def fillPresetWindow(self):
        gridW = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout()
        gridW.setLayout(grid)
        count = 0
        done = []
        for overlay in self.overlays:
            if overlay.name in done:
                continue
            done.append(overlay.name)
            label = QtWidgets.QLabel()
            label.setText(overlay.name)
            buttonSettings = QtWidgets.QPushButton('Layout')
            buttonPosition = QtWidgets.QPushButton('Position')
            buttonDelete = QtWidgets.QPushButton('Delete')
            buttonSettings.clicked.connect(overlay.showSettings)
            buttonPosition.clicked.connect(overlay.showPosition)
            buttonDelete.clicked.connect(lambda: self.deleteOverlay(overlay))
            grid.addWidget(label, count, 0)
            grid.addWidget(buttonSettings, count, 1)
            grid.addWidget(buttonPosition, count, 2)
            grid.addWidget(buttonDelete, count, 3)
            count = count+1
        addOverlayButton = QtWidgets.QPushButton('Add overlay')
        addOverlayButton.clicked.connect(self.addOverlay)
        addOverlayButton.setMaximumWidth(150)
        self.textbox = QtWidgets.QLineEdit()
        self.textbox.setMaximumWidth(150)
        self.textbox.setPlaceholderText('overlay Name')
        noneBox = QtWidgets.QLabel()
        noneBox.setMaximumWidth(150)
        grid.addWidget(noneBox, count, 3)
        grid.addWidget(addOverlayButton, count, 2)
        grid.addWidget(self.textbox, count, 1)
        self.presets.setCentralWidget(gridW)

    def addOverlay(self, button=None):
        if re.match('^[a-z]+$', self.textbox.text()):
            overlay = Overlay(self, self.configFileName,
                              self.textbox.text(), None)
            overlay.load()
            self.overlays.append(overlay)
            self.fillPresetWindow()
        else:
            error_dialog = QtWidgets.QErrorMessage()
            error_dialog.showMessage(
                "Please only use lower case letters and no symbols")
            error_dialog.exec_()

    def deleteOverlay(self, overlay):
        n = overlay.name
        overlay.delete()
        for overlayToo in self.overlays:
            if overlayToo.name == n:
                self.overlays.remove(overlayToo)
        # self.overlays.remove(overlay)
        config = ConfigParser(interpolation=None)
        config.read(self.configFileName)
        config.remove_section(n)
        with open(self.configFileName, 'w') as file:
            config.write(file)
        self.fillPresetWindow()

    def exit(self):
        self.app.quit()


class Overlay(QtCore.QObject):

    def __init__(self, up, configFileName, name, url):
        super().__init__()
        self.configFileName = configFileName
        self.parent = up
        self.app = up.app
        self.url = url
        self.size = None
        self.name = name
        self.overlay = None
        self.settings = None
        self.position = None
        self.enabled = True
        self.showtitle = True
        self.mutedeaf = True
        self.showtitle = True

    def load(self):
        config = ConfigParser(interpolation=None)
        config.read(self.configFileName)
        self.posXL = config.getint(self.name, 'xl', fallback=0)
        self.posXR = config.getint(self.name, 'xr', fallback=200)
        self.posYT = config.getint(self.name, 'yt', fallback=50)
        self.posYB = config.getint(self.name, 'yb', fallback=450)
        self.right = config.getboolean(self.name, 'rightalign', fallback=False)
        self.mutedeaf = config.getboolean(
            self.name, 'mutedeaf', fallback=True)
        self.chatresize = config.getboolean(
            self.name, 'chatresize', fallback=True)
        self.screenName = config.get(self.name, 'screen', fallback='None')
        #self.url = config.get(self.name, 'url', fallback=None)
        self.enabled = config.getboolean(self.name, 'enabled', fallback=True)
        self.showtitle = config.getboolean(self.name, 'title', fallback=True)
        self.hideinactive = config.getboolean(
            self.name, 'hideinactive', fallback=True)
        self.chooseScreen()
        # TODO Check, is there a better logic location for this?
        if self.enabled:
            self.showOverlay()

    def moveOverlay(self):
        if self.overlay:
            self.overlay.resize(self.posXR-self.posXL, self.posYB-self.posYT)
            self.overlay.move(self.posXL + self.screenOffset.left(),
                              self.posYT + self.screenOffset.top())

    def on_url(self, url):
        if self.overlay:
            self.overlay.load(QtCore.QUrl(url))
        self.url = url
        self.save()
        self.settings.close()
        self.settings = None

    def on_save_position(self, url):
        self.save()
        self.position.close()
        self.position = None

    @pyqtSlot()
    def save(self):
        config = ConfigParser(interpolation=None)
        config.read(self.configFileName)
        if not config.has_section(self.name):
            config.add_section(self.name)
        config.set(self.name, 'xl', '%d' % (self.posXL))
        config.set(self.name, 'xr', '%d' % (self.posXR))
        config.set(self.name, 'yt', '%d' % (self.posYT))
        config.set(self.name, 'yb', '%d' % (self.posYB))
        config.set(self.name, 'rightalign', '%d' % (int(self.right)))
        config.set(self.name, 'mutedeaf', '%d' % (int(self.mutedeaf)))
        config.set(self.name, 'chatresize', '%d' % (int(self.chatresize)))
        config.set(self.name, 'screen', self.screenName)
        config.set(self.name, 'enabled', '%d' % (int(self.enabled)))
        config.set(self.name, 'title', '%d' % (int(self.showtitle)))
        config.set(self.name, 'hideinactive', '%d' % (int(self.hideinactive)))
        if self.url:
            config.set(self.name, 'url', self.url)
            if ',' in self.url:
                self.parent.reinit()
        with open(self.configFileName, 'w') as file:
            config.write(file)

    @pyqtSlot()
    def on_click(self):
        self.runJS(
            "document.getElementsByClassName('source-url')[0].value;", self.on_url)

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
        infoListener = "if(typeof console.oldlog === 'undefined'){console.oldlog=console.log;}window.consoleCatchers=[];console.log = function(text,input){if(typeof input !== 'undefined'){window.consoleCatchers.forEach(function(item,index){item(input)})}else{console.oldlog(text);}};"
        catchGuild = "window.consoleCatchers.push(function(input){if(input.cmd == 'GET_GUILD'){window.guilds=input.data.id}})"
        catchChannel = "window.consoleCatchers.push(function(input){if(input.cmd == 'GET_CHANNELS'){window.channels = input.data.channels;}})"

        self.runJS(skipIntro)
        self.runJS(hideLogo)
        self.runJS(resizeContents)
        self.runJS(hidePreview)
        self.runJS(resizeHeader)
        self.runJS(hideClose)
        self.runJS(infoListener)
        self.runJS(catchGuild)
        self.runJS(catchChannel)
        if self.url:
            if 'overlay/voice' in self.url:
                self.runJS(chooseVoice)
            else:
                self.runJS(chooseChat)

    def enableConsoleCatcher(self):
        if self.overlay:
            tweak = "if(typeof console.oldlog === 'undefined'){console.oldlog=console.log;}window.consoleCatchers=[];console.log = function(text,input){if(typeof input !== 'undefined'){window.consoleCatchers.forEach(function(item,index){item(input)})}else{console.oldlog(text);}};"
            self.overlay.page().runJavaScript(tweak)

    def enableShowVoiceTitle(self):
        if self.overlay:
            tweak = "window.consoleCatchers.push(function(input){if(input.cmd == 'GET_CHANNEL'){chan=input.data.name;(function() { css = document.getElementById('title-css'); if (css == null) { css = document.createElement('style'); css.type='text/css'; css.id='title-css'; document.head.appendChild(css); } css.innerText='.voice-container:before{content:\"'+chan+'\";background:rgba(30, 33, 36, 0.95);padding:4px 6px;border-radius: 3px;}';})()}})"
            self.overlay.page().runJavaScript(tweak)

    def enableHideInactive(self):
        if self.overlay and self.url:
            if 'overlay/voice' in self.url:
                tweak = "document.getElementById('app-mount').style='display:none';window.consoleCatchers.push(function(input){if(input.cmd=='AUTHENTICATE'){console.error(input.data.user);window.iAm=input.data.user.username;}if(input.evt=='VOICE_STATE_CREATE' || input.evt=='VOICE_STATE_UPDATE'){if(input.data.nick.toUpperCase()==window.iAm.toUpperCase()){document.getElementById('app-mount').style='display:block';console.error('Showing '+chan)}}if(input.evt=='VOICE_STATE_DELETE'){if(input.data.nick.toUpperCase()==window.iAm.toUpperCase()){document.getElementById('app-mount').style='display:none';console.error('Hiding '+chan)}}});"
                self.overlay.page().runJavaScript(tweak)

    def enableMuteDeaf(self):
        if self.overlay:
            tweak = "window.consoleCatchers.push(function(input){if(input.evt == 'VOICE_STATE_UPDATE'){name=input.data.nick;uState = input.data.voice_state;muteicon = '';if(uState.self_mute || uState.mute){muteicon='<img src=\\'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAABhMAAAYJQE8CCw1AAAAB3RJTUUH5AUGCx0VMm5EjgAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeBDhcAAABzSURBVDjLxZIxCsAwCEW/oT1P7z93zZJjeIYMv0sCIaBoodTJDz6/JgJfBslOsns1xYONvK66JCeqAC4ALTz+dJvOo0lu/zS87p2C98IdHlq9Buo5D62h17amScMk78hBWXB/DUdP2fyBaINjJiJy4o94AM8J8ksz/MQjAAAAAElFTkSuQmCC\\' style=\\'height:0.9em;\\'>';}deaficon = '';if(uState.self_deaf || uState.deaf){deaficon='<img src=\\'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAABhMAAAYJQE8CCw1AAAAB3RJTUUH5AUGCx077rhJQQAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeBDhcAAACNSURBVDjLtZPNCcAgDIUboSs4iXTGLuI2XjpBz87g4fWiENr8iNBAQPR9ef7EbfsjAEQAN4A2UtCcGtyMzFxjwVlyBHAwTRFh52gqHDVnF+6L1XJ/w31cp7YvOX/0xlOJ254qYJ1ZLTAmPWeuDVxARDurfBFR8jovMLEKWxG6c1qB55pEuQOpE8vKz30AhEdNuXK0IugAAAAASUVORK5CYII=\\' style=\\'height:0.9em;\\'>';}spans = document.getElementsByTagName('span');for(i=0;i<spans.length;i++){if(spans[i].innerHTML.startsWith(name)){text = name + muteicon + deaficon;spans[i].innerHTML = text;}}}});"
            self.overlay.page().runJavaScript(tweak)

    def runJS(self, string, retFunc=None):
        if retFunc:
            self.settingWebView.page().runJavaScript(string, retFunc)
        else:
            self.settingWebView.page().runJavaScript(string)

    def applyTweaks(self):
        self.enableConsoleCatcher()
        if self.right:
            self.addCSS(
                'cssrightalign', 'li.voice-state{ direction:rtl; }.avatar{ float:right !important; }.user{ display:flex; }.voice-container{margin-top:30px;}.voice-container:before{position:fixed;right:0px;top:0px;}')
        else:
            self.delCSS('cssrightalign')
        if self.showtitle:
            self.enableShowVoiceTitle()
        if self.mutedeaf:
            self.enableMuteDeaf()
        if self.hideinactive:
            self.enableHideInactive()
        if self.chatresize:
            self.addCSS(
                'cssflexybox', 'div.chat-container { width: 100%; height: 100%; top: 0; left: 0; position: fixed; display: flex; flex-direction: column; } div.chat-container > .messages { box-sizing: border-box; width: 100%; flex: 1; }')
        else:
            self.delCSS('cssflexybox')

    def addCSS(self, name, css):
        if self.overlay:
            js = '(function() { css = document.getElementById(\'%s\'); if (css == null) { css = document.createElement(\'style\'); css.type=\'text/css\'; css.id=\'%s\'; document.head.appendChild(css); } css.innerText=\'%s\';})()' % (name, name, css)
            self.overlay.page().runJavaScript(js)

    def delCSS(self, name):
        if self.overlay:
            js = "(function() { css = document.getElementById('%s'); if(css!=null){ css.parentNode.removeChild(css);} })()" % (
                name)
            self.overlay.page().runJavaScript(js)

    @pyqtSlot()
    def toggleEnabled(self, button=None):
        self.enabled = self.enabledButton.isChecked()
        if self.enabled:
            self.showOverlay()
        else:
            self.hideOverlay()

    @pyqtSlot()
    def toggleTitle(self, button=None):
        self.showtitle = self.showTitle.isChecked()
        if self.showtitle:
            self.enableShowVoiceTitle()

    @pyqtSlot()
    def toggleMuteDeaf(self, button=None):
        self.mutedeaf = self.muteDeaf.isChecked()
        if self.muteDeaf.isChecked():
            self.enableMuteDeaf()

    @pyqtSlot()
    def toggleHideInactive(self, button=None):
        self.hideinactive = self.hideInactive.isChecked()
        if self.hideinactive:
            self.enableHideInactive()

    @pyqtSlot()
    def toggleChatResize(self, button=None):
        self.chatresize = self.chatResize.isChecked()
        self.applyTweaks()

    @pyqtSlot()
    def toggleRightAlign(self, button=None):
        self.right = self.rightAlign.isChecked()
        self.applyTweaks()

    @pyqtSlot()
    def changeValueFL(self):
        self.posXL = self.settingsDistanceFromLeft.value()
        self.moveOverlay()

    @pyqtSlot()
    def changeValueFR(self):
        self.posXR = self.settingsDistanceFromRight.value()
        self.moveOverlay()

    @pyqtSlot()
    def changeValueFT(self):
        self.posYT = self.settingsDistanceFromTop.value()
        self.moveOverlay()

    @pyqtSlot()
    def changeValueFB(self):
        self.posYB = self.settingsDistanceFromBottom.value()
        self.moveOverlay()

    def fillPositionWindowOptions(self):
        self.settingsDistanceFromLeft.valueChanged[int].connect(
            self.changeValueFL)
        self.settingsDistanceFromLeft.setMaximum(self.size.width())
        self.settingsDistanceFromLeft.setValue(self.posXL)
        self.settingsDistanceFromRight.valueChanged[int].connect(
            self.changeValueFR)
        self.settingsDistanceFromRight.setMaximum(self.size.width())
        self.settingsDistanceFromRight.setValue(self.posXR)
        self.settingsDistanceFromTop.valueChanged[int].connect(
            self.changeValueFT)
        self.settingsDistanceFromTop.setMaximum(self.size.height())
        self.settingsDistanceFromTop.setInvertedAppearance(True)
        self.settingsDistanceFromTop.setValue(self.posYT)
        self.settingsDistanceFromBottom.valueChanged[int].connect(
            self.changeValueFB)
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
            logger.warning(
                "Chose screen %r as fallback because %r could not be matched", screen.name(), self.screenName)

        # Fill Info!
        self.size = screen.size()
        self.screenName = s.name()
        self.screenOffset = screen.availableGeometry()
        if self.position:
            self.settingsAspectRatio.updateScreen(
                self.size.width(), self.size.height())
            self.fillPositionWindowOptions()
            self.screenShot(screen)
        self.moveOverlay()

    def showPosition(self):
        if self.position is not None:
            self.position.show()
        else:
            # Positional Settings Window
            self.position = QtWidgets.QWidget()
            self.position.setWindowTitle('Overlay %s Position' % (self.name))
            self.positionbox = QtWidgets.QVBoxLayout()

            # Use a grid to lay out screen & sliders
            self.settingsGridWidget = QtWidgets.QWidget()
            self.settingsGrid = QtWidgets.QGridLayout()

            # Use the custom Aspect widget to keep the whole thing looking
            # as close to the user experience as possible
            self.settingsAspectRatio = AspectRatioWidget(
                self.settingsGridWidget)

            # Grid contents
            self.settingsPreview = ResizingImage()
            self.settingsPreview.setMinimumSize(1, 1)
            sizePolicy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            self.settingsPreview.setSizePolicy(sizePolicy)
            self.settingsDistanceFromLeft = QtWidgets.QSlider(
                QtCore.Qt.Horizontal)
            self.settingsDistanceFromRight = QtWidgets.QSlider(
                QtCore.Qt.Horizontal)
            self.settingsDistanceFromTop = QtWidgets.QSlider(
                QtCore.Qt.Vertical)
            self.settingsDistanceFromBottom = QtWidgets.QSlider(
                QtCore.Qt.Vertical)

            # Screen chooser
            self.settingsScreen = QtWidgets.QComboBox()

    #        self.position.setMinimumSize(600,600)
            # Save button
            self.settingSave = QtWidgets.QPushButton("Save")

            # Fill Screens, Choose the screen if config is set
            self.populateScreenList()

            self.settingSave.clicked.connect(self.on_save_position)
            self.settingsScreen.currentIndexChanged.connect(self.changeScreen)

            self.settingsGrid.addWidget(self.settingsPreview, 0, 0)
            self.settingsGrid.addWidget(self.settingsDistanceFromLeft, 1, 0)
            self.settingsGrid.addWidget(self.settingsDistanceFromRight, 2, 0)
            self.settingsGrid.addWidget(self.settingsDistanceFromTop, 0, 1)
            self.settingsGrid.addWidget(self.settingsDistanceFromBottom, 0, 2)
            self.settingsGridWidget.setLayout(self.settingsGrid)
            self.positionbox.addWidget(self.settingsScreen)
            self.positionbox.addWidget(self.settingsAspectRatio)
            self.position.setLayout(self.positionbox)
            self.positionbox.addWidget(self.settingSave)
            self.fillPositionWindowOptions()
            self.position.show()

    def showSettings(self):
        if self.settings is not None:
            self.settings.show()
        else:
            self.settings = QtWidgets.QWidget()
            self.settings.setWindowTitle('Overlay %s Layout' % (self.name))
            self.settingsbox = QtWidgets.QVBoxLayout()
            self.settingWebView = QWebEngineView()
            self.rightAlign = QtWidgets.QCheckBox("Right Align")
            self.muteDeaf = QtWidgets.QCheckBox("Show mute and deafen")
            self.chatResize = QtWidgets.QCheckBox("Large chat box")
            self.showTitle = QtWidgets.QCheckBox("Show room title")
            self.hideInactive = QtWidgets.QCheckBox(
                "Hide voice channel when inactive")
            self.enabledButton = QtWidgets.QCheckBox("Enabled")
            self.settingTakeUrl = QtWidgets.QPushButton("Use this Room")
            self.settingTakeAllUrl = QtWidgets.QPushButton("Use all Rooms")

            self.settings.setMinimumSize(400, 400)
            self.settingTakeUrl.clicked.connect(self.on_click)
            self.settingTakeAllUrl.clicked.connect(self.getAllRooms)
            self.settingWebView.loadFinished.connect(self.skip_stream_button)
            self.rightAlign.stateChanged.connect(self.toggleRightAlign)
            self.rightAlign.setChecked(self.right)
            self.muteDeaf.stateChanged.connect(self.toggleMuteDeaf)
            self.muteDeaf.setChecked(self.mutedeaf)
            self.showTitle.stateChanged.connect(self.toggleTitle)
            self.showTitle.setChecked(self.showtitle)
            self.hideInactive.stateChanged.connect(self.toggleHideInactive)
            self.hideInactive.setChecked(self.hideinactive)
            self.enabledButton.stateChanged.connect(self.toggleEnabled)
            self.enabledButton.setChecked(self.enabled)
            self.chatResize.stateChanged.connect(self.toggleChatResize)
            self.chatResize.setChecked(self.chatresize)

            self.settingWebView.load(QtCore.QUrl(
                "https://streamkit.discord.com/overlay"))

            self.settingsbox.addWidget(self.settingWebView)
            self.settingsbox.addWidget(self.rightAlign)
            self.settingsbox.addWidget(self.muteDeaf)
            self.settingsbox.addWidget(self.chatResize)
            self.settingsbox.addWidget(self.showTitle)
            self.settingsbox.addWidget(self.hideInactive)
            self.settingsbox.addWidget(self.enabledButton)
            self.settingsbox.addWidget(self.settingTakeUrl)
            self.settingsbox.addWidget(self.settingTakeAllUrl)
            self.settings.setLayout(self.settingsbox)
            self.settings.show()

    def screenShot(self, screen):
        screenshot = screen.grabWindow(0)
        self.settingsPreview.setImage(screenshot)
        self.settingsPreview.setContentsMargins(0, 0, 0, 0)

    def showOverlay(self):
        if self.overlay:
            return
        self.overlay = QWebEngineView()
        self.overlay.page().setBackgroundColor(QtCore.Qt.transparent)
        self.overlay.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.overlay.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.overlay.setWindowFlags(
            QtCore.Qt.X11BypassWindowManagerHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.WindowTransparentForInput |
            QtCore.Qt.WindowDoesNotAcceptFocus |
            QtCore.Qt.NoDropShadowWindowHint |
            QtCore.Qt.WindowSystemMenuHint |
            QtCore.Qt.WindowMinimizeButtonHint
        )
        self.overlay.loadFinished.connect(self.applyTweaks)
        self.overlay.load(QtCore.QUrl(self.url))

        self.overlay.setStyleSheet("background:transparent;")
        self.overlay.show()
        self.moveOverlay()

    def hideOverlay(self):
        if self.overlay:
            self.overlay.close()
            self.overlay = None

    def delete(self):
        self.hideOverlay()
        if self.settings:
            self.settings.close()
        if self.position:
            self.position.close()
        self.overlay = None

    def getAllRooms(self):
        getChannel = "[window.channels, window.guilds]"
        self.runJS(getChannel, self.gotAllRooms)

    def gotAllRooms(self, message):
        sep = ''
        url = ''
        for chan in message[0]:
            if chan['type'] == 2:
                url += sep+"https://streamkit.discord.com/overlay/voice/%s/%s?icon=true&online=true&logo=white&text_color=%%23ffffff&text_size=14&text_outline_color=%%23000000&text_outline_size=0&text_shadow_color=%%23000000&text_shadow_size=0&bg_color=%%231e2124&bg_opacity=0.95&bg_shadow_color=%%23000000&bg_shadow_size=0&limit_speaking=false&small_avatars=false&hide_names=false&fade_chat=0" % (message[1], chan[
                    'id'])
                sep = ','

        if self.overlay:
            self.overlay.load(QtCore.QUrl(url))
        self.url = url
        self.save()
        self.settings.close()
        self.settings = None


def entrypoint():
    def main(app):
        logging.basicConfig(
            format='%(asctime)-15s %(levelname)-8s %(message)s')
        try:
            logging.getLogger().setLevel(os.environ.get("LOGLEVEL", "DEBUG").upper())
        except ValueError as exc:
            logger.warning("Can't set log level: %s", exc)

        a = App(app)
        a.main()
        app.exec()

    app = QtWidgets.QApplication(sys.argv)
    main(app)
