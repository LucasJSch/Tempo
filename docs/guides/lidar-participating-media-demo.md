# Lidar participating-media demo

The plugin-owned `/TempoSensors/Maps/TempoLidarMediaDemo` map puts a color camera and lidar at the
same pose, looking through three camera-visible media effects at opaque targets:

- tan translucent Niagara sprites model dust;
- dark translucent Niagara sprites model smoke;
- exponential height fog plus a local fog volume model fog.

The lidar starts in **Dual** return mode. Its ordinary return is drawn with the selected Rerun
signal; the other echo is magenta. This makes a medium return in front of a weakened target return
easy to identify.

## Run it

1. In an Unreal project with `TempoSensors` and `TempoWorld` enabled, open
   `/TempoSensors/Maps/TempoLidarMediaDemo` and start Play In Editor or Standalone Game.
2. Use a real deferred SM5 renderer. The demo cannot render under `-nullrhi`.
3. Install the Rerun example dependencies and expose Tempo's Python API:

   ```bash
   pip install -r ExampleClients/Python/RerunPlayground/requirements.txt
   export PYTHONPATH="$PYTHONPATH:$(pwd)/TempoCore/Content/Python/API"
   ```

4. Start the dedicated client:

   ```bash
   python ExampleClients/Python/ParticipatingMediaDemo.py --reset-layout
   ```

The native Rerun viewer shows the RGB image beside the 3D lidar cloud. The Gradio control panel at
`http://localhost:7860` can independently hide fog, dust, or smoke and can change the lidar's
participating-media switch, translucent-media pass, return mode, extinction, backscatter, and
stochastic range sampling. **Reset tuned defaults** restores the map's intended comparison.

## What to look for

Turn **Simulate media in lidar** off first. The camera remains obscured but the lidar sees the rear
targets as though the media were absent. Turn it on and select **Dual**: near medium echoes appear,
rear target intensities fall, and sufficiently weak surfaces disappear. Dust is deliberately light
and produces stronger medium echoes than the dark smoke. Disabling **Include translucent
dust/smoke** removes those two effects from the lidar while leaving them visible to the camera;
the fog remains because it comes through Unreal's fog rendering data rather than the translucent
primitive pass.

This is an editor demo and is intentionally not listed in `AlwaysCookMaps`. Add the map to a host
project's packaging settings if it is needed in a packaged build.
