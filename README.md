# VapourSynth-Destripe
A `descale` wrapper for anime destriping.

## Prerequisites

* VapourSynth version R46 or newer
* [vapoursynth-descale](https://github.com/Irrational-Encoding-Wizardry/vapoursynth-descale)
* VapourSynth R49 and Descale R3 or newer for `Spline64` support. A recent version since [this release](https://github.com/Irrational-Encoding-Wizardry/vapoursynth-descale/commit/7ea0ca134183cadf4c47d0ab607fe51c22912c04) for using cropping parameters `src_width` and `src_height`.
* An optional filter fixing borders before descaling. It should work for `GRAY16` input with `top` and `bottom` options. It is called only if nontrivial border widths are provided. The default is [EdgeFixer](https://github.com/sekrit-twc/EdgeFixer).

## How it works

Some striped (aka cross-conversion, or 縞縞) anime artifacts are caused by improper upscaling by field. `Destripe` manually descales by field.

## Usage

The first plane of the input clip will be internally converted to `GRAY16` if fixing borders is requested, then `GRAYS`, and be processed. The output has the same format as the first plane of the input.
```python
from destripe import Destripe

down = Destripe(clip clip[, int width=1280, int height=360, str kernel='bicubic', float b=0, float c=1/2, int taps=3, float[] src_left=[0, 0], float[] src_top=[0, 0], float[] src_width=[width, width], float[] src_height=[height, height], func fix_border_func=vs.core.edgefixer.Continuity, int[] fix_top=[0, 0], int[] fix_bottom=[0, 0], bool showdiff=False])

down, diff = Destripe(clip, ..., showdiff=True)
```
Parameters:
- `width`, `height`</br>
The destination descaled size for each field. For example, if you believe the native resolution was 1280x720, then each field should be 1280x360.
- `kernel`, `b`, `c`, `taps`</br>
Parameters of the resizers. See [Descale's page](https://github.com/Irrational-Encoding-Wizardry/vapoursynth-descale#usage).
- `src_left`, `src_top`, `src_width`, `src_height`</br>
Specify the cropping parameters for the top field and the bottom field, respectively. They refer to the initial upscale, see [this link](https://github.com/Irrational-Encoding-Wizardry/vapoursynth-descale/issues/2#issuecomment-305876093). Usually you need to modify `src_top` until satisfactory.
Note that `Descale` only accepts positive values of `src_width` and `src_height`, so negative or zero inputs will be replaced by values of `width` and `height`, respectively.
- `fix_border_func`, `fix_top`, `fix_bottom`</br>
If specified, a border fixing filter will be applied to the top and bottom borders for each field, respectively, before descaling.
- `showdiff`</br>
Set to `True` to include the de-rescale absolute error `diff` in the return list. `diff` has the same format as the first plane of `clip`.

Notes:
- IVTC should be taken prior to destriping, since this script doesn't deal with field order.
- Bad borders could be amplified while descaling.
Tweaking `fix_top` and `fix_bottom` may and may not be better than fixing edges before calling `Destripe`.
- Resizer settings could cause a position shift of the output from the source and you are supposed to fix by yourself.

## Examples
In these examples `clip` already has its borders fixed before processing.
#### Example 1
```python
down = Destripe(clip, 1280, 360, kernel='spline64', src_top=[1/6, 1/6])
up = core.resize.Spline64(down, 1920, 1080, src_top=1/3)
```
See [the comparison](https://slow.pics/c/Ff7sWVu5).
#### Example 2
```python
down = Destripe(clip, 1280, 360, kernel='bicubic', b=0, c=1/3, src_top=[1/12, -1/12])
up = core.resize.Bicubic(down, 1920, 1080, filter_param_a=0, filter_param_b=1/3)
```
See [the comparison](https://slow.pics/c/eiiJsRTE).

## Related

* [縞縞対策](https://anibin.blogspot.com/search/label/%E7%B8%9E%E7%B8%9E%E5%AF%BE%E7%AD%96)  from anibin's blog
* [CullResize](https://sites.google.com/site/anibinmidori/destripe), anibin's AVS Destripe
* [CullResize](https://github.com/DJATOM/CullResize), DJATOM's 64-bit port

## Thanks
joletb, NiTr0gLiTcH, xyx98


## License
MIT.
