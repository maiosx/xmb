# XMB Menu for Omarchy

A full-screen, PS3-inspired cross-media-bar interface for Omarchy's main menu.
It preserves the existing menu structure, application launcher, providers,
actions, search, and `SUPER + SPACE` shortcut while replacing the presentation
with an animated horizontal-and-vertical XMB layout.

![XMB Menu preview](preview.png)

## Features

- Fixed-position horizontal category carousel
- Inline vertical item carousel
- Global search across menu entries and applications
- Animated translucent background ribbons
- Keyboard, mouse-wheel, touchpad, and click navigation
- Focused-monitor presentation
- Existing Omarchy top bar remains unchanged
- Reversible replacement for the packaged `omarchy.menu`

## Requirements

- Omarchy 4 / Quattro with the Quickshell plugin system
- No third-party packages or services

The plugin reads Omarchy's existing menu definitions and uses the commands and
application data already provided by the system.

## Install

```bash
omarchy plugin add https://github.com/surfacedP/omarchy-xmb-menu.git --enable
```

Enabling the plugin routes the existing Omarchy menu shortcut to the XMB
interface. The packaged menu is not modified.

## Controls

- Left / Right: choose a root category
- Up / Down: choose an item
- Mouse wheel / two-finger touchpad: scroll using the system sensitivity
- Click: open an item or choose a category
- Enter / Right: open or run
- Left / Backspace: go back inside nested menus
- Escape or `SUPER + SPACE`: close
- Type: search all menu entries and applications
- Delete: uninstall a selected application, with confirmation

## Update

```bash
omarchy plugin update io.github.maiosx.xmb
```

## Disable or remove

Disable the XMB interface while keeping it installed:

```bash
omarchy plugin disable io.github.maiosx.xmb
```

Remove it completely:

```bash
omarchy plugin remove io.github.maiosx.xmb
```

Disabling or removing the plugin restores the packaged `omarchy.menu`. Your
Omarchy menu configuration and top bar are not deleted or overwritten.

## Configuration

The plugin deliberately uses the standard Omarchy menu configuration, including
user additions in `~/.config/omarchy/extensions/omarchy-menu.jsonc`. It does not
introduce a separate menu database.

## Attribution and trademarks

This project is derived from the MIT-licensed Omarchy menu implementation by
David Heinemeier Hansson and contributors. The XMB-inspired visual presentation
and plugin modifications are maintained by Patrick Brook.

"PlayStation" and "PS3" are trademarks of Sony Interactive Entertainment.
This unofficial community project is not affiliated with or endorsed by Sony.
No Sony artwork, firmware, or other proprietary assets are included.

## License

[MIT](LICENSE)
