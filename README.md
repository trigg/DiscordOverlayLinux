## Discord Overlay for Linux

A QT browser window to overlay Discord activity over the screen.
![Screenshot from 2020-05-05 20-22-25](https://user-images.githubusercontent.com/42376598/81101265-274ea100-8f0e-11ea-83dc-1a5476bffe3d.png)
![Witch It](https://user-images.githubusercontent.com/964775/81019917-99b47800-8e5f-11ea-9514-2b3cef24ebbf.png)


## Dependencies

`qt5-webengine pyqt5 python-pyqtwebengine`

Ubuntu/Debian:

`sudo apt install python3-pyqt5 python3-pyqt5.qtwebengine`


## Installation

Arch: 
Grab it from the AUR: https://aur.archlinux.org/packages/discord-overlay-git

Others:
Download and run with Python3

## Usage

On first launch a setup-window will appear. First choose either 'OBS' or 'XSplit'. There is no functional difference.

From there choose which widget you want to use as your overlay from the top, and make any changes to the style. Press the 'Use this overlay' button

Adjust the sliders to position the window, these correspond to invisible padding around the overlay, in the current order:
- Distance from left of screen
- Distance from right of screen
- Distance from top of screen
- Distance from bottom of screen


## Known Issues
- If loaded before Discord is logged in no display will show. Quite possible that unexpected Discord crashes will cause the same issue

### Tested configurations

- Wayfire/Wayland - Works Perfectly
- Openbox/X11     - Works Perfectly
- Gnome/X11       - Works
