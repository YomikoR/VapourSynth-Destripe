import vapoursynth as vs
from functools import partial
core = vs.core

def Destripe(clip, width=1280, height=360, kernel='bicubic', b=0, c=1/2, taps=3, src_top=[0.0, 0.0], src_left=[0.0, 0.0], showdiff=False):
    y32 = clip if clip.format.id == vs.GRAYS else _GetY32(clip)
    kernel = kernel.lower()
    if not isinstance(src_top, list):
        try:
            assert isinstance(src_top, float) or isinstance(src_top, int)
            src_top = [src_top, src_top]
        except:
            raise ValueError('Destripe: invalid src_top parameters specified.')
    if not isinstance(src_left, list):
        try:
            assert isinstance(src_left, float) or isinstance(src_left, int)
            src_left = [src_left, src_left]
        except:
            raise ValueError('Destripe: invalid src_left parameters specified.')
    sep = core.std.SeparateFields(y32, True).std.SetFrameProp('_Field', delete=True)
    ftop = core.std.SelectEvery(sep, 2, 0)
    fbot = core.std.SelectEvery(sep, 2, 1)
    if showdiff:
        downt, difft = _Descale(ftop, width, height, kernel, b, c, taps, src_top[0], src_left[0], True)
        downb, diffb = _Descale(fbot, width, height, kernel, b, c, taps, src_top[1], src_left[1], True)
        return _Weave(downt, downb), _Weave(difft, diffb)
    else:
        downt = _Descale(ftop, width, height, kernel, b, c, taps, src_top[0], src_left[0], False)
        downb = _Descale(fbot, width, height, kernel, b, c, taps, src_top[1], src_left[1], False)
        return _Weave(downt, downb)

def _GetY32(clip):
    return clip.std.ShufflePlanes(0, vs.GRAY).resize.Point(format=vs.GRAYS)

def _Weave(clipa, clipb):
    clip = core.std.Interleave([clipa, clipb])
    wv = core.std.DoubleWeave(clip, True).std.SelectEvery(2, 0)
    return wv.std.SetFrameProp('_FieldBased', intval=0)

def _GetDescaler(kernel, b, c, taps, src_top, src_left):
    if kernel == 'bilinear':
        return partial(core.descale.Debilinear, src_top=src_top, src_left=src_left)
    elif kernel == 'bicubic':
        return partial(core.descale.Debicubic, b=b, c=c, src_top=src_top, src_left=src_left)
    elif kernel == 'lanczos':
        return partial(core.descale.Delanczos, taps=taps, src_top=src_top, src_left=src_left)
    elif kernel == 'spline16':
        return partial(core.descale.Despline16, src_top=src_top, src_left=src_left)
    elif kernel == 'spline36':
        return partial(core.descale.Despline36, src_top=src_top, src_left=src_left)
    elif kernel == 'spline64':
        return partial(core.descale.Despline64, src_top=src_top, src_left=src_left)
    else:
        raise ValueError('descale: Invalid kernel specified.')

def _GetResizer(kernel, b, c, taps, src_top, src_left):
    if kernel == 'bilinear':
        return partial(core.resize.Bilinear, src_top=src_top, src_left=src_left)
    elif kernel == 'bicubic':
        return partial(core.resize.Bicubic, filter_param_a=b, filter_param_b=c, src_top=src_top, src_left=src_left)
    elif kernel == 'lanczos':
        return partial(core.resize.Lanczos, filter_param_a=taps, src_top=src_top, src_left=src_left)
    elif kernel == 'spline16':
        return partial(core.resize.Spline16, src_top=src_top, src_left=src_left)
    elif kernel == 'spline36':
        return partial(core.resize.Spline36, src_top=src_top, src_left=src_left)
    elif kernel == 'spline64':
        return partial(core.resize.Spline64, src_top=src_top, src_left=src_left)
    else:
        raise ValueError('resize: Invalid kernel specified.')

def _Descale(clip, width, height, kernel, b, c, taps, src_top, src_left, showdiff):
    descaler = _GetDescaler(kernel, b, c, taps, src_top, src_left)
    down = descaler(clip, width, height)
    if showdiff:
        resizer = _GetResizer(kernel, b, c, taps, src_top, src_left)
        up = resizer(down, clip.width, clip.height)
        diff = core.std.Expr([clip, up], 'x y - abs')
        return down, diff
    else:
        return down
