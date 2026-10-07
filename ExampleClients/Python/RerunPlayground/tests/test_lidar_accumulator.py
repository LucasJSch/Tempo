# Copyright Tempo Simulation, LLC. All Rights Reserved

import unittest
from types import SimpleNamespace

import numpy as np

from RerunPlayground.lidar_accumulator import ScanAccumulator


def _bytes(values, dtype):
    return np.asarray(values, dtype=dtype).tobytes()


def _segment(sequence, *, scan_count=1, return_mode=3, distances=(10.0, 20.0), second=()):
    count = len(distances)
    second = tuple(second)
    return SimpleNamespace(
        header=SimpleNamespace(sequence_id=sequence),
        scan_count=scan_count,
        return_mode=return_mode,
        horizontal_beams=count,
        vertical_beams=1,
        distances_m=_bytes(distances, np.float32),
        intensities=_bytes(np.linspace(0.25, 0.75, count), np.float32),
        labels=_bytes(range(1, count + 1), np.uint32),
        reflectivities=_bytes(np.linspace(64, 192, count), np.uint8),
        second_distances_m=_bytes(second, np.float32) if second else b"",
        second_intensities=_bytes(np.full(count, 0.4), np.float32) if second else b"",
        second_labels=_bytes(np.full(count, 9), np.uint32) if second else b"",
        second_reflectivities=_bytes(np.full(count, 100), np.uint8) if second else b"",
        azimuths_rad=_bytes(np.linspace(-0.1, 0.1, count), np.float32),
        elevations_rad=_bytes(np.zeros(count), np.float32),
        colors=b"",
        color_encoding=0,
    )


class ScanAccumulatorTest(unittest.TestCase):
    def test_single_segment_dual_return(self):
        result = ScanAccumulator(bgr_encoding=2).add(_segment(1, second=(5.0, 0.0)))
        self.assertEqual(len(result.primary.positions), 2)
        self.assertEqual(len(result.secondary.positions), 1)
        np.testing.assert_allclose(result.secondary.distances, [5.0])
        np.testing.assert_array_equal(result.secondary.labels, [9])

    def test_multiple_segments_are_joined(self):
        accumulator = ScanAccumulator(bgr_encoding=2)
        self.assertIsNone(accumulator.add(_segment(2, scan_count=2, second=(4.0, 0.0))))
        result = accumulator.add(_segment(2, scan_count=2, second=(0.0, 6.0)))
        self.assertEqual(len(result.primary.positions), 4)
        np.testing.assert_allclose(result.secondary.distances, [4.0, 6.0])

    def test_absent_second_echo_yields_empty_cloud(self):
        result = ScanAccumulator(bgr_encoding=2).add(_segment(3))
        self.assertEqual(result.secondary.positions.shape, (0, 3))
        self.assertEqual(len(result.secondary.intensities), 0)

    def test_new_sequence_discards_incomplete_scan(self):
        accumulator = ScanAccumulator(bgr_encoding=2)
        self.assertIsNone(accumulator.add(_segment(4, scan_count=2, second=(4.0, 0.0))))
        result = accumulator.add(_segment(5))
        self.assertEqual(len(result.primary.positions), 2)
        self.assertEqual(len(result.secondary.positions), 0)

    def test_empty_scan_after_dual_clears_secondary_state(self):
        accumulator = ScanAccumulator(bgr_encoding=2)
        dual = accumulator.add(_segment(6, second=(5.0, 0.0)))
        no_second = accumulator.add(_segment(7))
        self.assertEqual(len(dual.secondary.positions), 1)
        self.assertEqual(len(no_second.secondary.positions), 0)

    def test_mode_change_discards_old_segments_and_clears_second_echo(self):
        accumulator = ScanAccumulator(bgr_encoding=2)
        self.assertIsNone(
            accumulator.add(_segment(8, scan_count=2, return_mode=3, second=(5.0, 0.0)))
        )
        result = accumulator.add(_segment(8, scan_count=1, return_mode=0))
        self.assertEqual(len(result.primary.positions), 2)
        self.assertEqual(len(result.secondary.positions), 0)

    def test_malformed_second_payload_is_rejected(self):
        segment = _segment(9, second=(5.0, 0.0))
        segment.second_intensities = b"bad"
        with self.assertRaisesRegex(ValueError, "second_intensities"):
            ScanAccumulator(bgr_encoding=2).add(segment)


if __name__ == "__main__":
    unittest.main()
