"""Remove build-only files from an Agama wheel and repack it.

setup.py copies test executables (exe/), third-party build trees (extras/),
the static library and Makefile.local (which records build-machine paths)
into the package. None of these are needed to ``import agama``; the
executables also confuse wheel-repair tools (delocate/delvewheel).

Usage
-----
    python build/strip_wheel.py dist/agama-*.whl outdir/
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

REMOVE_DIRS = ["exe", "extras"]
REMOVE_FILES = ["agama.a", "agama.lib", "Makefile.local"]


def main(wheel, outdir):
    wheel = pathlib.Path(wheel).resolve()
    outdir = pathlib.Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.check_call([sys.executable, "-m", "wheel", "unpack", str(wheel), "-d", tmp])
        root = next(pathlib.Path(tmp).iterdir())
        pkg = root / "agama"
        removed = []
        for d in REMOVE_DIRS:
            if (pkg / d).is_dir():
                shutil.rmtree(pkg / d)
                removed.append(d + "/")
        for f in REMOVE_FILES:
            if (pkg / f).is_file():
                (pkg / f).unlink()
                removed.append(f)
        ext = [p.name for p in pkg.iterdir() if p.name in ("agama.so", "agama.pyd")]
        assert ext, "compiled extension agama.so/agama.pyd missing from wheel"
        print("removed:", removed, "| extension kept:", ext)
        subprocess.check_call([sys.executable, "-m", "wheel", "pack", str(root), "-d", str(outdir)])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
