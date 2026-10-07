# Copyright Tempo Simulation, LLC. All Rights Reserved

"""Runtime wiring for the plugin-owned lidar participating-media demo map."""

from dataclasses import dataclass

import tempo_sim.tempo_sensors as ts
import tempo_sim.tempo_world as tw
import tempo_sim.TempoSensors.Sensors_pb2 as Sensors


RIG_HINT = "TempoLidarMediaDemoRig"
EFFECT_HINTS = {
    "fog": "TempoLidarMediaDemoFog",
    "dust": "TempoLidarMediaDemoDust",
    "smoke": "TempoLidarMediaDemoSmoke",
}

DEFAULTS = {
    "simulate": True,
    "translucency": True,
    "return_mode": "Dual",
    "extinction": 1.0,
    "backscatter": 0.18,
    "stochastic": True,
}


@dataclass
class DemoScene:
    rig: str
    lidar: str
    camera: str
    effects: dict


def _match_actor(actors, hint):
    exact = next((name for name in actors if name == hint), None)
    if exact:
        return exact
    return next((name for name in actors if hint.lower() in name.lower()), None)


async def discover_demo_scene():
    actors = [actor.name for actor in (await tw.get_all_actors()).actors]
    rig = _match_actor(actors, RIG_HINT)
    effects = {kind: _match_actor(actors, hint) for kind, hint in EFFECT_HINTS.items()}
    missing = [hint for kind, hint in EFFECT_HINTS.items() if not effects[kind]]
    if not rig:
        missing.insert(0, RIG_HINT)
    if missing:
        raise RuntimeError(
            "The running level is not /TempoSensors/Maps/TempoLidarMediaDemo; "
            f"missing actor(s): {', '.join(missing)}"
        )

    descriptors = (await ts.get_available_sensors()).available_sensors
    lidar = next(
        (
            sensor.name
            for sensor in descriptors
            if sensor.owner == rig and Sensors.MT_LIDAR_SCAN in sensor.measurement_types
        ),
        None,
    )
    camera = next(
        (
            sensor.name
            for sensor in descriptors
            if sensor.owner == rig and Sensors.MT_COLOR_IMAGE in sensor.measurement_types
        ),
        None,
    )
    if not lidar or not camera:
        raise RuntimeError(
            f"{rig} must own one Tempo lidar and one color camera "
            f"(camera={camera!r}, lidar={lidar!r})."
        )
    return DemoScene(rig=rig, lidar=lidar, camera=camera, effects=effects)


async def set_effect_visible(scene, effect, visible):
    actor = scene.effects[effect]
    await (
        tw.call(actor=actor, function="SetActorHiddenInGame")
        .bool_arg("bNewHidden", not visible)
        .execute_async()
    )


async def set_bool(scene, property_name, value):
    await tw.set_bool_property(
        actor=scene.rig, component=scene.lidar, property=property_name, value=value
    )


async def set_float(scene, property_name, value):
    await tw.set_float_property(
        actor=scene.rig, component=scene.lidar, property=property_name, value=value
    )


async def set_return_mode(scene, mode):
    await tw.set_enum_property(
        actor=scene.rig, component=scene.lidar, property="ReturnMode", value=mode
    )


async def apply_defaults(scene):
    for effect in EFFECT_HINTS:
        await set_effect_visible(scene, effect, True)
    await set_bool(scene, "bSimulateParticipatingMedia", DEFAULTS["simulate"])
    await set_bool(scene, "bMediaIncludesTranslucency", DEFAULTS["translucency"])
    await set_return_mode(scene, DEFAULTS["return_mode"])
    await set_float(scene, "MediaExtinctionScale", DEFAULTS["extinction"])
    await set_float(scene, "MediaBackscatter", DEFAULTS["backscatter"])
    await set_bool(scene, "bStochasticMediaReturns", DEFAULTS["stochastic"])
