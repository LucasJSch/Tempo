# Copyright Tempo Simulation, LLC. All Rights Reserved

"""Rerun control panel: stream controls + the shared TempoWorld property editor.

The property editor (actor/component get/set) is the reusable `tempo_panel`
building block, also used by the standalone WorldPlaygroundGUI.py. This module
adds the rerun-specific Streams section (lidar signal + per-camera image) and
launches the page.

See tempo_panel for the threading/async details; the short version is that
launch() must run on the main thread (Gradio initializes its queue via an HTTP
self-request during launch) and building the UI makes no API calls.
"""

import traceback

import gradio as gr

from tempo_panel import AsyncBridge, property_editor, find_free_port

from .. import media_demo
from ..client import LIDAR_SIGNALS

# Image kinds the camera dropdown offers (bbox is an overlay, not a standalone view).
CAMERA_IMAGE_KINDS = ("color", "video", "depth", "label")
CAMERA_OFF = "(off)"

_bridge = None  # AsyncBridge onto the main loop; set by launch_control_panel
_client = None  # TempoRerunClient; set by launch_control_panel


def _set_lidar_mode(key, mode) -> str:
    try:
        _bridge.submit(_client.set_lidar_mode, key, mode)
        return f"✓ {key} → {mode}"
    except Exception as exc:
        return f"✗ {exc}"


def _set_camera_image(key, choice) -> str:
    kinds = [] if choice == CAMERA_OFF else [choice]
    try:
        _bridge.submit(_client.set_camera_measurements, key, kinds)
        return f"✓ {key}: {choice}"
    except Exception as exc:
        return f"✗ {exc}"


def _streams_section():
    gr.Markdown(
        "Pick which lidar signal to display, and which image each camera streams. "
        "Changing these re-applies the generated layout."
    )
    stream_status = gr.Markdown("")
    for sensor in _client.scene.sensors:
        if sensor.is_lidar:
            dd = gr.Dropdown(
                choices=list(LIDAR_SIGNALS),
                value=_client.lidar_modes.get(sensor.key, _client.cfg.colorize_lidar_by),
                label=f"{sensor.key} — lidar signal",
            )
            dd.change(lambda m, k=sensor.key: _set_lidar_mode(k, m), inputs=dd, outputs=stream_status)
        elif sensor.is_camera:
            available = [k for k in CAMERA_IMAGE_KINDS if k in _client.camera_kinds_available(sensor)]
            current = next((k for k in available if f"{sensor.key}:{k}" in _client.tasks), CAMERA_OFF)
            dd = gr.Dropdown(choices=[CAMERA_OFF] + available, value=current, label=f"{sensor.key} — image")
            dd.change(lambda choice, k=sensor.key: _set_camera_image(k, choice),
                      inputs=dd, outputs=stream_status)


def _demo_call(function, *args):
    try:
        _bridge.submit(function, _client.cfg.media_demo_scene, *args)
        return "✓ Updated"
    except Exception as exc:
        return f"✗ {exc}"


def _media_demo_section():
    defaults = media_demo.DEFAULTS
    status = gr.Markdown("")

    with gr.Row():
        fog = gr.Checkbox(value=True, label="Fog visible")
        dust = gr.Checkbox(value=True, label="Dust visible")
        smoke = gr.Checkbox(value=True, label="Smoke visible")
    fog.change(lambda value: _demo_call(media_demo.set_effect_visible, "fog", value),
               inputs=fog, outputs=status)
    dust.change(lambda value: _demo_call(media_demo.set_effect_visible, "dust", value),
                inputs=dust, outputs=status)
    smoke.change(lambda value: _demo_call(media_demo.set_effect_visible, "smoke", value),
                 inputs=smoke, outputs=status)

    simulate = gr.Checkbox(value=defaults["simulate"], label="Simulate participating media")
    translucency = gr.Checkbox(
        value=defaults["translucency"], label="Media includes translucency"
    )
    stochastic = gr.Checkbox(value=defaults["stochastic"], label="Stochastic returns")
    simulate.change(
        lambda value: _demo_call(media_demo.set_bool, "bSimulateParticipatingMedia", value),
        inputs=simulate, outputs=status,
    )
    translucency.change(
        lambda value: _demo_call(media_demo.set_bool, "bMediaIncludesTranslucency", value),
        inputs=translucency, outputs=status,
    )
    stochastic.change(
        lambda value: _demo_call(media_demo.set_bool, "bStochasticMediaReturns", value),
        inputs=stochastic, outputs=status,
    )

    return_mode = gr.Dropdown(
        choices=["Strongest", "First", "Last", "Dual"],
        value=defaults["return_mode"], label="Return mode",
    )
    return_mode.change(
        lambda value: _demo_call(media_demo.set_return_mode, value),
        inputs=return_mode, outputs=status,
    )

    extinction = gr.Slider(
        minimum=0.0, maximum=4.0, step=0.05,
        value=defaults["extinction"], label="Extinction scale",
    )
    backscatter = gr.Slider(
        minimum=0.0, maximum=1.0, step=0.01,
        value=defaults["backscatter"], label="Backscatter",
    )
    extinction.release(
        lambda value: _demo_call(media_demo.set_float, "MediaExtinctionScale", value),
        inputs=extinction, outputs=status,
    )
    backscatter.release(
        lambda value: _demo_call(media_demo.set_float, "MediaBackscatter", value),
        inputs=backscatter, outputs=status,
    )

    reset = gr.Button("Reset showcase defaults", variant="primary")

    def reset_defaults():
        message = _demo_call(media_demo.apply_defaults)
        return (
            True, True, True,
            defaults["simulate"], defaults["translucency"], defaults["stochastic"],
            defaults["return_mode"], defaults["extinction"], defaults["backscatter"],
            message,
        )

    reset.click(
        reset_defaults,
        outputs=[fog, dust, smoke, simulate, translucency, stochastic,
                 return_mode, extinction, backscatter, status],
    )


def _build_demo(cfg):
    with gr.Blocks(title="Tempo × rerun control") as demo:
        gr.Markdown("## Tempo × rerun — control panel")
        with gr.Accordion("Streams", open=True):
            _streams_section()
        if cfg.media_demo:
            with gr.Accordion("Participating media", open=True):
                _media_demo_section()
        property_editor(_bridge, demo)
    return demo


def launch_control_panel(loop, cfg, client) -> None:
    """Launch the Gradio panel (non-blocking) on the main thread.

    Runs on the main thread so Gradio's queue self-request works; building makes
    no API calls (the actor list loads lazily), so there's nothing to marshal onto
    the not-yet-running loop. See tempo_panel for the full rationale.
    """
    global _bridge, _client
    _bridge = AsyncBridge(loop)
    _client = client
    try:
        demo = _build_demo(cfg)
        demo.queue()
        port = find_free_port(cfg.control_port)
        if port != cfg.control_port:
            print(f"  Port {cfg.control_port} busy; using {port}")
        demo.launch(server_port=port, show_error=True, inbrowser=False,
                    quiet=True, prevent_thread_lock=True)
        print(f"  Control panel: http://localhost:{port}")
    except Exception:
        print("  [control] panel failed to start:\n" + traceback.format_exc())
