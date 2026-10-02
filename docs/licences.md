# Licences

Every dependency, binary, model, dataset, font, clip and track product-in-video uses, with its
licence and whether **commercial ad use** is allowed. A new row comes with the thing it
covers, in the same commit. Not legal advice: where a row says "ask", the user decides.

## Software (node p1-package-ffmpeg, 2026-10-02)

| Item | Version (pinned) | Licence | Used as | Commercial ad output | Source |
|---|---|---|---|---|---|
| numpy | 2.4.6 (wheel `cp311-macosx_14_0_x86_64`, Apple Accelerate; no bundled OpenBLAS or gfortran) | BSD-3-Clause, with bundled parts under 0BSD, MIT, Zlib, CC0-1.0 | library, linked into our process | Yes. Permissive; no restriction on use or on what it computes. | `License-Expression` in the wheel's METADATA; https://numpy.org/doc/stable/license.html |
| Pillow | 12.3.0 (wheel `cp311-macosx_10_10_x86_64`) | MIT-CMU (HPND). Bundled dylibs: libjpeg-turbo (IJG/BSD), libpng (libpng), zlib-ng (Zlib), FreeType (FTL), HarfBuzz (MIT), libtiff (libtiff), libwebp (BSD-3), libavif (BSD-2), OpenJPEG (BSD-2), LittleCMS (MIT), Brotli (MIT), liblzma (0BSD), libxcb/libXau (MIT) | library | Yes. All permissive. | the wheel's LICENSE (lists each bundled library); https://github.com/python-pillow/Pillow/blob/main/LICENSE |
| imageio-ffmpeg | 0.6.0 (wheel `py3-none-macosx_10_9_intel.macosx_10_9_x86_64`) | BSD-2-Clause (the Python wrapper) | library: finds the bundled ffmpeg binary | Yes. | METADATA; https://github.com/imageio/imageio-ffmpeg/blob/master/LICENSE |
| **ffmpeg binary** bundled in imageio-ffmpeg 0.6.0 (`imageio_ffmpeg/binaries/ffmpeg-macos-x86_64-v7.1`, sha256 `4a4a968b98859588e98500ae25973d80a5ca5eed0724222b9f76360dcb72a001`) | FFmpeg 7.1, static, x86_64, built with Apple clang 13; configured `--enable-gpl --enable-version3 --enable-nonfree` with libx264 (x264 core 164 r3075 66a5bc1), libx265, libvpx, libaom, libsvtav1, libass, libfreetype, libharfbuzz and others. The configure line matches evermeet.cx's macOS builds (`--prefix=/Volumes/tempdisk/sw`). | **GPLv3 overall, marked "nonfree": `ffmpeg -L` prints "This version of ffmpeg has nonfree parts compiled in. Therefore it is not legally redistributable."** x264 itself is GPLv2+ (a commercial licence is sold by x264 LLC). | an **external tool**: we run it as a separate process and pipe raw frames into it. We never link it, modify it or ship it. | **Yes, with conditions below.** The GPL covers copying, changing and distributing the program, not what it outputs: "the output of a program is not, in general, covered by the copyright on the code of the program" (GNU GPL FAQ, https://www.gnu.org/licenses/gpl-faq.html#WhatCaseIsOutputGPL). The mp4s are made from our frames, so they are ours (and Haki's) to use in ads. | `ffmpeg -version`, `-buildconf`, `-L`; https://ffmpeg.org/legal.html; https://www.videolan.org/developers/x264.html |
| hatchling | 1.32.4 | MIT | build backend (pure Python, build time only) | n/a (not in outputs) | https://github.com/pypa/hatch/blob/master/LICENSE.txt |
| pytest | 9.1.1 (dev) | MIT | tests only | n/a | METADATA |
| ruff | 0.16.10 (dev) | MIT | lint and format only | n/a | METADATA |

Every pin was checked for an x86_64 macOS wheel before it was added:
`uv pip install --dry-run --no-build --python-platform x86_64-apple-darwin --python-version 3.11 <pkg>`
in a scratch venv, then the wheel filename confirmed on PyPI. `[tool.uv] no-build-package`
forbids building numpy, Pillow or imageio-ffmpeg from source.

### The conditions on the ffmpeg binary (for the user)
1. **Using it to make our ads is fine** (above). Nothing in a rendered mp4 is GPL code.
2. **Don't redistribute the binary.** Because it is built `--enable-nonfree`, FFmpeg itself
   says it is not legally redistributable. Running it on our own Mac, or later on machines
   we run, is use, not distribution. Handing it to someone else (a container image we give
   away, an app we ship) would need a different build: an LGPL or plain-GPL one, with the
   GPL's source obligations. Flag this at the cloud move.
3. **H.264 patents.** H.264 is covered by the Via LA (formerly MPEG LA) AVC patent pool.
   Its terms charge nothing for AVC video delivered free to viewers over the internet
   ("Internet Broadcast AVC Video"), which is what a feed ad is; encoder royalties fall on
   whoever distributes encoders, which we don't. Meta and other platforms re-encode uploads
   anyway. This is the usual position for ad studios, but it is a reading of a licence, not
   advice: **ask before paid distribution at scale outside the ad platforms.**
   https://www.via-la.com/licensing-2/avc-h-264/
