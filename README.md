# Configurator

Automation for generating a car "paint configurator" asset: given a spreadsheet of official paint colors, it builds one Maya/V-Ray render layer per color, then assembles the rendered passes into a single layered Photoshop file that a compositor/marketing team can toggle through.

The pipeline has two stages, run in two different applications:

1. **`MayaConfigurator.py`** (runs inside Autodesk Maya) — reads a color list from Excel and creates a V-Ray render layer for every color/finish combination.
2. **`PhotoshopConfigurator.py`** (runs standalone, using the third-party [PhotoshopAPI](https://github.com/EmilDohne/PhotoshopAPI) library — Adobe Photoshop itself does not need to be installed) — takes the rendered `.exr` passes and assembles them into a single grouped, layered `.psd`, or composites them into flat `.png` previews.

`testing.py` is a small scratch script for inspecting the layer structure of a generated `.psd`.

## How it works

### 1. Color list (Excel)

The input is an Excel sheet (e.g. `G70_Individual_Color_List_0423.xlsx`) with one row per paint color. The columns the scripts care about (by position):

| Index | Column | Example |
|---|---|---|
| 3 | Name | `PHYTONIC BLUE METALLIC` |
| 5 | Hex (`#RRGGBB`) | `#264185` |
| 6 | Base color / family | `blue` |
| 7 | Finish/Lackart | `Metallic`, `Uni`, `Frozen` |

`read_excel_rows()` loads the sheet with `pandas` and hands back the rows as plain lists.

### 2. Maya: render layer generation (`MayaConfigurator.py`)

The Maya scene is expected to contain two `VRaySwitchMtl` shaders already assigned to the car geometry:

- `base_paint` — switches between `solid_carpaint` (`VRayMtl`) and `metallic_carpaint` (`VRayCarPaint2Mtl`)
- `twotone_paint` — same idea, but also carries the two fixed two-tone finishes (`twotone_black`, `twotone_gray`)

For each row in the spreadsheet, `configurator()`:

1. Cleans up the color name (title-cases it, fixes `Ii` → `II`, strips spaces/dots/dashes) and builds a render-layer name from `<base color>_<color name>`.
2. Converts the hex color to RGB (`colormath`) and then from sRGB into the scene's working colorspace, **ACEScg** (`colour`), since V-Ray renders/shades in linear ACEScg.
3. Maps the "Lackart" finish to a shader index and a clearcoat flag:
   - `Metallic` → metallic carpaint shader, clearcoat glossiness `0.99`
   - `Uni` → solid carpaint shader, clearcoat glossiness `0.99`
   - `Frozen` → metallic carpaint shader, glossiness `0.78` (matte/frozen look)
4. Calls `create_rl()`, which uses Maya's `renderSetup` API to:
   - create a new render layer,
   - add a collection that selects the whole scene,
   - add a collection per switch material with an absolute override on `.materialsSwitch` to pick the right shader index,
   - add a collection on the resolved carpaint shader with absolute overrides on `base_color`/`color` (and `coat_glossiness` for metallics) set to the converted ACEScg color.

The result is one render layer per catalogue color, ready to be batch-rendered to `.exr`.

### 3. Photoshop: layer assembly (`PhotoshopConfigurator.py`)

Once the render layers have been rendered out to `.exr` (one file per color/pass, following a `..._renderRender<Pass>_<Color>_...` naming convention), this script builds the final deliverable using `psapi` (PhotoshopAPI), `OpenImageIO`, and `OpenCV`:

- **`ingest(folder)`** — the main entry point:
  1. Recursively collects all `.exr` files under `folder`.
  2. Derives group names from the filenames (one group per render pass, plus a `Car` base group and a `Two Tone` group) via regex.
  3. Creates an 8-bit RGB layered Photoshop document sized to match the renders, with one group layer per pass (base car layer at the bottom, two-tone layer on top).
  4. For every `.exr`: converts ACEScg → sRGB and re-encodes to 8-bit PNG (`convert_exr`, via OpenImageIO), loads it into the packed/planar array layout `psapi` expects (`load_image`), wraps it in an image layer, and inserts it into the matching group.
  5. Saves the assembled file (hardcoded to `.../configurator/BMW_config.psd`).
- **`compose(folder)`** — an alternative, simpler path that flattens each carpaint render over the base car and the two-tone-gray pass using `ImageBufAlgo.over`, converts to sRGB, and writes one flat PNG per color directly to disk (no Photoshop file involved).

`testing.py` just re-opens a generated `.psd` and prints its group/layer names, to sanity check the output of `ingest()`.

## Requirements

- **Maya stage**: Autodesk Maya with V-Ray, run inside Maya's Python interpreter (`maya.cmds`, `maya.api.OpenMaya`, `maya.app.renderSetup`), plus `pandas`, `colormath`, `colour`, `numpy`.
- **Photoshop stage**: a standalone Python 3.10 environment (this repo ships one under `Scripts/`/`Lib/`) with `psapi` — the Python bindings for [PhotoshopAPI](https://github.com/EmilDohne/PhotoshopAPI), a third-party (non-Adobe) C++ library for reading/writing `.psd`/`.psb` files — plus `OpenImageIO`, `opencv-python` (`cv2`), `numpy`. **Adobe Photoshop does not need to be installed** — `psapi` reads/writes the `.psd`/`.psb` file format directly, independent of the Photoshop application.
- An OCIO config for ACES 1.2 color management (path is currently hardcoded to `Z:/OCIO/aces_1.2/config.ocio`).

## Usage

Both scripts currently drive themselves via a hardcoded call at the bottom of the file rather than a CLI, so running them means editing that line first:

```python
# MayaConfigurator.py — run inside Maya's Script Editor
configurator("PATH/TO/EXCELFILE.xlsx")
```

```python
# PhotoshopConfigurator.py — run with the standalone Python env
ingest("path/to/rendered/exr/folder")
# or, for flat PNG previews instead of a layered PSD:
# compose("path/to/rendered/exr/folder")
```

## Notes / known limitations

- Several filesystem paths (OCIO config, output `.psd`/`.png` locations) are hardcoded to a specific user's machine and need to be adjusted before running elsewhere.
- The scripts assume fixed naming conventions for both the Maya shaders (`base_paint`, `twotone_paint`, `metallic_carpaint`, `solid_carpaint`) and the rendered `.exr` filenames (`renderRenderCar`, `TwoToneBlack`, `TwoToneGray`, `renderRender<Pass>_<Color>_...`) — scenes/renders that deviate from these will need script changes.
- The repository also contains a full Python 3.10 virtual environment (`Lib/`, `Scripts/`, `Include/`, `share/`) checked into git; the actual source lives at the repo root (`MayaConfigurator.py`, `PhotoshopConfigurator.py`, `testing.py`).
