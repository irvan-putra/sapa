# Releasing

The launcher icon shows the app version as numbers only (no "v"). For every new version:

1. Bump `versionCode` and `versionName` in `app/build.gradle`.
2. Run `python3 tools/make_icons.py` (needs `pip install pillow==12.3.0` and DejaVuSans-Bold.ttf from fonts-dejavu-core; the script stops if either differs). It reads `versionName`, redraws the legacy icons and the adaptive foreground from `tools/assets/sapa-sticker.png`, and rewrites `tools/icon-manifest.json`. Pass `X.Y.Z` to override the version.
3. Look at the result: the badge is a full-width strip across the bottom 24% of the visible icon area, and the picture and number stay inside the circle of the visible area. The script checks this and fails if something would be clipped. Open the PNGs in `app/src/main/res/mipmap-xxxhdpi/` and check a longer version still fits.
4. Run `python3 tools/check-icon-version.py`, build, then confirm the built APK's versionName matches the badge.

Do not cut a release only to change the icon.
