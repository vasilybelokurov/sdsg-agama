"""Patch Agama's setup.py for a reproducible, non-interactive course build.

What the patch does
-------------------
1. Answers setup.py's interactive questions with a fixed policy:
   N for CVXOPT, UNSIO and "reuse Makefile.local"; Y for everything else
   (GSL, Eigen, and "continue without OpenMP" on macOS).
2. Wraps ``urlretrieve`` so that every third-party download must match a
   pinned SHA-256; any unknown URL or hash mismatch aborts the build.
   (setup.py disables HTTPS certificate checks and fetches GSL over HTTP on
   Windows, so the hash check is what makes the downloads trustworthy.)
3. Sets a PEP 440 local version that records the pinned Agama commit.

Usage
-----
    python build/patch_setup.py path/to/Agama/setup.py <agama-commit-sha>
"""
import sys

PINNED = {
    # GSL port for MSVC used by setup.py on Windows
    "http://eugvas.net/software/agama/gsl-master.zip":
        "5be5792b9ed769aa2688b585b496671e314d51cd2da6729673275157a6160dd6",
    # GNU GSL 2.8 used by setup.py on Linux/macOS
    "https://ftpmirror.gnu.org/gnu/gsl/gsl-2.8.tar.gz":
        "6a99eeed15632c6354895b1dd542ed5a855c0f15d9ad1326c6fe2b2c9e423190",
    # Eigen 3.4.1 headers (all platforms)
    "https://gitlab.com/libeigen/eigen/-/archive/3.4.1/eigen-3.4.1.zip":
        "c57ef61ee12f67f55856c1f5de61877e90f2fa8c201dfc541a55dfb3c93be880",
}

OVERRIDE = r'''
# ---- sdsg-agama build policy (inserted by build/patch_setup.py) ----
import hashlib as _sdsg_hashlib
_SDSG_PINNED = %(pinned)r
_sdsg_orig_urlretrieve = urlretrieve
def urlretrieve(url, filename):
    # use the pre-fetched, hash-checked copy if build_wheel.py provided one
    cache = os.environ.get('SDSG_DEPS_CACHE')
    cached = os.path.join(cache, url.rsplit('/', 1)[-1]) if cache else None
    if cached and os.path.isfile(cached):
        import shutil as _sdsg_shutil
        _sdsg_shutil.copyfile(cached, filename)
        say('    [sdsg] using cached %%s\n' %% cached)
    else:
        _sdsg_orig_urlretrieve(url, filename)
    h = _sdsg_hashlib.sha256(open(filename, 'rb').read()).hexdigest()
    if _SDSG_PINNED.get(url) != h:
        say('\nSDSG BUILD ERROR: download not pinned or hash mismatch\n  url=%%s\n  sha256=%%s\n' %% (url, h))
        os._exit(3)   # bypass setup.py's own try/except so the build fails loudly
    say('    [sdsg] verified sha256 of %%s\n' %% url)

def ask(q):
    ql = q.lower()
    answer = not any(k in ql for k in ('cvxopt', 'unsio', 'makefile.local'))
    say(q if q.endswith('\n') else q + '\n')
    say(('y' if answer else 'n') + '    [sdsg build policy]\n')
    return answer
# ---- end of sdsg-agama build policy ----
'''


def main(path, sha):
    src = open(path, encoding="utf-8").read()
    anchor = "if '-h' in sys.argv or '--help' in sys.argv: print(helpstr)"
    assert src.count(anchor) == 1, "anchor for policy override not found"
    src = src.replace(anchor, OVERRIDE % {"pinned": PINNED} + "\n" + anchor)
    ver = "    version          = '1.0',"
    assert src.count(ver) == 1, "version line not found"
    src = src.replace(ver, "    version          = '1.0+sdsg.%s'," % sha[:7])
    open(path, "w", encoding="utf-8").write(src)
    print("patched", path, "version 1.0+sdsg.%s" % sha[:7])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
