#
#         PySceneDetect: Python-Based Video Scene Detector
#   ---------------------------------------------------------------
#     [  Site: https://scenedetect.com                           ]
#     [  Docs: https://scenedetect.com/docs/                     ]
#     [  Github: https://github.com/Breakthrough/PySceneDetect/   ]
#
# Copyright (C) 2014 Brandon Castellano <http://www.bcastell.com>.
# PySceneDetect is licensed under the BSD 3-Clause License; see the
# included LICENSE file, or visit one of the above pages for details.
#

import logging
import os
import typing as ty

import cv2

logger = logging.getLogger("pyscenedetect")

DEFAULT_MIN_FRAMES: int = 1000

OPT_5: int = 8

OPT_6: int = 250


def opt_3(n_frames: int) -> int:
    override = os.environ.get("SCENEDETECT_OPT_1")
    if override is not None:
        try:
            requested = int(override)
        except ValueError:
            logger.warning("Ignoring invalid SCENEDETECT_OPT_1=%s", override)
            return 0
        return requested if requested > 1 else 0
    if n_frames < DEFAULT_MIN_FRAMES:
        return 0
    return max(0, min(OPT_5, (os.cpu_count() or 1) - 1,
                      n_frames // OPT_6))


def _keyframes(path: str) -> list[int]:
    """Frame indices that start a keyframe, by DEMUXING only -- no frame is
    decoded, so this is milliseconds for a whole file. Empty if PyAV is absent,
    in which case the split falls back to equal frame ranges."""
    try:
        import av
    except ImportError:
        return []
    try:
        with av.open(path) as container:
            stream = container.streams.video[0]
            keyframes, index = [], 0
            for packet in container.demux(stream):
                if packet.pts is None:
                    continue
                if packet.is_keyframe:
                    keyframes.append(index)
                index += 1
            return keyframes
    except Exception as ex:                     # a container we cannot index is not fatal
        logger.debug("Could not index keyframes (%s); using an even split.", ex)
        return []


def opt_17(n_frames: int, keyframes: ty.Sequence[int],
                   opt_4: int) -> list[tuple[int, int | None]]:
    starts = [0]
    usable = [k for k in keyframes if 0 < k < n_frames]
    if len(usable) >= opt_4 - 1:
        step = len(usable) / float(opt_4)
        starts += [usable[min(len(usable) - 1, int(round(i * step)))]
                   for i in range(1, opt_4)]
    else:
        per = n_frames / float(opt_4)
        starts += [int(round(i * per)) for i in range(1, opt_4)]
    starts = sorted({start for start in starts if 0 <= start < n_frames})
    return [(start, starts[i + 1] if i + 1 < len(starts) else None)
            for i, start in enumerate(starts)]


def _seek_exact(cap: cv2.VideoCapture, target: int) -> int:
    """Position `cap` so that the next read() returns frame `target`."""
    if target <= 0:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        return 0
    cap.set(cv2.CAP_PROP_POS_FRAMES, target)
    position = int(round(cap.get(cv2.CAP_PROP_POS_FRAMES)))
    if position > target:                       # overshot: walk from the start
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        position = 0
    while position < target:
        if not cap.grab():
            break
        position += 1
    return position


def _opt_16(task):
    path, start, end, weights, downscale_factor, interpolation = task
    cv2.setNumThreads(1)
    cap = cv2.VideoCapture(path)
    try:
        index = _seek_exact(cap, max(0, start - 1))
        scores: list[float] = []
        last_hsv = None
        weight_sum = sum(abs(weight) for weight in weights)
        while end is None or index < end:
            grabbed, frame = cap.read()
            if not grabbed:
                break
            if downscale_factor > 1.0:
                frame = cv2.resize(
                    frame,
                    (max(1, round(frame.shape[1] / downscale_factor)),
                     max(1, round(frame.shape[0] / downscale_factor))),
                    interpolation=interpolation,
                )
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            if last_hsv is None:
                score = 0.0
            else:
                num_pixels = float(hsv.shape[0] * hsv.shape[1])
                channel_sums = cv2.sumElems(cv2.absdiff(hsv, last_hsv))
                score = (
                    channel_sums[0] / num_pixels * weights[0]
                    + channel_sums[1] / num_pixels * weights[1]
                    + channel_sums[2] / num_pixels * weights[2]
                    + 0.0 * weights[3]
                ) / weight_sum
            last_hsv = hsv
            if index >= start:
                scores.append(score)
            index += 1
        return start, scores
    finally:
        cap.release()


def opt_18(path: str, n_frames: int, opt_4: int, weights,
                 downscale_factor: float, interpolation: int) -> list[float] | None:
    import multiprocessing

    bounds = opt_17(n_frames, _keyframes(path), opt_4)
    if len(bounds) < 2:
        return None
    tasks = [(path, start, end, tuple(weights), downscale_factor, interpolation)
             for start, end in bounds]
    try:
        context = multiprocessing.get_context("fork")
    except ValueError:                          # platforms without fork
        return None
    try:
        with context.Pool(len(tasks)) as opt_7:
            results = opt_7.map(_opt_16, tasks)
    except Exception as ex:
        logger.warning("Optimized scoring failed (%s); falling back to the stock reader.", ex)
        return None
    scores: list[float] = []
    for _start, segment in sorted(results, key=lambda item: item[0]):
        scores.extend(segment)
    logger.debug("Scored %d frames in %d segments (%d).",
                 len(scores), len(bounds), len(tasks))
    return scores
