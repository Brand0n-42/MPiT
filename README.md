# MPiT V1.1.2 (music Player in Terminal)

MPiT is a minimalistic Music player that lives in your terminal.

MPiT should work on Linux, Windows, and macOS.

MPiT supports MP3,OGG and WAV files.

---

By default, MPiT loads files from: ` ~/Music `.
You can specify a custom directory as a command-line argument.
` python MPiT.py -d PATH `

---

### Controls
| Key                   | Action                     |
| ----------------------| -------------------------- |
| up/down arrow key     | Navigate song list         |
| Space                 | Play / Pause               |
| left/right  arrow key | Decrease / Increase volume |
| q                     | Quit                       |
| n                     | play next song             |

---

### Features:
* scrollable song list
* Autoplays next song in list
* Volume control
* Live updating progress bar
* Can play MP3,OGG and WAV files


### Requirements/Dependencies
* minimal terminal size : 8x9 characters
* Python 3.8+
* pygame
* mutagen

This project is licensed under the MIT License — see the LICENSE file for details.
