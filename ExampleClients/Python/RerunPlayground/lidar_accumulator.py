# Copyright Tempo Simulation, LLC. All Rights Reserved

"""Pure numpy accumulation for segmented Tempo lidar scans.

This module deliberately has no rerun or gRPC imports. Keeping wire decoding and
scan assembly separate from visualization makes dual-return behavior cheap to test.
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class ReturnCloud:
    positions: np.ndarray
    distances: np.ndarray
    intensities: np.ndarray
    labels: np.ndarray
    reflectivities: np.ndarray | None
    colors_rgb: np.ndarray | None


@dataclass
class CompletedScan:
    primary: ReturnCloud
    secondary: ReturnCloud


def _packed(scan, name, dtype, count, *, optional=False):
    payload = getattr(scan, name)
    if optional and not payload:
        return None
    expected = count * np.dtype(dtype).itemsize
    if len(payload) != expected:
        raise ValueError(f"{name} has {len(payload)} bytes; expected {expected}")
    return np.frombuffer(payload, dtype=dtype)


def _decode_return(scan, *, secondary, bgr_encoding):
    h, v = scan.horizontal_beams, scan.vertical_beams
    count = h * v
    prefix = "second_" if secondary else ""

    distances = _packed(scan, f"{prefix}distances_m", np.float32, count, optional=secondary)
    if distances is None:
        distances = np.zeros(count, dtype=np.float32)
        intensities = np.zeros(count, dtype=np.float32)
        labels = np.zeros(count, dtype=np.uint32)
        reflectivities = None
    else:
        intensities = _packed(scan, f"{prefix}intensities", np.float32, count)
        labels = _packed(scan, f"{prefix}labels", np.uint32, count)
        reflectivities = _packed(
            scan, f"{prefix}reflectivities", np.uint8, count, optional=True
        )
        if reflectivities is not None:
            reflectivities = reflectivities.astype(np.float32) / 255.0

    colors_rgb = None
    if not secondary and scan.colors:
        colors_rgb = _packed(scan, "colors", np.uint8, count * 3).reshape(count, 3)
        if scan.color_encoding == bgr_encoding:
            colors_rgb = colors_rgb[:, ::-1]

    return distances, intensities, labels, reflectivities, colors_rgb


class ScanAccumulator:
    """Collect all segments for a sequence and return primary/secondary clouds."""

    def __init__(self, bgr_encoding):
        self.bgr_encoding = bgr_encoding
        self._reset(None)

    def _reset(self, scan):
        self.sequence_id = scan.header.sequence_id if scan else None
        self.return_mode = getattr(scan, "return_mode", None) if scan else None
        self.scan_count = scan.scan_count if scan else 0
        self.segments_seen = 0
        self._primary = []
        self._secondary = []

    @staticmethod
    def _segment_cloud(scan, secondary, bgr_encoding):
        distances, intensities, labels, reflectivities, colors_rgb = _decode_return(
            scan, secondary=secondary, bgr_encoding=bgr_encoding
        )
        count = scan.horizontal_beams * scan.vertical_beams
        azimuths = _packed(scan, "azimuths_rad", np.float32, count)
        elevations = _packed(scan, "elevations_rad", np.float32, count)
        valid = np.isfinite(distances) & (distances > 0.0)

        d = distances[valid]
        az = azimuths[valid]
        el = elevations[valid]
        cos_el = np.cos(el)
        positions = (
            np.stack(
                [d * cos_el * np.cos(az), d * cos_el * np.sin(az), d * np.sin(el)],
                axis=-1,
            )
            if d.size
            else np.zeros((0, 3), dtype=np.float32)
        )

        return ReturnCloud(
            positions=positions,
            distances=d,
            intensities=intensities[valid],
            labels=labels[valid].astype(np.uint16),
            reflectivities=reflectivities[valid] if reflectivities is not None else None,
            colors_rgb=colors_rgb[valid] if colors_rgb is not None else None,
        )

    @staticmethod
    def _join(parts):
        if not parts:
            return ReturnCloud(
                positions=np.zeros((0, 3), np.float32),
                distances=np.zeros((0,), np.float32),
                intensities=np.zeros((0,), np.float32),
                labels=np.zeros((0,), np.uint16),
                reflectivities=None,
                colors_rgb=None,
            )

        def concatenate(name, empty_shape, dtype):
            values = [getattr(part, name) for part in parts]
            if any(value is None for value in values):
                return None
            return np.concatenate(values, axis=0) if values else np.zeros(empty_shape, dtype=dtype)

        return ReturnCloud(
            positions=np.concatenate([part.positions for part in parts], axis=0),
            distances=np.concatenate([part.distances for part in parts]),
            intensities=np.concatenate([part.intensities for part in parts]),
            labels=np.concatenate([part.labels for part in parts]),
            reflectivities=concatenate("reflectivities", (0,), np.float32),
            colors_rgb=concatenate("colors_rgb", (0, 3), np.uint8),
        )

    def add(self, scan):
        return_mode = getattr(scan, "return_mode", None)
        if scan.header.sequence_id != self.sequence_id or return_mode != self.return_mode:
            self._reset(scan)

        self._primary.append(self._segment_cloud(scan, False, self.bgr_encoding))
        self._secondary.append(self._segment_cloud(scan, True, self.bgr_encoding))
        self.segments_seen += 1
        if self.segments_seen < self.scan_count:
            return None

        result = CompletedScan(self._join(self._primary), self._join(self._secondary))
        self._reset(None)
        return result
