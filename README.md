<div align="center">
  <a href="https://autooptm.com"><img src=".autooptm/logo.png" width="96" alt="AutoOptm"></a>

  <h1>PySceneDetect · optimized by <a href="https://autooptm.com">AutoOptm</a></h1>

  <p><b>1.86x faster end to end</b> on the command below, output verified against the stock program.</p>

  <p>
    <a href="https://autooptm.com"><img alt="speedup" src="https://img.shields.io/badge/end--to--end-1.86x-2ea44f"></a>
    <a href="https://github.com/Breakthrough/PySceneDetect/commit/2fa8290de0353d371eaae92a8a6efb69d16a1e0c"><img alt="base" src="https://img.shields.io/badge/upstream-2fa8290de035-blue"></a>
    <img alt="card" src="https://img.shields.io/badge/measured%20on-NVIDIA%20RTX%204090-lightgrey">
  </p>
</div>

> This is a fork of [Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect) at commit
> [`2fa8290de035`](https://github.com/Breakthrough/PySceneDetect/commit/2fa8290de0353d371eaae92a8a6efb69d16a1e0c) with the AutoOptm patch applied on top.
> The optimisation was found, measured and verified automatically by [AutoOptm](https://autooptm.com);
> the patch is kept under [`.autooptm/`](.autooptm/).

Every optimisation is on by default and the command runs unchanged — same file, same flags, same outputs. Every change is behind a switch that defaults on; see `.autooptm/autooptm.patch`.

## The result — `python scenedetect/__main__.py -i demo.mp4 detect-adaptive list-scenes -n`

| | |
|---|---|
| **Command** | `python scenedetect/__main__.py -i demo.mp4 detect-adaptive list-scenes -n` |
| **Entry point** | `scenedetect/__main__.py` |
| **Unit measured** | one clip scored with detect-adaptive end to end (decode → per-frame score → cut decision → scene list) |
| **Before (stock)** | 1.944 (as reported) per unit |
| **After (this tree, all switches default ON)** | 1.037 (as reported) per unit |
| **Speedup** | **1.86x** end to end on NVIDIA RTX 4090, host noise floor 2.1% |
| **Output** | bit-identical: scores max_abs_diff = 0 and the cut list identical to stock |

### What changed

| File | Where | Gain (alone) |
|---|---|---|
| `scenedetect/detectors/content_detector.py` | ContentDetector._calculate_frame_score / _opt_12 | 1.1496x |
| `scenedetect/detectors/content_detector.py` | ContentDetector.process_score / _decide | 1.0x |
| `scenedetect/detectors/adaptive_detector.py` | AdaptiveDetector.process_score / _detect_adaptive | 1.0x |
| `scenedetect/_opt_score.py` | new module | 1.87x |
| `scenedetect/scene_manager.py` | SceneManager.detect_scenes | 1.87x |


## Reproduce

```bash
git clone https://github.com/autooptm/PySceneDetect-ao.git
cd PySceneDetect-ao
# set up exactly as upstream documents, then:
python scenedetect/__main__.py -i demo.mp4 detect-adaptive list-scenes -n
```

`git diff 2fa8290de035` is the same change as the patch file under `.autooptm/`.

---

<div align="center"><sub>Optimized by <a href="https://autooptm.com">AutoOptm</a> — point it at a repository, get back a verified speedup and the patch.</sub></div>

---


<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Breakthrough/PySceneDetect/main/website/pages/img/pyscenedetect_logo_small_darkmode.png">
  <img alt="PySceneDetect" src="https://raw.githubusercontent.com/Breakthrough/PySceneDetect/main/website/pages/img/pyscenedetect_logo_small.png">
</picture>

# Video Cut Detection and Analysis Tool

[![Build Status](https://img.shields.io/github/actions/workflow/status/Breakthrough/PySceneDetect/build.yml)](https://github.com/Breakthrough/PySceneDetect/actions)
[![PyPI Status](https://img.shields.io/pypi/status/scenedetect.svg)](https://pypi.python.org/pypi/scenedetect/)
[![PyPI Version](https://img.shields.io/pypi/v/scenedetect?color=blue)](https://pypi.python.org/pypi/scenedetect/)
[![PyPI License](https://img.shields.io/pypi/l/scenedetect.svg)](https://scenedetect.com/copyright/)

----------------------------------------------------------

### Latest Release: v0.7.1 (July 21, 2026)

**Website**:  [scenedetect.com](https://www.scenedetect.com)

**Quickstart Example**: [scenedetect.com/cli/](https://www.scenedetect.com/cli/)

**Documentation**:  [scenedetect.com/docs/](https://www.scenedetect.com/docs/)

**Discord**: https://discord.gg/H83HbJngk7

----------------------------------------------------------

**Quick Install**:

    pip install scenedetect --upgrade

Requires ffmpeg/mkvmerge for video splitting support. Windows builds (MSI installer/portable ZIP) can be found on [the download page](https://scenedetect.com/download/). A Docker image with all dependencies included is available as [`ghcr.io/breakthrough/pyscenedetect`](https://github.com/Breakthrough/PySceneDetect/pkgs/container/pyscenedetect).

----------------------------------------------------------

**Quick Start (Command Line)**:

Split input video on each fast cut using `ffmpeg`:

    scenedetect -i video.mp4 split-video

Save some frames from each cut:

    scenedetect -i video.mp4 save-images

Skip the first 10 seconds of the input video:

    scenedetect -i video.mp4 time -s 10s

More examples can be found throughout [the documentation](https://www.scenedetect.com/docs/latest/cli.html).

**Quick Start (Docker)**:

The same commands work without installing anything using [the official Docker image](https://github.com/Breakthrough/PySceneDetect/pkgs/container/pyscenedetect), which includes all dependencies (`ffmpeg`/`mkvmerge` included). Mount the folder containing your videos and use it for input/output paths:

    docker run --rm -v "$(pwd):/files" ghcr.io/breakthrough/pyscenedetect -i /files/video.mp4 split-video -o /files

**Quick Start (Python API)**:

To get started, there is a high level function in the library that performs content-aware scene detection on a video (try it from a Python prompt):

```python
from scenedetect import detect, ContentDetector

scene_list = detect("my_video.mp4", ContentDetector())
```

`scene_list` will now be a list containing the start/end times of all scenes found in the video.  There also exists a two-pass version `AdaptiveDetector` which handles fast camera movement better, and `ThresholdDetector` for handling fade out/fade in events.

Try calling `print(scene_list)`, or iterating over each scene:

```python
from scenedetect import detect, ContentDetector

scene_list = detect("my_video.mp4", ContentDetector())
for i, scene in enumerate(scene_list):
    print(
        "    Scene %2d: Start %s / Frame %d, End %s / Frame %d"
        % (
            i + 1,
            scene[0].get_timecode(),
            scene[0].frame_num,
            scene[1].get_timecode(),
            scene[1].frame_num,
        )
    )
```

We can also split the video into each scene if `ffmpeg` is installed (`mkvmerge` is also supported):

```python
from scenedetect import detect, ContentDetector, split_video_ffmpeg

scene_list = detect("my_video.mp4", ContentDetector())
split_video_ffmpeg("my_video.mp4", scene_list)
```

For more advanced usage, the API is highly configurable, and can easily integrate with any pipeline. This includes using different detection algorithms, splitting the input video, and much more. The following example shows how to implement a function similar to the above, but using [the `scenedetect` API](https://www.scenedetect.com/docs/latest/api.html):

```python
from scenedetect import open_video, SceneManager, split_video_ffmpeg
from scenedetect.detectors import ContentDetector
from scenedetect.video_splitter import split_video_ffmpeg


def split_video_into_scenes(video_path, threshold=27.0):
    # Open our video, create a scene manager, and add a detector.
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))
    scene_manager.detect_scenes(video, show_progress=True)
    scene_list = scene_manager.get_scene_list()
    split_video_ffmpeg(video_path, scene_list, show_progress=True)
```

See [the documentation](https://www.scenedetect.com/docs/latest/api.html) for more examples.

**Benchmark**:

We evaluate the performance of different detectors in terms of accuracy and processing speed. See [www.scenedetect.com/benchmarks](https://www.scenedetect.com/benchmarks/) for results, or the [benchmark report](benchmark/README.md) for details on the datasets and methodology.

## Reference

 - [Documentation](https://www.scenedetect.com/docs/) (covers application and Python API)
 - [CLI Example](https://www.scenedetect.com/cli/)
 - [Config File](https://www.scenedetect.com/docs/latest/cli/config_file.html)

## Help & Contributing

Please submit any bugs/issues or feature requests to [the Issue Tracker](https://github.com/Breakthrough/PySceneDetect/issues). Before submission, ensure you search through existing issues (both open and closed) to avoid creating duplicate entries.
Pull requests are welcome and encouraged.  PySceneDetect is released under the BSD 3-Clause license, and submitted code should be compliant.

For help or other issues, you can join [the official PySceneDetect Discord Server](https://discord.gg/H83HbJngk7), submit an issue/bug report [here on Github](https://github.com/Breakthrough/PySceneDetect/issues), or contact me via [my website](https://bcastell.com/about/).

## Code Signing

This program uses free code signing provided by [SignPath.io](https://signpath.io?utm_source=foundation&utm_medium=github&utm_campaign=PySceneDetect), and a free code signing certificate by the [SignPath Foundation](https://signpath.org?utm_source=foundation&utm_medium=github&utm_campaign=PySceneDetect)

## License

BSD-3-Clause; see [`LICENSE`](LICENSE) and [`THIRD-PARTY.md`](THIRD-PARTY.md) for details.

----------------------------------------------------------

Copyright (C) 2014 Brandon Castellano.
All rights reserved.
