## Discord Overlay for Linux

A QT/X11 (much to my distress) browser window to overlay Discord activity over the screen.

## Dependencies

`qt5-webengine pyqt5 python-pyqtwebengine`

Ubuntu/Debian:

`sudo apt install python3-pyqt5 python3-pyqt5.qtwebengine`

## Usage

On first launch a setup-window will appear. First choose either 'OBS' or 'XSplit'. I'm convinced there's no difference but why not use this as a show of faith.

From there choose which widget you want to use as your overlay from the top, and make and changes to the style. Press the 'Use this' button

Adjust the sliders to position the window, these correspond to invisible padding around the overlay, in the current order:
- Distance from left of screen
- Distance from right of screen
- Distance from top of screen
- Distance from bottom of screen


## Known Issues

- Can't close. use `pkill overlay-qt5.py` to stop.
- If loaded before Discord is logged in no display will show. Quite possible that unexpected Discord crashes will cause the same issue

### Tested configurations

- Wayfire/Wayland - Works Perfectly
- Openbox/X11     - Works Perfectly
- Gnome/X11       - Works

- 
