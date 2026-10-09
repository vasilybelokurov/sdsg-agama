"""Write docs/index.html: a pip ``--find-links`` page for the released wheels.

Each link points at a GitHub Release asset and carries a ``#sha256=`` fragment,
which pip verifies automatically when it downloads the wheel.

Usage
-----
    python build/make_index.py <release-tag> wheels/*.whl
"""
import hashlib
import html
import pathlib
import sys
import urllib.parse

REPO = "vasilybelokurov/sdsg-agama"


def main(tag, wheels):
    rows = []
    sums = []
    for w in sorted(map(pathlib.Path, wheels)):
        sha = hashlib.sha256(w.read_bytes()).hexdigest()
        url = "https://github.com/%s/releases/download/%s/%s" % (REPO, tag, urllib.parse.quote(w.name))
        rows.append('<a href="%s#sha256=%s">%s</a><br>' % (html.escape(url), sha, html.escape(w.name)))
        sums.append("%s  %s" % (sha, w.name))
    out = pathlib.Path("docs")
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(
        "<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\"><title>sdsg-agama wheels</title></head>\n<body>\n"
        "<h1>AGAMA wheels for SDSG (%s)</h1>\n<p>Install instructions: "
        "<a href=\"https://github.com/%s/blob/main/GUIDE.md\">GUIDE.md</a></p>\n%s\n</body></html>\n"
        % (html.escape(tag), REPO, "\n".join(rows)))
    (out / ".nojekyll").write_text("")
    pathlib.Path("SHA256SUMS").write_text("\n".join(sums) + "\n")
    print("\n".join(sums))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
