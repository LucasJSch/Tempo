# Copyright Tempo Simulation, LLC. All Rights Reserved

"""Accumulate Tempo lidar segments and log primary and secondary returns."""

import numpy as np
import rerun as rr

import tempo_sim.tempo_sensors as ts
import tempo_sim.TempoSensors.Common_pb2 as Common

from .. import colormap
from .. import conventions as conv
from .._compat import set_sim_time
from ..lidar_accumulator import ScanAccumulator
from ..streaming import pump


def _primary_style(cloud, mode):
    if mode == "color":
        colors = cloud.colors_rgb
        if colors is None:
            colors = np.full((len(cloud.positions), 3), 128, dtype=np.uint8)
        return {"colors": colors}
    if mode == "label":
        return {"class_ids": cloud.labels}
    if mode == "distance":
        return {"colors": colormap.scalar_to_rgb(cloud.distances)}
    if mode == "reflectivity":
        values = cloud.reflectivities
        if values is None:
            values = np.full(len(cloud.positions), 0.5, dtype=np.float32)
        return {"colors": colormap.scalar_to_rgb(values)}
    return {
        "colors": colormap.scalar_to_rgb(
            cloud.intensities, vmin=0.0, vmax=1.0
        )
    }


def _secondary_style(cloud):
    """Use an unmistakable magenta ramp for the second echo."""
    values = np.clip(cloud.intensities, 0.0, 1.0)
    colors = np.empty((len(values), 3), dtype=np.uint8)
    colors[:, 0] = 255
    colors[:, 1] = (32.0 + 64.0 * values).astype(np.uint8)
    colors[:, 2] = 255
    return {"colors": colors, "radii": 0.055}


async def stream_lidar(sensor, mode="intensity"):
    entity = conv.sensor_entity(sensor.owner, sensor.name)
    primary_entity = f"{entity}/points/primary"
    secondary_entity = f"{entity}/points/secondary"
    accumulator = ScanAccumulator(Common.CE_BGR8)
    include_color = mode == "color"

    def handle(scan):
        result = accumulator.add(scan)
        if result is None:
            return

        set_sim_time(conv.SIM_TIME, scan.header.capture_time_s)
        rr.log(entity, conv.transform_to_rerun(scan.header.capture_transform))
        rr.log(
            primary_entity,
            rr.Points3D(result.primary.positions, **_primary_style(result.primary, mode)),
        )
        # Log an empty entity too, so leaving Dual mode clears stale second echoes.
        rr.log(
            secondary_entity,
            rr.Points3D(result.secondary.positions, **_secondary_style(result.secondary)),
        )

    await pump(
        ts.stream_lidar_scans(
            owner=sensor.owner, sensor=sensor.name, include_color=include_color
        ),
        handle,
        queue_size=8,
        label=f"{sensor.key}:lidar",
    )
