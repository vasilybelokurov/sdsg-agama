"""Strict checks of the Agama features used in the SDSG course notebooks.

Every check compares against an analytic result and raises on failure;
the script exits non-zero if anything fails. Run in the student environment:

    python tests/test_course.py

Units: Agama's default N-body units, G = 1 (no setUnits) unless stated.
"""
import math
import platform
import sys

import numpy as np

FAILURES = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (" | " + detail if detail else ""))
    if not ok:
        FAILURES.append(name)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import agama  # noqa: E402  (also registers agama colormaps with matplotlib)

    print("python", sys.version.split()[0], platform.machine(), sys.executable)
    print("numpy", np.__version__, "| agama module", agama.__file__)

    # --- Potentials ---------------------------------------------------------
    M, a = 1.0, 1.0
    pl = agama.Potential(type="Plummer", mass=M, scaleRadius=a)
    r = np.array([0.1, 1.0, 3.0])
    xyz = np.column_stack([r, 0 * r, 0 * r])
    phi_true = -M / np.sqrt(r**2 + a**2)
    check("Plummer potential", np.allclose(pl.potential(xyz), phi_true, rtol=1e-10))
    rho_true = 3 * M / (4 * math.pi * a**3) * (1 + r**2 / a**2) ** -2.5
    check("Plummer density", np.allclose(pl.density(xyz), rho_true, rtol=1e-6))
    m_true = M * r**3 / (r**2 + a**2) ** 1.5
    check("Plummer enclosedMass", np.allclose(pl.enclosedMass(r), m_true, rtol=1e-6))
    check("Plummer totalMass", math.isclose(pl.totalMass(), M, rel_tol=1e-6))

    # Logarithmic: Phi = 0.5 v0^2 ln(R^2 + z^2/q^2 + rc^2), default core rc = 1
    # => v_circ(R) = v0 R / sqrt(R^2 + rc^2)
    lg = agama.Potential(type="Logarithmic", v0=1.0, q=1.0)
    f = lg.force([10.0, 0, 0])
    check("Logarithmic v_circ", math.isclose(math.sqrt(-f[0] * 10.0), 10.0 / math.sqrt(101.0), rel_tol=1e-8))

    # Miyamoto-Nagai: Phi = -M / sqrt(R^2 + (a + sqrt(z^2+b^2))^2)
    mn = agama.Potential(type="MiyamotoNagai", mass=1.0, scaleRadius=2.0, scaleHeight=0.3)
    R, z = 3.0, 0.5
    phi_mn = -1.0 / math.sqrt(R**2 + (2.0 + math.sqrt(z**2 + 0.3**2)) ** 2)
    check("MiyamotoNagai potential", math.isclose(mn.potential([R, 0, z]), phi_mn, rel_tol=1e-8))

    # Dehnen gamma=1 (Hernquist): Phi = -M/(r+a)
    de = agama.Potential(type="Dehnen", mass=1.0, scaleRadius=1.0, gamma=1.0)
    check("Dehnen(Hernquist) potential", math.isclose(de.potential([2.0, 0, 0]), -1.0 / 3.0, rel_tol=1e-6))

    # NFW: Phi = -M ln(1 + r/rs) / r   (Agama's 'mass' is the normalisation M)
    nfw = agama.Potential(type="NFW", mass=1.0, scaleRadius=1.0)
    check("NFW potential", math.isclose(nfw.potential([2.0, 0, 0]), -math.log(3.0) / 2.0, rel_tol=1e-6))

    # Composite potential (as in nbody_effects.ipynb)
    comp = agama.Potential(pl, de)
    check("Composite potential",
          math.isclose(comp.potential([2.0, 0, 0]), pl.potential([2.0, 0, 0]) + de.potential([2.0, 0, 0]), rel_tol=1e-10))

    # --- Orbits -------------------------------------------------------------
    ic = np.array([1.0, 0.0, 0.0, 0.0, 0.5, 0.1])
    E0 = pl.potential(ic[:3]) + 0.5 * np.sum(ic[3:] ** 2)
    t, traj = agama.orbit(potential=pl, ic=ic, time=100.0, trajsize=1001)
    E = pl.potential(traj[:, :3]) + 0.5 * np.sum(traj[:, 3:] ** 2, axis=1)
    check("orbit shape", traj.shape == (1001, 6) and len(t) == 1001, str(traj.shape))
    check("orbit energy conservation", np.max(np.abs(E - E0)) < 1e-6 * abs(E0),
          "max |dE/E| = %.2e" % (np.max(np.abs(E - E0)) / abs(E0)))
    L = np.cross(traj[:, :3], traj[:, 3:])
    check("orbit angular momentum conservation", np.max(np.abs(L - L[0])) < 1e-6)
    t2, traj2 = agama.orbit(potential=pl, ic=ic, time=-10.0, timestart=1e-6, trajsize=11, dtype="f8")
    check("orbit backwards in time (dtype f8)", traj2.shape == (11, 6) and t2[-1] < 0)
    ics = np.tile(ic, (8, 1))
    res = agama.orbit(potential=lg, ic=ics, time=5.0, trajsize=5)
    check("orbit, multiple ICs", len(res) == 8)

    # --- Actions ------------------------------------------------------------
    vc = math.sqrt(-pl.force([1.0, 0, 0])[0] * 1.0)
    circ = np.array([1.0, 0, 0, 0, vc, 0])
    act = agama.ActionFinder(pl)(circ)
    check("actions of circular orbit", abs(act[0]) < 1e-6 and abs(act[1]) < 1e-6 and math.isclose(act[2], vc, rel_tol=1e-6),
          "Jr,Jz,Jphi = %s" % np.array2string(np.asarray(act), precision=3))

    # --- Distribution function and GalaxyModel (plummer_df.ipynb) ------------
    den = agama.Density(type="Plummer", mass=M, scaleRadius=a)
    df = agama.DistributionFunction(type="QuasiSpherical", potential=pl, density=den)
    check("QuasiSpherical DF total mass", math.isclose(df.totalMass(), M, rel_tol=1e-3), "%.5f" % df.totalMass())
    model = agama.GalaxyModel(potential=pl, df=df)
    posvel, mass = model.sample(100000)
    # particle masses come from a Monte-Carlo estimate of the DF mass, so allow 1%
    check("GalaxyModel.sample shape and mass", posvel.shape == (100000, 6) and math.isclose(np.sum(mass), M, rel_tol=1e-2),
          "sum(m) = %.4f" % np.sum(mass))
    # Plummer: total kinetic energy T = 3 pi G M^2 / (64 a)  =>  <v^2> = 2T/M
    v2 = np.sum(mass * np.sum(posvel[:, 3:] ** 2, axis=1)) / np.sum(mass)
    v2_true = 2 * 3 * math.pi / 64
    check("sampled <v^2> vs analytic Plummer", math.isclose(v2, v2_true, rel_tol=0.02), "%.4f vs %.4f" % (v2, v2_true))

    # --- Physical units (as in several notebooks) ----------------------------
    agama.setUnits(length=1, velocity=1, mass=1)   # kpc, km/s, Msun
    G = 4.300917e-6  # kpc (km/s)^2 / Msun
    pu = agama.Potential(type="Plummer", mass=1e10, scaleRadius=1.0)
    check("setUnits kpc/km/s/Msun", math.isclose(pu.potential([1.0, 0, 0]), -G * 1e10 / math.sqrt(2), rel_tol=1e-4))

    print()
    if FAILURES:
        print("FAILED: %d check(s): %s" % (len(FAILURES), ", ".join(FAILURES)))
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
