# Discord overlay is deprecated
We are now developing [Discover Overlay](https://github.com/trigg/Discover). We strongly advise you try that instead!

## Discord Overlay for Linux

A QT browser window to overlay Discord activity over the screen.
![Screenshot](https://user-images.githubusercontent.com/42376598/81101265-274ea100-8f0e-11ea-83dc-1a5476bffe3d.png)
![Witch It](https://user-images.githubusercontent.com/964775/81019917-99b47800-8e5f-11ea-9514-2b3cef24ebbf.png)
![Configuration](https://user-images.githubusercontent.com/535772/82892575-a2243e00-9f47-11ea-8d42-0ec08be39441.png)


## Dependencies

Python `pip` will deal with dependencies, but for posterity the script needs 

`qt5-webengine pyqt5 python-pyqtwebengine python-pyxdg`

## Installation

Manual
```
git clone https://github.com/trigg/DiscordOverlayLinux.git
cd DiscordOverlayLinux
python -m pip install PyQtWebEngine
python -m pip install .
```

## Usage

On first use a window will show up with two buttons "Layout" and "Position"

The first allows you to choose which widget you want to use as your overlay, and make any changes to the style. 

The second shows you which display and where on it the overlay will be placed.

Extra Overlays can be added at will

## Known Issues
- Unexpected Discord crashes will leave the overlay in the state it was last showing.
- As this uses Discord's StreamKit under the hood there is no way to interact with the overlay itself.

### Tested configurations

- Wayfire/Wayland - Works
- Openbox/X11     - Works
- Gnome/X11       - Works
- Gnome/Wayland   - Works
