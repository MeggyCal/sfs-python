"""Compute the sound field generated by a sound source.

.. plot::
    :context: reset

    import sfs
    import numpy as np
    import matplotlib.pyplot as plt
    plt.rcParams['figure.figsize'] = 8, 4.5  # inch

    x0 = 1.5, 1, 0
    f = 500  # Hz
    omega = 2 * np.pi * f

    grid = sfs.util.xyz_grid([-2, 3], [-1, 2], 0, spacing=0.02)

"""

import itertools
import numpy as np
from scipy import special
from .. import util
from .. import defs


def point(omega, x0, n0, grid, c=None):
    """Point source.

    ::

                      1  e^(-j w/c |x-x0|)
        G(x-x0, w) = --- -----------------
                     4pi      |x-x0|

    Examples
    --------
    .. plot::
        :context: close-figs

        p = sfs.mono.source.point(omega, x0, None, grid)
        sfs.plot.soundfield(p, grid)
        plt.title("Point Source at {} m".format(x0))

    Normalization ... multiply by :math:`4\pi` ...

    .. plot::
        :context: close-figs

        p *= 4 * np.pi
        sfs.plot.soundfield(p, grid)
        plt.title("Point Source at {} m (normalized)".format(x0))

    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)
    grid = util.XyzComponents(grid)

    r = np.linalg.norm(grid - x0)
    return 1 / (4*np.pi) * np.exp(-1j * k * r) / r


def point_velocity(omega, x0, n0, grid, c=None):
    """Velocity of a point source.

    Returns
    -------
    XyzComponents
        Particle velocity at positions given by `grid`.
        See :class:`sfs.util.XyzComponents`.

    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)
    grid = util.XyzComponents(grid)
    offset = grid - x0
    r = np.linalg.norm(offset)
    v = point(omega, x0, n0, grid, c=c)
    v *= (1+1j*k*r) / (defs.rho0 * defs.c * 1j*k*r)
    return util.XyzComponents([v * o / r for o in offset])


def point_modal(omega, x0, n0, grid, L, N=None, deltan=0, c=None):
    """Point source in a rectangular room using a modal room model.

    Parameters
    ----------
    omega : float
        Frequency of source.
    x0 : (3,) array_like
        Position of source.
    n0 : (3,) array_like
        Normal vector (direction) of source (only required for
        compatibility).
    grid : triple of numpy.ndarray
        The grid that is used for the sound field calculations.
        See :func:`sfs.util.xyz_grid`.
    L : (3,) array_like
        Dimensionons of the rectangular room.
    N : (3,) array_like or int, optional
        Combination of modal orders in the three-spatial dimensions to
        calculate the sound field for or maximum order for all
        dimensions.  If not given, the maximum modal order is
        approximately determined and the sound field is computed up to
        this maximum order.
    deltan : float, optional
        Absorption coefficient of the walls.
    c : float, optional
        Speed of sound.

    Returns
    -------
    numpy.ndarray
        Sound pressure at positions given by `grid`.

    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)
    x, y, z = util.XyzComponents(grid)

    if N is None:
        # determine maximum modal order per dimension
        Nx = int(np.ceil(L[0]/np.pi * k))
        Ny = int(np.ceil(L[1]/np.pi * k))
        Nz = int(np.ceil(L[2]/np.pi * k))
        mm = range(Nx)
        nn = range(Ny)
        ll = range(Nz)
    elif np.isscalar(N):
        # compute up to a given order
        mm = range(N)
        nn = range(N)
        ll = range(N)
    else:
        # compute field for one order combination only
        mm = [N[0]]
        nn = [N[1]]
        ll = [N[2]]

    kmp0 = [((kx + 1j * deltan)**2, np.cos(kx * x) * np.cos(kx * x0[0]))
            for kx in [m * np.pi / L[0] for m in mm]]
    kmp1 = [((ky + 1j * deltan)**2, np.cos(ky * y) * np.cos(ky * x0[1]))
            for ky in [n * np.pi / L[1] for n in nn]]
    kmp2 = [((kz + 1j * deltan)**2, np.cos(kz * z) * np.cos(kz * x0[2]))
            for kz in [l * np.pi / L[2] for l in ll]]
    ksquared = k**2
    p = 0
    for (km0, p0), (km1, p1), (km2, p2) in itertools.product(kmp0, kmp1, kmp2):
        km = km0 + km1 + km2
        p = p + 8 / (ksquared - km) * p0 * p1 * p2
    return p


def point_modal_velocity(omega, x0, n0, grid, L, N=None, deltan=0, c=None):
    """Velocity of point source in a rectangular room using a modal room model.

    Parameters
    ----------
    omega : float
        Frequency of source.
    x0 : (3,) array_like
        Position of source.
    n0 : (3,) array_like
        Normal vector (direction) of source (only required for
        compatibility).
    grid : triple of numpy.ndarray
        The grid that is used for the sound field calculations.
        See :func:`sfs.util.xyz_grid`.
    L : (3,) array_like
        Dimensionons of the rectangular room.
    N : (3,) array_like or int, optional
        Combination of modal orders in the three-spatial dimensions to
        calculate the sound field for or maximum order for all
        dimensions.  If not given, the maximum modal order is
        approximately determined and the sound field is computed up to
        this maximum order.
    deltan : float, optional
        Absorption coefficient of the walls.
    c : float, optional
        Speed of sound.

    Returns
    -------
    XyzComponents
        Particle velocity at positions given by `grid`.
        See :class:`sfs.util.XyzComponents`.

    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)
    x, y, z = util.XyzComponents(grid)

    if N is None:
        # determine maximum modal order per dimension
        Nx = int(np.ceil(L[0]/np.pi * k))
        Ny = int(np.ceil(L[1]/np.pi * k))
        Nz = int(np.ceil(L[2]/np.pi * k))
        mm = range(Nx)
        nn = range(Ny)
        ll = range(Nz)
    elif np.isscalar(N):
        # compute up to a given order
        mm = range(N)
        nn = range(N)
        ll = range(N)
    else:
        # compute field for one order combination only
        mm = [N[0]]
        nn = [N[1]]
        ll = [N[2]]

    kmp0 = [((kx + 1j * deltan)**2, np.sin(kx * x) * np.cos(kx * x0[0]))
            for kx in [m * np.pi / L[0] for m in mm]]
    kmp1 = [((ky + 1j * deltan)**2, np.sin(ky * y) * np.cos(ky * x0[1]))
            for ky in [n * np.pi / L[1] for n in nn]]
    kmp2 = [((kz + 1j * deltan)**2, np.sin(kz * z) * np.cos(kz * x0[2]))
            for kz in [l * np.pi / L[2] for l in ll]]
    ksquared = k**2
    vx = 0+0j
    vy = 0+0j
    vz = 0+0j
    for (km0, p0), (km1, p1), (km2, p2) in itertools.product(kmp0, kmp1, kmp2):
        km = km0 + km1 + km2
        vx = vx - 8*1j / (ksquared - km) * p0
        vy = vy - 8*1j / (ksquared - km) * p1
        vz = vz - 8*1j / (ksquared - km) * p2
    return util.XyzComponents([vx, vy, vz])


def line(omega, x0, n0, grid, c=None):
    """Line source parallel to the z-axis.

    Note: third component of x0 is ignored.

    ::

                           (2)
        G(x-x0, w) = -j/4 H0  (w/c |x-x0|)

    Examples
    --------
    .. plot::
        :context: close-figs

        p = sfs.mono.source.line(omega, x0, None, grid)
        sfs.plot.soundfield(p, grid)
        plt.title("Line Source at {} m".format(x0[:2]))

    Normalization ...

    .. plot::
        :context: close-figs

        p *= np.sqrt(8 * np.pi * omega / sfs.defs.c) * np.exp(1j * np.pi / 4)
        sfs.plot.soundfield(p, grid)
        plt.title("Line Source at {} m (normalized)".format(x0[:2]))

    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)
    x0 = x0[:2]  # ignore z-component
    grid = util.XyzComponents(grid)

    r = np.linalg.norm(grid[:2] - x0)
    p = -1j/4 * special.hankel2(0, k * r)
    return _duplicate_zdirection(p, grid)


def line_velocity(omega, x0, n0, grid, c=None):
    """Velocity of line source parallel to the z-axis.

    Returns
    -------
    XyzComponents
        Particle velocity at positions given by `grid`.
        See :class:`sfs.util.XyzComponents`.

    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)
    x0 = x0[:2]  # ignore z-component
    grid = util.XyzComponents(grid)

    offset = grid[:2] - x0
    r = np.linalg.norm(offset)
    v = -1/(4*defs.c*defs.rho0) * special.hankel2(1, k * r)
    v = [v * o / r for o in offset]

    assert v[0].shape == v[1].shape

    if len(grid) > 2:
        v.append(np.zeros_like(v[0]))

    return util.XyzComponents([_duplicate_zdirection(vi, grid) for vi in v])


def line_dipole(omega, x0, n0, grid, c=None):
    """Line source with dipole characteristics parallel to the z-axis.

    Note: third component of x0 is ignored.

    ::

                           (2)
        G(x-x0, w) = jk/4 H1  (w/c |x-x0|) cos(phi)


    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)
    x0 = x0[:2]  # ignore z-component
    n0 = n0[:2]
    grid = util.XyzComponents(grid)
    dx = grid[:2] - x0
    r = np.linalg.norm(dx)
    p = 1j*k/4 * special.hankel2(1, k * r) * np.inner(dx, n0) / r
    return _duplicate_zdirection(p, grid)


def plane(omega, x0, n0, grid, c=None):
    """Plane wave.

    ::

        G(x, w) = e^(-i w/c n x)

    Example
    -------
    .. plot::
        :context: close-figs

        direction = 45  # degree
        n0 = sfs.util.direction_vector(np.radians(direction))
        p_plane = sfs.mono.source.plane(omega, x0, n0, grid)
        sfs.plot.soundfield(p_plane, grid);
        plt.title("Plane wave with direction {} degree".format(direction))

    """
    k = util.wavenumber(omega, c)
    x0 = util.asarray_1d(x0)
    n0 = util.asarray_1d(n0)
    grid = util.XyzComponents(grid)
    return np.exp(-1j * k * np.inner(grid - x0, n0))


def plane_velocity(omega, x0, n0, grid, c=None):
    """Velocity of a plane wave.

    ::

        V(x, w) = 1/(rho c) e^(-i w/c n x) n

    Returns
    -------
    XyzComponents
        Particle velocity at positions given by `grid`.
        See :class:`sfs.util.XyzComponents`.

    """
    v = plane(omega, x0, n0, grid, c=c) / (defs.rho0 * defs.c)
    return util.XyzComponents([v * n for n in n0])


def _duplicate_zdirection(p, grid):
    """If necessary, duplicate field in z-direction."""
    gridshape = np.broadcast(*grid).shape
    if len(gridshape) > 2:
        return np.tile(p, [1, 1, gridshape[2]])
    else:
        return p
