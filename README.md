# Uiia × Pibble Christmas Concert

A spinning 3D meme cat and a singing, Santa-hat-wearing pibble in your terminal. Like the spinning ASCII donut, the characters are made of lit 3D surfaces, drawn with **letters and numbers**. Fixed neutral lighting keeps the cat's warm gray-brown coat, the pibble's cream fur, and the red-and-white Santa hat consistent as the animals move. A depth buffer, snowfall, a curled cat tail, and an animated dog mouth complete the concert.

## Run

Requires **Python 3.10+**. No Python packages to install.

```sh
./run.sh
```

The launcher enables colors and plays the local `pibble.mp3`. You can also run `python3 christmas.py` directly to use the original synthesized music.

Use a terminal with true-color support, a dark background, and a monospace font. Maximize the window and reduce the font size for more character cells: **160 × 50** or larger gives much more detail. Both animals fill the available space, and their surface sampling automatically increases at higher resolutions. The interface shows only the project title and exit hint. Press **Ctrl+C** to exit; the program restores your cursor and terminal screen.

## Music

By default, the program synthesizes and loops an **original instrumental Christmas-style bell melody**. The pibble's mouth and bounce follow its beat. These are animated singing gestures; the program does not synthesize vocals.

To play your own copy of Mariah Carey's *All I Want for Christmas Is You*, or another track:

```sh
python3 christmas.py --music "/path/to/All I Want for Christmas Is You.mp3"
```

Commercial recordings are not included or downloaded. A custom song loops, while the mouth animation keeps its own 144 BPM rhythm; it does not analyze or lip-sync to your recording.

Audio uses the first installed compatible command: macOS's built-in `afplay`, `ffplay` (FFmpeg), `play` (SoX), or `aplay` (WAV only). On Linux or Windows, install one of those players for sound. If no player is available or playback fails, the animation continues silently. Playback runs locally and stops when you exit.

## Options

```sh
python3 christmas.py --no-audio             # silent mode
python3 christmas.py --fps 30               # 1–60 FPS; default 24
python3 christmas.py --plain                # letters and numbers without color
python3 christmas.py --width 120 --height 40
python3 christmas.py --frames 120 --no-audio # short animated preview
python3 christmas.py --help
```

`NO_COLOR` also disables colors. Redirected output automatically becomes a single plain-text frame unless `--frames` is specified:

```sh
python3 christmas.py --width 100 --height 36 > preview.txt
```

The renderer, original music synthesizer, and audio lifecycle are all in `christmas.py`, using only the Python standard library. The animals are stylized 3D approximations of the memes.
