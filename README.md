## Discord Overlay for Linux

A QT/X11 (much to my distress) browser window to overlay Discord activity over the screen.

## Dependencies

`qt5-webengine pyqt5 python-pyqtwebengine`

## Usage

Visit https://streamkit.discord.com/overlay and choose your overlay & settings. On the right copy the URL when done.
create file `~/.discordurl` and paste the URL in, save

## Known Issues

- Proper Fullscreen windows will hide this, but most games have a borderless-window option that works.
- Can't close. use `pkill overlay-qt5.py` to stop.
- If loaded before Discord is logged in no display will show. Quite possible that unexpected Discord crashes will cause the same issue

### Missing features

- Show overlay options to user and craft URL for them, removing manual setup steps
- Location control

### Untested

- Wayland. Although I strongly advise we start a whole different project for that case.
- Anything that isn't Openbox, because I'm stubborn
