import vapoursynth as vs
from functools import partial
from typing import Any, Callable, List, Union, Optional
core = vs.core

def Destripe(clip: vs.VideoNode,
             width: int = 1280,
             height: int = 360,
             kernel: str = 'bicubic',
             b: float = 0,
             c: float = 1/2,
             taps: int = 3,
             src_left: Union[float, List[float]] = [0.0, 0.0],
             src_top: Union[float, List[float]] = [0.0, 0.0],
             src_width: Union[float, List[float]] = [0.0, 0.0],
             src_height: Union[float, List[float]] = [0.0, 0.0],
             fix_border_func: Optional[Callable[..., vs.VideoNode]] = None,
             fix_top: Union[int, List[int]] = [0, 0],
             fix_bottom: Union[int, List[int]] = [0, 0],
             showdiff: bool = False) -> Union[vs.VideoNode, List[vs.VideoNode]]:
    y = clip if clip.format.color_family == vs.GRAY else core.std.ShufflePlanes(clip, 0, vs.GRAY)
    kernel = kernel.lower()
    if kernel.startswith('de'):
        kernel = kernel[2:]
    if not isinstance(src_left, list):
        src_left = [src_left, src_left]
    if not isinstance(src_top, list):
        src_top = [src_top, src_top]
    cropping_args_top = dict(src_top=src_top[0], src_left=src_left[0])
    cropping_args_bot = dict(src_top=src_top[1], src_left=src_left[1])
    if not isinstance(src_width, list):
        src_width = [src_width, src_width]
    if not isinstance(src_height, list):
        src_height = [src_height, src_height]
    if src_width[0] > 0.0 or src_width[1] > 0.0 or src_height[0] > 0.0 or src_height[1] > 0.0:
        cropping_args_top['src_width'] = width if src_width[0] <= 0.0 else src_width[0]
        cropping_args_bot['src_width'] = width if src_width[1] <= 0.0 else src_width[1]
        cropping_args_top['src_height'] = height if src_height[0] <= 0.0 else src_height[0]
        cropping_args_bot['src_height'] = height if src_height[1] <= 0.0 else src_height[1]
    if fix_border_func is None:
        fix_border_func = core.edgefixer.Continuity
    if not isinstance(fix_top, list):
        fix_top = [fix_top, fix_top]
    if not isinstance(fix_bottom, list):
        fix_bottom = [fix_bottom, fix_bottom]

    isfloat = (y.format.sample_type == vs.FLOAT and y.format.bits_per_sample == 32)
    sep = core.std.SeparateFields(y, True)
    if 'API R4.' in vs.core.version():
        sep = core.std.RemoveFrameProps(sep, '_Field')
    else:
        sep = core.std.SetFrameProp(sep, '_Field', delete=True)
    st = sep[0::2]
    sb = sep[1::2]
    if fix_top[0] > 0 or fix_bottom[0] > 0:
        st16 = core.resize.Point(st, format=vs.GRAY16, dither_type='error_diffusion')
        st32 = fix_border_func(st16, top=fix_top[0], bottom=fix_bottom[0]).resize.Point(format=vs.GRAYS)
    elif isfloat:
        st32 = st
    else:
        st32 = core.resize.Point(st, format=vs.GRAYS)
    if fix_top[1] > 0 or fix_bottom[1] > 0:
        sb16 = core.resize.Point(sb, format=vs.GRAY16, dither_type='error_diffusion')
        sb32 = fix_border_func(sb16, top=fix_top[1], bottom=fix_bottom[1]).resize.Point(format=vs.GRAYS)
    elif isfloat:
        sb32 = sb
    else:
        sb32 = core.resize.Point(sb, format=vs.GRAYS)

    if showdiff:
        downt, difft = _Descale(st32, width, height, kernel, b, c, taps, True, **cropping_args_top)
        downb, diffb = _Descale(sb32, width, height, kernel, b, c, taps, True, **cropping_args_bot)
        down = _Weave(downt, downb)
        diff = _Weave(difft, diffb)
        if isfloat:
            return [down, diff]
        else:
            downi = core.resize.Point(down, format=y.format, dither_type='error_diffusion')
            diffi = core.resize.Point(diff, format=y.format, range_in_s='limited', range_s='full')
            return [downi, diffi]
    else:
        downt = _Descale(st32, width, height, kernel, b, c, taps, False, **cropping_args_top)
        downb = _Descale(sb32, width, height, kernel, b, c, taps, False, **cropping_args_bot)
        down = _Weave(downt, downb)
        if isfloat:
            return down
        else:
            downi = core.resize.Point(down, format=y.format, dither_type='error_diffusion')
            return downi

def _Weave(clipa: vs.VideoNode, clipb: vs.VideoNode) -> vs.VideoNode:
    clip = core.std.Interleave([clipa, clipb])
    wv = core.std.DoubleWeave(clip, True)[0::2]
    return wv.std.SetFrameProp('_FieldBased', intval=0)

def _GetDescaler(kernel: str,
                 b: float,
                 c: float,
                 taps: int) -> Callable[..., vs.VideoNode]:
    if kernel == 'bilinear':
        return core.descale.Debilinear
    elif kernel == 'bicubic':
        return partial(core.descale.Debicubic, b=b, c=c)
    elif kernel == 'lanczos':
        return partial(core.descale.Delanczos, taps=taps)
    elif kernel == 'spline16':
        return core.descale.Despline16
    elif kernel == 'spline36':
        return core.descale.Despline36
    elif kernel == 'spline64':
        return core.descale.Despline64
    else:
        raise ValueError('descale: Invalid kernel specified.')

def _GetResizer(kernel: str,
                b: float,
                c: float,
                taps: int) -> Callable[..., vs.VideoNode]:
    if kernel == 'bilinear':
        return core.resize.Bilinear
    elif kernel == 'bicubic':
        return partial(core.resize.Bicubic, filter_param_a=b, filter_param_b=c)
    elif kernel == 'lanczos':
        return partial(core.resize.Lanczos, filter_param_a=taps)
    elif kernel == 'spline16':
        return core.resize.Spline16
    elif kernel == 'spline36':
        return core.resize.Spline36
    elif kernel == 'spline64':
        return core.resize.Spline64
    else:
        raise ValueError('resize: Invalid kernel specified.')

def _Descale(clip: vs.VideoNode,
             width: int,
             height: int,
             kernel: str,
             b: float,
             c: float,
             taps: int,
             showdiff: bool,
             **cropping_args: Any) -> Union[vs.VideoNode, List[vs.VideoNode]]:
    descaler = _GetDescaler(kernel, b, c, taps)
    down = descaler(clip, width, height, **cropping_args)
    if showdiff:
        resizer = _GetResizer(kernel, b, c, taps)
        up = resizer(down, clip.width, clip.height, **cropping_args)
        diff = core.std.Expr([clip, up], 'x y - abs')
        return [down, diff]
    else:
        return down
