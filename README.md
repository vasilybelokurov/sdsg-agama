# sdsg-agama

Prebuilt [AGAMA](https://github.com/GalacticDynamics-Oxford/Agama) wheels for the
Cambridge Part II course *Stellar Dynamics and Structure of Galaxies* (SDSG), so that
students on Windows and macOS can install AGAMA without a C++ compiler.

**Students: follow [GUIDE.md](GUIDE.md).**

## What is built

| Platform | Wheel tag | Notes |
|---|---|---|
| Windows 10/11, x64 (and Windows 11 on ARM via x64 emulation) | `cp312-win_amd64` | OpenMP runtime (`vcomp140.dll`) bundled |
| macOS 11+ Apple Silicon | `cp312-macosx_11_0_arm64` | single-threaded (no OpenMP) |
| macOS 11+ Intel | `cp312-macosx_11_0_x86_64` | single-threaded (no OpenMP) |

All wheels require **Python 3.12** and are tested with **numpy 2.3** from conda-forge.

## How the wheels are made

- AGAMA source pinned to commit [`60d8d8b`](https://github.com/GalacticDynamics-Oxford/Agama/commit/60d8d8b8dce4eea33e500c34700f28ebc6bbfd7b) (23 Jul 2026). The newer commit `f302756` (25 Aug 2026) does not compile with MSVC (it includes the POSIX header `alloca.h`)
  (see `build/AGAMA_COMMIT`).
- `build/patch_setup.py` makes AGAMA's `setup.py` non-interactive with a fixed policy
  (GSL: yes, Eigen: yes, CVXOPT: no, UNSIO: no) and requires every downloaded
  dependency to match a pinned SHA-256.
- `build/build_wheel.py` builds the wheel, removes build-only files, and repairs it
  (`delvewheel` on Windows, `delocate` checks on macOS). On macOS it builds only
  against system libraries (no Homebrew).
- `.github/workflows/build-test.yml` builds on `windows-2022`, `macos-15`, `macos-15-intel`
  and tests each wheel on fresh runners (`windows-2022`, `windows-2025-vs2026`,
  `windows-11-vs2026-arm`, `macos-15`, `macos-26`, `macos-15-intel`) in exactly the
  environment described in the guide, using `tests/test_course.py` (analytic checks of
  every AGAMA feature used in the course) and `tests/smoke.ipynb` (run through Jupyter).

## Licence and sources

AGAMA's own source is BSD/MIT licensed, but it links the GNU Scientific Library (GSL),
so these binary wheels are distributed under the **GNU GPL** (see AGAMA's `LICENSE`,
included in each wheel). Corresponding sources:

- AGAMA: https://github.com/GalacticDynamics-Oxford/Agama at the pinned commit above
- GSL (macOS builds): GNU GSL 2.8, https://ftpmirror.gnu.org/gnu/gsl/gsl-2.8.tar.gz
  (sha256 `6a99eeed15632c6354895b1dd542ed5a855c0f15d9ad1326c6fe2b2c9e423190`)
- GSL (Windows builds): MSVC port distributed by the AGAMA author,
  http://eugvas.net/software/agama/gsl-master.zip
  (sha256 `5be5792b9ed769aa2688b585b496671e314d51cd2da6729673275157a6160dd6`)
- Eigen 3.4.1 (MPL2, headers only): https://gitlab.com/libeigen/eigen/-/archive/3.4.1/eigen-3.4.1.zip

These are unofficial builds made for teaching; AGAMA is developed by Eugene Vasiliev.
Please cite AGAMA ([Vasiliev 2019, MNRAS 482, 1525](https://doi.org/10.1093/mnras/sty2672)) in any work that uses it.
