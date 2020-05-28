## Discord Overlay for Linux

A QT browser window to overlay Discord activity over the screen.
![Screenshot](https://user-images.githubusercontent.com/42376598/81101265-274ea100-8f0e-11ea-83dc-1a5476bffe3d.png)
![Witch It](https://user-images.githubusercontent.com/964775/81019917-99b47800-8e5f-11ea-9514-2b3cef24ebbf.png)
![Configuration](https://user-images.githubusercontent.com/535772/82892575-a2243e00-9f47-11ea-8d42-0ec08be39441.png)


## Dependencies

`qt5-webengine pyqt5 python-pyqtwebengine python-pyxdg` (installing with `pip` will install these)

Ubuntu/Debian:

`sudo apt install python3-pyqt5 python3-pyqt5 python3-pyqt5.qtwebengine`


## Installation

Arch: 
Grab it from the AUR: https://aur.archlinux.org/packages/discord-overlay-git

Others:
Clone/Download the repo and `pip install .`

## Usage

On first use a window will show with two buttons "Layout" and "Position"

The first allows you to choose which widget you want to use as your overlay, and make any changes to the style. 

The second shows you which display and where on it the overlay will be placed.

## Known Issues
- Unexpected Discord crashes will leave the overlay in the state it was last showing.
- As this uses Discords StreamKit under the hood there is no way to interact with the overlay itself.

### Tested configurations

- Wayfire/Wayland - Works Perfectly
- Openbox/X11     - Works Perfectly
- Gnome/X11       - Works
- Gnome/Wayland   - Works
