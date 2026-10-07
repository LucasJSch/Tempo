# Copyright Tempo Simulation, LLC. All Rights Reserved

"""Launch the camera/lidar viewer for /TempoSensors/Maps/TempoLidarMediaDemo."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from RerunPlayground.__main__ import amain
from RerunPlayground.config import parse_config


def main():
    cfg = parse_config()
    cfg.media_demo = True
    cfg.app_id = "tempo_lidar_participating_media_demo"
    cfg.include_static = True
    try:
        asyncio.run(amain(cfg))
    except KeyboardInterrupt:
        print("\nBye!\n")
    except RuntimeError as exc:
        raise SystemExit(f"Participating-media demo could not start: {exc}") from exc


if __name__ == "__main__":
    main()
