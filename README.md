# Tempo Lidar Media Demo

This branch was created specifically for the Tempo lidar participating-media demo.

The demo shows an RGB camera and lidar looking through fog, dust, and smoke. It demonstrates:

- Lidar attenuation and returns produced by participating media.
- Primary and secondary lidar echoes in Dual return mode.
- Forward-facing and overhead views of the same lidar point cloud.
- Live controls for the media effects and lidar settings.

## Run the demo

Tempo must be inside an Unreal project's `Plugins/Tempo` directory. Unreal Engine 5.7 or 5.8 and a real GPU renderer are required.

From the Tempo directory, set up and build the host project:

```bash
./Scripts/Setup.sh
./Scripts/Build.sh
```

On Linux, set `UNREAL_ENGINE_PATH` before running these scripts.

Open the demo map:

```bash
./Scripts/Run.sh /TempoSensors/Maps/TempoLidarMediaDemo
```

Press **Play** in Unreal. Then, in another terminal:

```bash
source ../../TempoEnv/bin/activate
pip install -r ExampleClients/Python/RerunPlayground/requirements.txt
python ExampleClients/Python/ParticipatingMediaDemo.py --reset-layout
```

The Rerun viewer opens with the RGB, forward lidar, and overhead lidar views. The live control panel is available at http://localhost:7860.

Do not run this demo with `-nullrhi`; the camera and lidar media simulation require GPU rendering.
