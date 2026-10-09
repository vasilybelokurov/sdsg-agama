"""Build a repaired, self-contained Agama wheel for the SDSG course.

Steps: clone Agama at the pinned commit -> apply build policy patch ->
``setup.py bdist_wheel`` -> strip build-only files -> repair the wheel
(delocate on macOS, delvewheel on Windows) so that it carries any runtime
libraries it needs (e.g. vcomp140.dll for OpenMP on Windows).

Run inside the activated build environment (Python 3.12 + numpy + setuptools
+ wheel + delocate/delvewheel; on Windows also the MSVC x64 environment):

    python build/build_wheel.py --out wheelhouse
"""
import argparse
import glob
import os
import pathlib
import platform
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
AGAMA_URL = "https://github.com/GalacticDynamics-Oxford/Agama.git"
AGAMA_SHA = (HERE / "AGAMA_COMMIT").read_text().strip()


def run(cmd, **kw):
    print("+", " ".join(map(str, cmd)), flush=True)
    subprocess.check_call(cmd, **kw)


MIRROR = "https://github.com/vasilybelokurov/sdsg-agama/releases/download/deps-v1/"


def prefetch(cache):
    """Download every pinned dependency into ``cache``: original URL first, then the
    course mirror (a release of this repo); the SHA-256 must match either way."""
    import hashlib
    import urllib.request
    sys.path.insert(0, str(HERE))
    from patch_setup import PINNED
    cache.mkdir(parents=True, exist_ok=True)
    for url, sha in PINNED.items():
        name = url.rsplit("/", 1)[-1]
        dest = cache / name
        for src in (url, MIRROR + name):
            try:
                req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
                data = urllib.request.urlopen(req, timeout=120).read()
            except Exception as e:
                print("  fetch failed:", src, "|", e)
                continue
            if hashlib.sha256(data).hexdigest() == sha:
                dest.write_bytes(data)
                print("  fetched + verified:", name, "from", src)
                break
            print("  HASH MISMATCH from", src)
        else:
            sys.exit("could not obtain pinned dependency " + name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="wheelhouse")
    ap.add_argument("--workdir", default="agama_src")
    args = ap.parse_args()
    out = pathlib.Path(args.out).resolve()
    work = pathlib.Path(args.workdir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    print("python", sys.version, "| machine", platform.machine(), "| platform", sys.platform)
    if sys.version_info[:2] != (3, 12):
        sys.exit("build must use Python 3.12")

    if work.exists():
        shutil.rmtree(work)
    run(["git", "clone", "--quiet", AGAMA_URL, str(work)])
    run(["git", "-C", str(work), "checkout", "--quiet", AGAMA_SHA])
    run([sys.executable, str(HERE / "patch_setup.py"), str(work / "setup.py"), AGAMA_SHA])

    if sys.platform == "win32":
        for tool in ("cl", "nmake", "msbuild"):
            if shutil.which(tool) is None:
                sys.exit("MSVC tool not on PATH: %s (run inside the x64 MSVC environment)" % tool)

    cache = work.parent / "deps_cache"
    prefetch(cache)
    env = dict(os.environ)
    env["SDSG_DEPS_CACHE"] = str(cache)
    if sys.platform == "darwin":
        # Build only against macOS system libraries: no Homebrew/MacPorts GSL or
        # libomp (they would not exist on student Macs and would raise the
        # minimum macOS version to that of the build machine).
        # Also hide conda from setup.py: it would otherwise link conda's libomp, and a
        # bundled second copy of libomp next to numpy's crashes ("OMP: Error #15").
        for k in ("CFLAGS", "CPPFLAGS", "CXXFLAGS", "LDFLAGS", "CPATH", "LIBRARY_PATH",
                  "CONDA_EXE", "CONDA_PREFIX", "CONDA_PYTHON_EXE", "CONDA_DEFAULT_ENV", "_CE_CONDA"):
            env.pop(k, None)
        bad = ("/opt/homebrew", "/usr/local", "/opt/local")
        env["PATH"] = os.pathsep.join(p for p in env["PATH"].split(os.pathsep)
                                      if not p.startswith(bad))
        env.setdefault("MACOSX_DEPLOYMENT_TARGET", "11.0")
        print("macOS build PATH:", env["PATH"])

    run([sys.executable, "setup.py", "bdist_wheel"], cwd=work, env=env)
    mk = (work / "Makefile.local").read_text()
    print(mk)
    if sys.platform == "darwin" and any(b in mk for b in ("/opt/homebrew", "/usr/local", "/opt/local")):
        sys.exit("Makefile.local refers to Homebrew/MacPorts paths; build is not self-contained")
    raw = glob.glob(str(work / "dist" / "agama-*.whl"))
    assert len(raw) == 1, raw
    stripped = work / "stripped"
    run([sys.executable, str(HERE / "strip_wheel.py"), raw[0], str(stripped)])
    whl = glob.glob(str(stripped / "agama-*.whl"))[0]

    if sys.platform == "darwin":
        arch = platform.machine()
        deps = subprocess.run(["delocate-listdeps", "--all", whl], capture_output=True, text=True).stdout
        print("dependencies:\n" + deps)
        nonsys = [d for d in deps.split() if d.startswith("/") and not d.startswith(("/usr/lib/", "/System/"))]
        if nonsys:
            sys.exit("agama.so depends on non-system libraries: %s" % nonsys)
        run(["delocate-wheel", "--require-archs", arch, "-w", str(out), "-v", whl])
    elif sys.platform == "win32":
        run([sys.executable, "-m", "delvewheel", "show", whl])
        run([sys.executable, "-m", "delvewheel", "repair", "-w", str(out), whl])
        # the repaired wheel must bundle the OpenMP runtime
        import zipfile
        rep = glob.glob(str(out / "agama-*.whl"))[0]
        names = zipfile.ZipFile(rep).namelist()
        bundled = [n for n in names if n.lower().endswith(".dll")]
        print("bundled DLLs:", bundled)
        if not any("vcomp140" in n.lower() for n in bundled):
            sys.exit("vcomp140.dll was not bundled into the wheel")
    else:
        shutil.copy(whl, out)

    for w in glob.glob(str(out / "agama-*.whl")):
        print("BUILT", w, os.path.getsize(w), "bytes")


if __name__ == "__main__":
    main()
