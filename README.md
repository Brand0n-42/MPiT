# MPiT V1.0 (music Player in Terminal)

MPiT is a minimalistic MP3 player that lives in your terminal.

MPiT should work on Linux, Windows, and macOS.

**HOW TO INSTALL :** Download MPiT.py

**HOW TO RUN :** python MPiT.py


By default, MPiT loads MP3 files from: ` ~/Music `.
You can specify a custom directory as a command-line argument.
` python MPiT.py /path/to/music `

---

### Controls
| Key                   | Action                     |
| ----------------------| -------------------------- |
| up/down arrow key     | Navigate song list         |
| Space                 | Play / Pause               |
| left/right  arrow key | Decrease / Increase volume |
| q                     | Quit                       |

---

### Features:
* scrollable song list
* Autoplays next song in list
* Volume control
* Live updating progress bar


### Requirements/Dependencies
* minimal terminal size : 8x9 characters
* Python 3.8+
* pygame
* mutagen

This project is licensed under the MIT License — see the LICENSE file for details.
