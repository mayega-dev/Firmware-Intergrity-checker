# Packaging as a standalone executable

Produces a folder (`dist/FirmwareIntegrityMonitor/`) containing an
executable plus everything it needs - no Python install required on the
machine that runs it.

## The one hard constraint: no cross-compiling

PyInstaller bundles the actual interpreter and compiled libraries it finds
*on the machine it's running on*. There's no way around this - **a Windows
`.exe` has to be built by running PyInstaller on Windows.** Running it on
Linux (natively or in Docker) can only ever produce a Linux binary. This
isn't a limitation of this project's setup specifically; it's true of
PyInstaller (and most tools like it) in general.

Practically, that means:
- **Linux executable**: buildable right now, from your existing Ubuntu +
  Docker setup. See below.
- **Windows executable**: needs to actually run on a Windows machine at
  some point. If you don't have one:
  - A Windows VM (VirtualBox/VMware/Hyper-V, or a cloud VM) works fine -
    it just needs to be genuinely Windows, not Wine-on-Linux (technically
    possible, notoriously unreliable for GUI apps with native
    dependencies like Qt - not recommended for something you intend to
    actually distribute).
  - Borrow a Windows machine for the ~10 minutes the build takes.
  - GitHub Actions has free Windows runners if this project ends up in a
    repo - `windows-latest` running `packaging\build_windows.ps1` would
    produce a downloadable build artifact with zero local Windows access
    needed. Worth doing if you'll rebuild this more than once or twice.

## Building the Linux executable (Docker - recommended)

```
docker compose build dashboard-package-linux
docker compose run --rm dashboard-package-linux
```

Output: `dashboard/dist/FirmwareIntegrityMonitor/` on your host (mounted
out of the container, same pattern as everything else in this project).
Run it directly:
```
./dashboard/dist/FirmwareIntegrityMonitor/FirmwareIntegrityMonitor
```

**Portability caveat, stated plainly**: this binary is linked against the
build container's library versions (Debian "bookworm" base). It'll run
on this machine and reasonably similar recent Debian/Ubuntu systems, but
isn't a "runs on literally any Linux distro" build - that would need an
old-glibc base image (the same idea as the "manylinux" images used for
distributing Python packages), which is more setup than this project
needs unless you're specifically distributing to unknown target systems.
Flag it if that becomes a real requirement and I'll adjust
`packaging/Dockerfile.build`.

## Building the Linux executable (native, no Docker)

If you'd rather not use Docker for this step:
```
./packaging/build_linux.sh
```
Same output location. Needs Python 3.11+ on the host; the script creates
its own venv (`.venv-build/`) so it won't touch any Python environment you
already have.

## Building the Windows executable

On an actual Windows machine, with Python 3.11+ installed (from
python.org - tick "Add python.exe to PATH" during install):
```powershell
cd dashboard
.\packaging\build_windows.ps1
```
Output: `dashboard\dist\FirmwareIntegrityMonitor\FirmwareIntegrityMonitor.exe`

## What's actually verified vs. what isn't

Honest accounting, since I have neither PyInstaller nor a Windows machine
in the sandbox that produced this:

**Verified:**
- `main.py`'s path-resolution logic (the thing that finds `theme.qss`
  once bundled) - tested directly against both normal execution and a
  simulated frozen (`sys.frozen`/`sys._MEIPASS`) environment; both
  resolve to the correct file.
- `packaging/dashboard.spec` - valid Python syntax (PyInstaller spec files
  are executed as Python).
- `build_linux.sh` - valid bash syntax.
- The icon files (`packaging/icon/app.ico`, `app.png`) - generated and
  visually confirmed (shield + checkmark, matches the dashboard's accent
  color).

**Not verified - this sandbox has no network access to install
PyInstaller, and no Windows environment at all:**
- Whether `pyinstaller packaging/dashboard.spec` actually completes
  successfully end to end.
- Whether the resulting executable launches, renders correctly, and can
  open a serial port on a real machine.
- `build_windows.ps1` - PowerShell syntax was written carefully but not
  executed anywhere; Windows-specific behavior (path separators, the
  venv activation script name) should be correct but is unverified.

**Run the Linux build first and tell me what happens** - same approach as
every other piece of this project so far. Two specific things worth
checking once you have a built executable:
1. Does the window look identical to running `python main.py` directly
   (theme applied, fonts look right)?
2. Does Settings → port detection still work the same way (the grouped
   ESP32-devices/other-ports list)?

## Common issues if the build fails or misbehaves

- **`ImportError: libgssapi_krb5.so.2: cannot open shared object file`
  during the build itself** (or a similarly-named missing `.so` for some
  other Qt module you don't actually use, e.g. `QtSql`, `QtPrintSupport`):
  a known PyInstaller + PySide6 interaction, not a bug in this app's code.
  PyInstaller loads *every* Qt submodule's hook script during analysis
  just to read what it excludes - some of those hook scripts (QtNetwork's,
  checking OpenSSL support) run an isolated-process import of their module
  as an unconditional side effect of being loaded, which fails if a system
  library that module's `.so` links against isn't installed, even though
  the app never imports that module. `packaging/Dockerfile.build` already
  includes `libgssapi-krb5-2` (fixes the `QtNetwork` case) and `libcups2`
  (pre-empts the same pattern for `QtPrintSupport`). If a *different*
  module hits this, the fix is identical: `apt-get install` whichever
  `.so` the error names, add it to `Dockerfile.build`, rebuild.

- **"Could not load the Qt platform plugin 'xcb'" when running the built
  executable** (Linux): the target machine is missing the same X11/GL
  libraries the Docker build container has. Install them:
  `sudo apt install libgl1 libxkbcommon-x11-0 libxcb-cursor0` (the full
  list is in `packaging/Dockerfile.build`) - or just run it on the same
  machine you built it on, which already has them.
- **Executable seems to hang or shows nothing on first launch**: PyInstaller
  bundles can be slow to start the very first time due to filesystem
  caching. Give it a few seconds before assuming it's broken.
- **Windows SmartScreen warning ("Windows protected your PC")**: expected
  for any unsigned `.exe` - not a sign of a broken build. "More info" →
  "Run anyway". Removing this warning for other people who'll run it
  requires code-signing (an actual certificate, generally a paid one from
  a CA) - worth doing if you're distributing this beyond yourself, not
  necessary just to run it yourself.
- **Antivirus flags the executable**: PyInstaller-built executables
  occasionally get flagged by antivirus heuristics (self-extracting/
  bundled executables in general trigger this, not anything specific to
  this project's code) - a known, common false-positive pattern for
  PyInstaller apps generally. If it's a real concern for distribution,
  code-signing (same as above) also helps here.
- **Font looks different from the Docker-run version**: the Linux
  executable relies on whatever fonts are actually installed on the
  machine running it - the Docker image installs `fonts-noto-core`
  specifically for consistent rendering, but a standalone executable
  doesn't bundle fonts. `sudo apt install fonts-noto-core` on the target
  machine for the same look, or it'll fall back through the theme's font
  stack (`Segoe UI`, `Inter`, `Helvetica Neue`, `Arial`) to whatever's
  available - fine on Windows (Segoe UI is built in) and macOS, more
  variable on Linux depending on what's installed.
