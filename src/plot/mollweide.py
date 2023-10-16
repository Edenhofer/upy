#!/usr/bin/env python3

from typing import Optional

import numpy as np


def _mollweide_helper(xsize):
    xsize = int(xsize)
    ysize = xsize // 2
    res = np.full(shape=(ysize, xsize), fill_value=np.nan, dtype=np.float64)
    xc, yc = (xsize - 1) * 0.5, (ysize - 1) * 0.5
    u, v = np.meshgrid(np.arange(xsize), np.arange(ysize))
    u, v = 2 * (u - xc) / (xc / 1.02), (v - yc) / (yc / 1.02)

    mask = np.where((u * u * 0.25 + v * v) <= 1.)
    t1 = v[mask]
    theta = 0.5 * np.pi - (
        np.arcsin(
            2 / np.pi * (np.arcsin(t1) + t1 * np.sqrt((1. - t1) * (1 + t1)))
        )
    )
    phi = -0.5 * np.pi * u[mask] / np.maximum(
        np.sqrt((1 - t1) * (1 + t1)), 1e-6
    )
    phi = np.where(phi < 0, phi + 2 * np.pi, phi)
    return res, mask, theta, phi


def _find_closest(singles, target):
    # singles must be sorted
    idx = np.clip(singles.searchsorted(target), 1, len(singles) - 1)
    idx -= target - singles[idx - 1] < singles[idx] - target
    return idx


def ring2mollweide(pxs, xsize=800, dom_name="HPSpace", scheme="RING"):
    """Converts from HEALPix RING to the Mollweide projection"""
    nside = np.sqrt(pxs.size // 12).astype(int)
    res, mask, theta, phi = _mollweide_helper(xsize)
    if dom_name == "HPSpace":
        from ducc0 import healpix

        ptg = np.column_stack((theta, phi))
        base = healpix.Healpix_Base(nside, scheme)
        res[mask] = pxs[base.ang2pix(ptg)]
    else:
        from ducc0.misc import GL_thetas

        nlat, nlon = nside, 2 * nside - 1
        ra = np.linspace(0, 2 * np.pi, nlon + 1)
        dec = GL_thetas(nlat)
        ilat = _find_closest(dec, theta)
        ilon = _find_closest(ra, phi)
        ilon = np.where(ilon == nlon, 0, ilon)
        res[mask] = pxs[ilat * nlon + ilon]
    return res


def immollweide(
    pxs,
    *,
    ax,
    norm=None,
    vscale=None,
    vmin=None,
    vmax=None,
    cmap=None,
    xsize=800,
    nest=False,
    axis="off",
):
    import matplotlib.colors as mcolors

    if norm is not None:
        if vscale is not None:
            raise ValueError("only one of `norm` or `vscale` can be specified")
    elif vscale in ("log", "Log"):
        # Workaround for matplotlib's poor treatment of np.nan's on log-scale
        SafeLogNorm = mcolors.LogNorm
        SafeLogNorm.__call__ = np.errstate(invalid="ignore")(
            SafeLogNorm.__call__
        )
        norm = SafeLogNorm(vmin=vmin, vmax=vmax)
    elif isinstance(vscale, tuple) and vscale[0] in ("symlog", "SymLog"):
        # Workaround for matplotlib's poor treatment of np.nan's on log-scale
        SafeSymLogNorm = mcolors.SymLogNorm
        SafeSymLogNorm.__call__ = np.errstate(invalid="ignore")(
            SafeSymLogNorm.__call__
        )
        kw = vscale[1].copy()
        kw.setdefault("vmin", vmin)
        kw.setdefault("vmin", vmax)
        norm = SafeSymLogNorm(**kw)
    elif vscale in ("linear", "Linear") or vscale is None:
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    ax.axis(axis)
    pxs = ring2mollweide(pxs, xsize=xsize, scheme="NEST" if nest else "RING")
    im = ax.imshow(pxs, norm=norm, origin="lower", cmap=cmap)
    return im


def moll_plot(
    pxs,
    *,
    ax,
    title=None,
    cbar_label=None,
    cbar_shrink=0.85,
    cbar_aspect=35,
    cbar_pad=0.02,
    cbar_kw: Optional[dict] = {},
    **kw
):
    import matplotlib.pyplot as plt

    if title is not None:
        ax.set_title(title)
    im = immollweide(pxs, ax=ax, **kw)

    if cbar_kw is None:
        return im, None

    cbar_kw = cbar_kw.copy()
    for k, v in {
        "ax": ax,
        "label": cbar_label,
        "shrink": cbar_shrink,
        "aspect": cbar_aspect,
        "pad": cbar_pad
    }.items():
        cbar_kw.setdefault(k, v)
    if kw.get("vmin", None) is not None and kw.get("vmax", None) is not None:
        cbar_kw.setdefault("extend", "both")
    elif kw.get("vmin", None) is not None:
        cbar_kw.setdefault("extend", "min")
    elif kw.get("vmax", None) is not None:
        cbar_kw.setdefault("extend", "max")
    cbar_kw.setdefault("orientation", "horizontal")

    cbar = plt.colorbar(im, **cbar_kw)
    return im, cbar


def oneshot_moll_plot(
    fs,
    nrows=None,
    ncols=None,
    figsize=(16, 10),
    dpi=None,
    ax_args=None,
    **moll_kw
):
    import matplotlib.pyplot as plt

    fs = np.asarray(fs)
    fs = fs[np.newaxis, :] if fs.ndim == 1 else fs
    if ncols is nrows is None:
        ncols = nrows = np.ceil(np.sqrt(fs.shape[0])).astype(int)
    elif ncols is None:
        ncols = np.ceil(fs.shape[0] / nrows).astype(int)
    elif nrows is None:
        nrows = np.ceil(fs.shape[0] / ncols).astype(int)
    if nrows * ncols < fs.shape[0]:
        raise ValueError(
            "Figure dimensions insufficient for specified number of plots; "
            f"available plot slots: {nrows * ncols}; number of plots: {fs.shape[0]}"
        )
    if ax_args is not None:
        ax_args = np.asarray(ax_args)
        ax_args = ax_args[np.newaxis, :] if fs.ndim == 1 else ax_args

    fig = plt.figure(figsize=figsize, dpi=dpi)
    for i, pxs in enumerate(fs):
        ax = fig.add_subplot(nrows, ncols, i + 1)
        arg = ax_args[i] if ax_args is not None else []
        if isinstance(arg, dict):
            # Ensure arg overwrites moll_kw
            moll_plot(pxs, ax=ax, **{**moll_kw, **arg})
        else:
            moll_plot(pxs, ax=ax, *arg, **moll_kw)
    fig.tight_layout()
    return fig, fig.axes
