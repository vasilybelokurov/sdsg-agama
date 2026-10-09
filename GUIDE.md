# Installing AGAMA for SDSG (Windows and macOS)

This takes about 15 minutes, most of it downloading. You do **not** need a C++ compiler,
Visual Studio or Xcode: AGAMA comes prebuilt for the course.

**You need:** Windows 10 or 11 (64-bit), or Windows 11 on an ARM laptop (Snapdragon / Surface Pro X),
or macOS 11 (Big Sur) or later; about 3 GB of free disk space; an internet connection.
Windows 10 on ARM is not supported.

If anything below does not give the expected result, stop and contact the lecturer or a
demonstrator, with a screenshot of the window.

---

## 1. Install Miniforge (a Python distribution)

Skip this step if you already have Miniforge, Miniconda or Anaconda; go to step 2 and use its prompt.

**Windows** (including ARM laptops):

1. Download the installer:
   <https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe>
   (use this x86_64 installer even on an ARM laptop).
2. Run it and accept the defaults ("Just Me", default folder).
3. From the Start menu open **Miniforge Prompt**. Type all commands below into this window.

**macOS:** open **Terminal** and run

```bash
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh
```

Press Enter / type `yes` when asked, and answer **yes** to "initialize Miniforge3".
Then **close Terminal and open a new one**. Type all commands below into Terminal.

## 2. Create the course environment

Copy and paste (one line):

```
conda create -n sdsg -c conda-forge python=3.12 numpy=2.3 scipy matplotlib pandas requests astropy jupyterlab
```

Answer `y` when asked. Then activate it:

```
conda activate sdsg
```

Your prompt should now start with `(sdsg)`. You need `conda activate sdsg` **every time** you
open a new prompt/Terminal for this course.

## 3. Check your Python

```
python -c "import sys, sysconfig; print(sysconfig.get_platform(), sys.version.split()[0])"
```

Expected output, depending on your computer:

| Computer | Expected output |
|---|---|
| Windows (any, including ARM laptops) | `win-amd64 3.12.x` |
| Mac with Apple chip (M1-M4) | `macosx-11.0-arm64 3.12.x` |
| Mac with Intel chip | `macosx-11.0-x86_64 3.12.x` |

Any other result: stop and ask for help.

## 4. Install AGAMA

```
pip install --no-index --find-links https://vasilybelokurov.github.io/sdsg-agama/ agama
```

pip picks the right file for your computer and checks its checksum automatically.

## 5. Test AGAMA

```
python -c "import sys, agama; ok = abs(agama.Potential(type='Plummer').potential([1,0,0]) + 0.5**0.5) < 1e-10; print('AGAMA', agama.__version__, '|', sys.executable); print('PASS' if ok else 'FAIL')"
```

The last line must be **PASS**, and the path printed before it must contain `sdsg`.

## 6. Use it in Jupyter

```
conda activate sdsg
jupyter lab
```

Jupyter opens in your browser. In a new notebook, run `import agama`. If it fails, you started
Jupyter from a different environment: close it, and re-run the two commands above.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `'conda' is not recognized` (Windows) | Use **Miniforge Prompt** from the Start menu, not the ordinary Command Prompt or PowerShell. |
| `conda: command not found` (Mac) | Close Terminal and open a new one. If it persists, run `~/miniforge3/bin/conda init zsh` and reopen Terminal. |
| pip: `No matching distribution found for agama` | Your Python is not 3.12 or not 64-bit: re-check step 3, and make sure the prompt shows `(sdsg)`. |
| `ImportError: DLL load failed` (Windows) | Contact the lecturer, with a screenshot. |
| `Library not loaded` or `incompatible architecture` (Mac) | Contact the lecturer, with the output of step 3. |
| Anything else | Contact the lecturer or a demonstrator, with a screenshot. |

**To remove everything later:** `conda env remove -n sdsg` (and uninstall Miniforge as an ordinary program).

---

*About these files:* AGAMA is developed by Eugene Vasiliev ([GitHub](https://github.com/GalacticDynamics-Oxford/Agama);
[Vasiliev 2019, MNRAS 482, 1525](https://doi.org/10.1093/mnras/sty2672)). The course wheels are
unofficial builds of a fixed AGAMA version; see the [README](README.md) for how they are built and tested.
