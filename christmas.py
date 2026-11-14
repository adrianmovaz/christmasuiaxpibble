#!/usr/bin/env python3
"""A tiny, dependency-free ASCII Christmas concert. Python 3.10+."""

import argparse
import math
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import wave

TAU = math.tau
RAMP = "il1tfLCG08MW"
BEAT = 60 / 144
TREE_TIERS = ((-1.25, .90, 1.65), (-.25, 1.85, 1.25), (.75, 2.80, .85))


class Mesh(list):
    def __init__(self, detail=1.5):
        super().__init__()
        self.detail = detail


def ellipsoid(mesh, center, radii, material="fur", density=28):
    """Sample an ellipsoid and its actual surface normals."""
    density = round(density * getattr(mesh, "detail", 1))
    cx, cy, cz = center
    rx, ry, rz = radii
    for row in range(1, density):
        v = math.pi * row / density
        sv, cv = math.sin(v), math.cos(v)
        for col in range(density * 2):
            u = TAU * col / (density * 2)
            su, cu = math.sin(u), math.cos(u)
            nx, ny, nz = sv * cu / rx, cv / ry, sv * su / rz
            length = math.sqrt(nx * nx + ny * ny + nz * nz)
            mesh.append((cx + rx * sv * cu, cy + ry * cv,
                         cz + rz * sv * su, nx / length, ny / length,
                         nz / length, material))


def triangle(mesh, a, b, c, material="fur", density=25):
    density = round(density * getattr(mesh, "detail", 1))
    ab = tuple(b[i] - a[i] for i in range(3))
    ac = tuple(c[i] - a[i] for i in range(3))
    n = (ab[1] * ac[2] - ab[2] * ac[1],
         ab[2] * ac[0] - ab[0] * ac[2],
         ab[0] * ac[1] - ab[1] * ac[0])
    length = math.sqrt(sum(v * v for v in n))
    n = tuple(v / length for v in n)
    for i in range(density + 1):
        for j in range(density + 1 - i):
            p = tuple(a[k] + ab[k] * i / density + ac[k] * j / density
                      for k in range(3))
            mesh.append((*p, *n, material))


def cat_model(detail=1.5):
    mesh = Mesh(detail)
    ellipsoid(mesh, (0, -.65, 0), (.61, .82, .48))
    ellipsoid(mesh, (0, .49, .04), (.82, .69, .64), density=40)
    for side in (-1, 1):
        front = [(side * .32, .88, .25), (side * .79, .78, .13),
                 (side * .64, 1.55, .02)]
        triangle(mesh, *front)
        triangle(mesh, front[1], front[0], (side * .64, 1.55, -.26))
        triangle(mesh, front[2], front[1], (side * .64, 1.55, -.26))
        triangle(mesh, (side * .44, .98, .28), (side * .70, .92, .20),
                 (side * .63, 1.37, .10), "pink")
        ellipsoid(mesh, (side * .32, .59, .61), (.12, .17, .065), "ink", 15)
        ellipsoid(mesh, (side * .30, .64, .67), (.035, .055, .02), "white", 8)
        ellipsoid(mesh, (side * .17, .25, .62), (.21, .16, .09), "white", 16)
        ellipsoid(mesh, (side * .39, -1.31, .22), (.25, .19, .36), "white", 16)
        for stripe in range(3):
            ellipsoid(mesh, (side * (.47 + stripe * .09), .29 - stripe * .075, .53),
                      (.11, .018, .025), "ink", 8)
    ellipsoid(mesh, (0, .32, .73), (.10, .07, .05), "pink", 12)
    ellipsoid(mesh, (0, .12, .66), (.07, .065, .04), "ink", 10)
    # A curled tail remains visible from the sides and back during the spin.
    for i in range(25):
        a = i / 24 * math.pi * 1.4
        ellipsoid(mesh, (.63 + .40 * math.sin(a), -.90 + i / 24 * .95,
                         -.35 - .35 * math.cos(a)), (.12, .12, .12), density=8)
    return mesh


def pibble_model(detail=1.5):
    mesh = Mesh(detail)
    ellipsoid(mesh, (0, -.71, 0), (.76, .77, .49), "dog")
    ellipsoid(mesh, (0, .41, 0), (.93, .77, .60), "dog", 42)
    for side in (-1, 1):
        ellipsoid(mesh, (side * .83, .89, -.03), (.31, .46, .24), "dog", 22)
        ellipsoid(mesh, (side * .86, .88, .19), (.16, .27, .07), "pink", 16)
        ellipsoid(mesh, (side * .36, .63, .55), (.115, .13, .075), "ink", 16)
        ellipsoid(mesh, (side * .34, .67, .62), (.035, .04, .016), "white", 8)
        ellipsoid(mesh, (side * .23, .19, .59), (.32, .24, .20), "white", 24)
        ellipsoid(mesh, (side * .44, -1.29, .20), (.29, .20, .38), "dog", 16)
    ellipsoid(mesh, (0, .34, .80), (.21, .135, .10), "ink", 18)
    ellipsoid(mesh, (0, -.72, .46), (.38, .49, .08), "white", 20)
    # A red Christmas hat, with a white brim and pompom.
    triangle(mesh, (-.54, 1.02, .32), (.49, 1.05, .32), (.21, 1.90, .05), "red")
    triangle(mesh, (.49, 1.05, .32), (-.54, 1.02, .32), (.21, 1.90, -.29), "red")
    for i in range(12):
        ellipsoid(mesh, (-.53 + i * .094, 1.05, .32), (.10, .105, .12), "white", 8)
    ellipsoid(mesh, (.21, 1.87, .05), (.15, .15, .15), "white", 12)
    return mesh


def tree_model(detail=1.5):
    mesh = Mesh(detail)
    ellipsoid(mesh, (0, -1.45, 0), (.22, .45, .22), "wood", 16)
    # Overlapping cones give the evergreen its tiered silhouette.
    for bottom, top, radius in TREE_TIERS:
        rows = round(36 * detail)
        slope = radius / (top - bottom)
        length = math.sqrt(1 + slope * slope)
        for row in range(rows + 1):
            fraction = row / rows
            y = bottom + (top - bottom) * fraction
            r = radius * (1 - fraction)
            for col in range(rows * 3):
                angle = TAU * col / (rows * 3)
                c, s = math.cos(angle), math.sin(angle)
                mesh.append((r * c, y, r * s,
                             c / length, slope / length, s / length, "pine"))
        # Decorate every side so ornaments remain visible as the tree turns.
        for i in range(8):
            angle = .45 + i * TAU / 8
            fraction = .24 + .13 * (i % 2)
            r = radius * (1 - fraction)
            ellipsoid(mesh, (r * math.cos(angle),
                             bottom + (top - bottom) * fraction,
                             r * math.sin(angle)),
                      (.10, .10, .10), "red" if i % 2 else "gold", 10)
    # Give the star a back and edges so it also catches light as it turns.
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        radius = .27 if i % 2 == 0 else .12
        points.append((radius * math.cos(angle),
                       3.0 + radius * math.sin(angle), .08))
    for i in range(10):
        a, b = points[i], points[(i + 1) % 10]
        back_a, back_b = (*a[:2], -.08), (*b[:2], -.08)
        triangle(mesh, (0, 3.0, .08), a, b, "gold", 10)
        triangle(mesh, (0, 3.0, -.08), back_b, back_a, "gold", 10)
        triangle(mesh, a, back_a, back_b, "gold", 6)
        triangle(mesh, a, back_b, b, "gold", 6)
    return mesh


CAT = None
DOG = None
TREE = None


def palette():
    # Neutral light preserves the meme colors at every point in the animation.
    materials = {
        "fur": (156, 143, 123),   # Ethel's warm gray-brown tabby coat.
        "dog": (244, 232, 210),   # The pale cream pibble puppy.
        "white": (255, 250, 240),
        "pink": (228, 148, 155),
        "red": (220, 30, 42),
        "ink": (38, 34, 32),
        "pine": (38, 132, 66),
        "wood": (116, 75, 43),
        "gold": (255, 204, 65),
    }
    colors = {}
    for material, rgb in materials.items():
        colors[material] = []
        for level in range(32):
            value = .20 + .80 * level / 31
            colors[material].append("\x1b[38;2;%d;%d;%dm" % tuple(int(x * value) for x in rgb))
    return colors


SHADES = palette()
# Fixed upper-left light gives curved surfaces a clear lit and shaded side.
LIGHT = tuple(v / math.sqrt(.70 ** 2 + .65 ** 2 + .80 ** 2)
              for v in (-.70, .65, .80))
# Blinn halfway vector between the light and the camera, looking along +Z.
_half = (LIGHT[0], LIGHT[1], LIGHT[2] + 1)
HALF_LIGHT = tuple(v / math.sqrt(sum(x * x for x in _half)) for v in _half)


def surface_brightness(nx, ny, nz, material, visibility=1):
    """Shade a rotated surface normal with neutral, stationary lighting."""
    diffuse = max(0, nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2])
    highlight = max(0, nx * HALF_LIGHT[0] + ny * HALF_LIGHT[1]
                    + nz * HALF_LIGHT[2]) ** 24
    gloss = .015 if material == "pine" else (.04 if material in ("fur", "dog") else .14)
    if diffuse == 0:
        highlight = 0
    # Low ambient fill keeps shadow detail visible without washing it out.
    return min(1, .09 + visibility * (.86 * diffuse + gloss * highlight))


def tree_shadow(x, y, z):
    """Soft shadows cast by the solid branch tiers toward the fixed light."""
    visibility = 1.0
    for bottom, _, radius in TREE_TIERS:
        distance = bottom - y
        if distance <= .015:
            continue
        # Where the ray to the light crosses the underside of this tier.
        ray_x = x + LIGHT[0] * distance / LIGHT[1]
        ray_z = z + LIGHT[2] * distance / LIGHT[1]
        edge = math.hypot(ray_x, ray_z) - radius
        softness = .10 + distance * .10
        blend = max(0, min(1, .5 + edge / (2 * softness)))
        blend = blend * blend * (3 - 2 * blend)
        visibility = min(visibility, .22 + .78 * blend)
    return visibility


def render(t, width, height, color=True):
    global CAT, DOG, TREE
    scene_height = height - 2
    # Keep the pair close together and fit their entire height, including the hat.
    scale = min((width - 4) / 6.1, (scene_height - 2) / 1.95)
    # Increase surface sampling with terminal resolution, caching until it changes.
    detail = min(4, max(1.5, math.ceil(scale / 18 * 2) / 2))
    if CAT is None or CAT.detail != detail:
        CAT, DOG = cat_model(detail), pibble_model(detail)
        TREE = tree_model(detail)
    grid = [[None] * width for _ in range(scene_height)]
    depth = [[-float("inf")] * width for _ in range(scene_height)]

    def draw(mesh, angle, offset, bob=0, z_offset=0, size=1):
        c, s = math.cos(angle), math.sin(angle)
        for x, y, z, nx, ny, nz, material in mesh:
            xx, zz = c * x + s * z, -s * x + c * z
            # Trace tree shadows in rotated coordinates toward the fixed light.
            shadow_x, shadow_z = xx, zz
            xx, zz = xx * size, zz * size + z_offset
            # Slight perspective makes the near ear and paw larger.
            perspective = 6 / (6 - zz)
            px = int(width / 2 + (offset + xx * perspective) * scale)
            py = int(scene_height * .5 - (y * size * perspective + bob - .23) * scale * .5)
            if not (0 <= px < width and 0 <= py < scene_height):
                continue
            if zz <= depth[py][px]:
                continue
            depth[py][px] = zz
            nx, nz = c * nx + s * nz, -s * nx + c * nz
            visibility = tree_shadow(shadow_x, y, shadow_z) if mesh is TREE else 1
            brightness = surface_brightness(nx, ny, nz, material, visibility)
            level = int(brightness * 31)
            glyph = RAMP[min(len(RAMP) - 1, int(brightness * len(RAMP)))]
            if material == "ink":
                glyph = "0"
            grid[py][px] = (glyph, SHADES[material][level])

    draw(TREE, t * .35, 0, z_offset=-5.5, size=.9)
    draw(CAT, t * 1.8, -1.45, .08 * math.sin(t * 5))
    singing = (math.sin(TAU * t / BEAT) + 1) / 2
    mouth = Mesh(detail)
    ellipsoid(mouth, (0, -.10 - singing * .08, .62),
              (.27, .09 + singing * .20, .12), "ink", 18)
    ellipsoid(mouth, (0, -.19 - singing * .15, .73),
              (.14, .035 + singing * .055, .035), "pink", 12)
    dog_angle = .19 * math.sin(t * 2.2)
    dog_bob = .065 * math.sin(TAU * t / BEAT)
    draw(DOG, dog_angle, 1.45, dog_bob)
    draw(mouth, dog_angle, 1.45, dog_bob)

    # Deterministic snowfall: never changes the user's global random state.
    rng = random.Random(1225)
    for i in range(max(18, width // 2)):
        x = int((rng.random() * width + math.sin(t + i) * 2) % width)
        y = int((rng.random() * scene_height + t * (1 + i % 3)) % scene_height)
        if grid[y][x] is None:
            grid[y][x] = ("1" if i % 3 else "o", "\x1b[38;2;110;150;180m")

    def centered(text):
        return text[:width].center(width)

    header = centered("UIIA x PIBBLE")
    lines = [("\x1b[38;2;255;212;130m" if color else "") + header
             + ("\x1b[0m" if color else "")]
    for row in grid:
        line, previous = [], None
        for cell in row:
            glyph, ink = cell if cell else (" ", None)
            if color and ink and ink != previous:
                line.append(ink)
                previous = ink
            line.append(glyph)
        lines.append("".join(line) + ("\x1b[0m" if color else ""))
    lines.append(centered("Ctrl+C to exit"))
    return "\n".join(lines)


def make_jingle(path):
    """Synthesize an original eight-bar melody, bass, and bell percussion."""
    rate = 22050
    melody = [76, 79, 83, 79, 81, 78, 74, 78,
              79, 83, 86, 83, 81, 79, 78, 74,
              76, 79, 83, 86, 88, 86, 83, 79,
              81, 78, 74, 78, 79, 76, 72, 76]
    roots = [48, 50, 55, 52, 48, 53, 50, 55]
    count = round(len(melody) * BEAT * rate)
    data = bytearray()
    for i in range(count):
        t = i / rate
        beat = t / BEAT
        index = min(len(melody) - 1, int(beat))
        local = (beat - index) * BEAT
        f = 440 * 2 ** ((melody[index] - 69) / 12)
        bell = (math.sin(TAU * f * local) + .35 * math.sin(TAU * f * 2.01 * local))
        bell *= math.exp(-local * 10) * min(1, local * 250)
        bass_f = 440 * 2 ** ((roots[index // 4] - 69) / 12)
        bass = math.sin(TAU * bass_f * local) * math.exp(-local * 7)
        chime = math.sin(TAU * 6100 * local) * math.exp(-local * 65)
        fade = min(1, t * 50, (count / rate - t) * 50)
        sample = (bell * .29 + bass * .20 + chime * .045) * fade
        data.extend(struct.pack("<h", int(max(-1, min(1, sample)) * 25000)))
    with wave.open(str(path), "wb") as wav:
        wav.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        wav.writeframes(data)


class Audio:
    def __init__(self, path):
        self.path = str(path)
        self.process = None
        self.command = None
        for player, flags in (("afplay", []),
                              ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"]),
                              ("play", ["-q"]), ("aplay", ["-q"])):
            executable = shutil.which(player)
            if executable and (player != "aplay" or path.suffix.lower() == ".wav"):
                self.command = [executable, *flags, self.path]
                break
        self.warned = False

    def tick(self):
        if self.command and (self.process is None or self.process.poll() == 0):
            try:
                self.process = subprocess.Popen(self.command, stdin=subprocess.DEVNULL,
                                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError as error:
                self.command = None
                self.warn("Audio could not start: " + str(error))
        elif not self.command:
            self.warn("No audio player found; animation continues silently. See README.md.")
        elif self.process.poll() is not None:
            self.warn("Audio playback failed; animation continues silently.")

    def warn(self, message):
        if not self.warned:
            print(message, file=sys.stderr)
            self.warned = True

    def close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--music", type=Path, help="Play and loop your own local MP3/WAV/etc.")
    parser.add_argument("--no-audio", action="store_true", help="Silent animation")
    parser.add_argument("--plain", action="store_true", help="Disable ANSI colors")
    parser.add_argument("--fps", type=int, default=24, help="Frames per second (1-60)")
    parser.add_argument("--frames", type=int, help="Stop after this many frames (useful for previews)")
    parser.add_argument("--width", type=int, help="Override terminal width (minimum 50)")
    parser.add_argument("--height", type=int, help="Override terminal height (minimum 20)")
    args = parser.parse_args()
    if not 1 <= args.fps <= 60:
        parser.error("--fps must be between 1 and 60")
    for name, minimum in (("width", 50), ("height", 20), ("frames", 1)):
        value = getattr(args, name)
        if value is not None and value < minimum:
            parser.error(f"--{name} must be at least {minimum}")
    if args.music and not args.music.is_file():
        parser.error(f"Music file does not exist: {args.music}")
    is_terminal = sys.stdout.isatty()
    if os.name == "nt" and is_terminal:
        # Enable virtual terminal processing in the Windows console.
        import ctypes
        kernel = ctypes.windll.kernel32
        handle = kernel.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        if kernel.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel.SetConsoleMode(handle, mode.value | 0x0004)
    limit = args.frames if args.frames is not None else (None if is_terminal else 1)
    color = is_terminal and not args.plain and "NO_COLOR" not in os.environ
    audio = None
    with tempfile.TemporaryDirectory(prefix="uiia-pibble-") as temp:
        try:
            if not args.no_audio and is_terminal:
                music = args.music
                if music is None:
                    music = Path(temp) / "original-festive-loop.wav"
                    make_jingle(music)
                audio = Audio(music)
                audio.tick()
            # Warm up model generation before starting the animation clock.
            render(0, 80, 28, False)
            if is_terminal:
                sys.stdout.write("\x1b[?1049h\x1b[?25l\x1b[2J")
            start = time.monotonic()
            frame = 0
            while limit is None or frame < limit:
                size = shutil.get_terminal_size((100, 36))
                width = args.width or max(1, size.columns - 1)
                height = args.height or max(1, size.lines - 1)
                if width < 50 or height < 20:
                    output = "Please resize the terminal to at least 51 columns x 21 rows."
                else:
                    output = render(time.monotonic() - start, width, height, color)
                sys.stdout.write(("\x1b[H\x1b[J" if is_terminal else "") + output + ("" if is_terminal else "\n"))
                sys.stdout.flush()
                if audio:
                    audio.tick()
                frame += 1
                if limit is None or frame < limit:
                    time.sleep(max(0, start + frame / args.fps - time.monotonic()))
        except (KeyboardInterrupt, BrokenPipeError):
            pass
        finally:
            if audio:
                audio.close()
            if is_terminal:
                sys.stdout.write("\x1b[0m\x1b[?25h\x1b[?1049l")
                sys.stdout.flush()


if __name__ == "__main__":
    main()
