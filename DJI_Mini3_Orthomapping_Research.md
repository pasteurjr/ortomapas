# DJI Mini 3 Orthomapping - Comprehensive Research Guide

**Research compiled: March 2025 (Sections 1-7), March 2026 (Section 8)**

---

## Table of Contents

1. [DJI Mini 3 Camera Specifications](#1-dji-mini-3-camera-specifications)
2. [Litchi Pilot App](#2-litchi-pilot-app)
3. [Other Flight Planning Software](#3-other-flight-planning-software)
4. [Photogrammetry / Orthomosaic Software](#4-photogrammetry--orthomosaic-software)
5. [Best Practices for DJI Mini 3 Orthomapping](#5-best-practices-for-dji-mini-3-orthomapping)
6. [GIS Analysis Tools](#6-gis-analysis-tools)
7. [AI/ML Tools for Drone Imagery Analysis](#7-aiml-tools-for-drone-imagery-analysis)
8. [Regions Near Belo Horizonte for Drone Orthomapping](#8-regions-near-belo-horizonte-for-drone-orthomapping)

---

## 1. DJI Mini 3 Camera Specifications

Understanding the camera specs is critical for calculating GSD, overlap, and mission parameters.

| Spec | Value |
|------|-------|
| **Sensor** | 1/1.3-inch CMOS |
| **Effective Pixels** | 48 MP |
| **Max Photo Resolution** | 8064 x 6048 px (48MP) / 4032 x 3024 px (12MP) |
| **Focal Length** | 24mm equivalent (actual ~6.7mm) |
| **Aperture** | f/1.7 (fixed) |
| **Field of View** | 82.1 degrees |
| **Focus Range** | 1m to infinity |
| **Photo Formats** | JPEG, DNG (RAW) |
| **ISO Range** | 100-3200 |
| **Shutter Speed** | 2s to 1/8000s (electronic) |
| **Gimbal** | 3-axis mechanical stabilization |
| **Weight** | < 249g |

### Battery and Flight Time

| Battery Type | Rated Flight Time | Real-World Mapping Time |
|---|---|---|
| Standard Intelligent Flight Battery | 38 min | ~25-28 min |
| Intelligent Flight Battery Plus | 51 min | ~35-40 min |

**Note:** Real-world mapping flight time is typically 70-75% of rated time due to wind, maneuvering, acceleration/deceleration at waypoints, and safety margins (always land with >20% battery).

---

## 2. Litchi Pilot App

### 2.1 DJI Mini 3 Compatibility

- **You MUST use "Litchi Pilot"** (NOT the older "Litchi for DJI Drones" app)
- The original Litchi app does NOT support Mini 3, Mini 3 Pro, Mini 4 Pro, or other newer DJI drones
- Litchi Pilot is available on both iOS and Android
- **Version 5.0.0** (December 2025) added battery-swap mission recovery and improved waypoint flight management

### 2.2 Litchi Mission Hub (Web Planner)

**URL:** https://flylitchi.com/hub

The Mission Hub is a web-based planning interface where you:

1. **Plan waypoint missions** on a satellite map using your browser
2. **Set waypoint parameters:** altitude, speed, heading, gimbal pitch, actions (take photo, start/stop recording)
3. **Save missions** to your Litchi account
4. **Sync automatically** to the Litchi Pilot mobile app when connected to the internet
5. **Execute missions** using Litchi Pilot on your phone/tablet connected to the drone

### 2.3 Creating Grid/Lawnmower Missions for Orthomapping

Litchi Mission Hub does **NOT** have a built-in grid/survey mission generator. To create orthomapping missions, you need external tools that generate Litchi-compatible CSV waypoints:

#### Option A: Drone Grid Mission Planner (dronegrid.web.id) - RECOMMENDED

**URL:** https://www.dronegrid.web.id/

This is a **free, browser-based** tool that generates automated flight paths. Key features:

- **6 Mission Modes:** Grid (lawnmower), Corridor, Facade, Orbit, Helix, Panorama
- **Grid Mode** is ideal for orthomosaics:
  - Draw a polygon around the target area
  - Set altitude, front overlap (75% recommended), side overlap (70% recommended)
  - Set flight speed (typically 3-5 m/s for mapping)
  - Set gimbal pitch to -90 degrees (nadir/straight down)
  - Auto-calculates GSD based on drone camera specs
  - Auto-calculates line spacing and photo trigger intervals
- **Terrain following** using Copernicus DEM data (maintains constant AGL)
- **Multi-battery splitting** (automatically splits missions exceeding 99 waypoints, which is Litchi's limit)
- **Double-grid mode** for cross-hatch 3D coverage
- **GSD quality badges** (Ultra/Standard/Low)
- **50+ drone presets** including DJI Mini 3/Mini 3 Pro
- **Export to Litchi CSV** format

**Workflow:**
1. Go to dronegrid.web.id
2. Select your drone (DJI Mini 3)
3. Draw polygon around survey area
4. Configure: altitude, overlap %, speed, gimbal angle
5. Click "Download CSV"
6. Go to flylitchi.com/hub -> Missions -> Import CSV
7. Open Litchi Pilot app, sync missions
8. Fly the mission

#### Option B: QGIS UAV Mapping Path Generator Plugin

**Plugin URL:** https://plugins.qgis.org/plugins/drone_path/

- Generates Litchi-compatible CSV from a polygon layer in QGIS
- Allows setting drone camera parameters (sensor width, focal length, image dimensions)
- Outputs .csv that can be uploaded directly to Litchi Mission Hub
- Good if you already have survey boundaries in GIS format

#### Option C: DJIFlightPlanner

**URL:** https://www.djiflightplanner.com/

- Desktop/web tool for planning grid missions
- Can export waypoints compatible with Litchi
- Provides GSD calculations and coverage estimates

#### Option D: UgCS + Litchi Integration

**URL:** https://www.sphengineering.com/flight-planning/ugcs/litchi

- Professional flight planning software (UgCS)
- Plans missions and exports to Litchi CSV format
- More suitable for complex, multi-flight professional surveys

### 2.4 Litchi CSV Format

The CSV format is simple with one waypoint per line. Minimum required columns:
- Column 1: Latitude (decimal degrees)
- Column 2: Longitude (decimal degrees)
- Column 3: Altitude (meters, optional)

Additional columns control: heading, curve size, rotation direction, gimbal pitch angle, and actions at each waypoint (e.g., take photo).

### 2.5 Mission Sync Process

1. Save/import mission in Mission Hub (flylitchi.com/hub)
2. Open Litchi Pilot app on your mobile device
3. Missions sync automatically over internet
4. Select the mission in the app
5. Connect to DJI Mini 3, verify waypoints on the map
6. Start the mission

### 2.6 Important Litchi Tips for Mini 3

- **Force stop DJI Fly app** before launching Litchi Pilot to prevent conflicts
- **Reset controls to DJI standard** in DJI Fly before using Litchi (custom control settings can cause "Flight Ended" errors)
- Litchi Pilot supports **terrain following** capability
- Maximum **99 waypoints per mission** (use multi-battery splitting for large areas)
- **Version 5.0.0+** supports resuming missions after battery swap

---

## 3. Other Flight Planning Software

### 3.1 DJI Fly App

- The official DJI app for Mini 3
- **Does NOT have automated survey/mapping mission modes**
- Supports basic waypoint missions (on some models) via built-in waypoint feature
- **No grid pattern generation**, no overlap calculation, no photogrammetry automation
- Useful for manual mapping flights using Spotlight and POI modes
- Can import KMZ waypoint files (on supported drones)

### 3.2 Dronelink

**URL:** https://www.dronelink.com/

- **Supports DJI Mini 3** (requires downloading the correct app version from dronelink.com/download, NOT from Google Play)
- **Paid subscription required** for automated flight control
- Features:
  - Pre-plan missions on web or in-app
  - 3D flight path preview
  - Mission estimates (flight time, data capture)
  - Virtual drone simulation before actual flight
  - Hybrid manual/auto flight modes
  - Multi-component mission combining
- **More powerful than Litchi** for complex, repeatable commercial missions
- Includes mapping-specific mission components with grid patterns

### 3.3 Maven

**URL:** https://www.mavenpilot.com/

- Cross-platform (iOS, Android, Web via MavenRoute)
- **Supports DJI Mini 3** for autonomous flight planning
- **Photogrammetry-specific features:**
  - Auto-split for large mapping missions by flight time
  - Battery management optimization
  - Mission preview in 2D, 3D, and FPV mode
- MavenRoute web planner syncs to Maven mobile app
- Active development of additional photogrammetry tools (2025)

### 3.4 WaypointMap

**URL:** https://www.waypointmap.com/

- **Free automated mapping tool** by YouTuber Jays Tech Vault
- Supports DJI Mini 4 Pro, Mini 5, Mavic 3/4, Air 3/3S
- **DJI Mini 3 may NOT be supported** (not explicitly listed - supports waypoint-capable DJI Fly drones)
- Generates KMZ files for import into DJI Fly app
- Grid intersection waypoints for orthomosaic mapping
- Adjustable overlap percentage and photo interval

### 3.5 DJI Pilot 2

- Enterprise-focused flight planning app
- Designed for Matrice and Enterprise series drones
- **Does NOT support DJI Mini 3**
- Has built-in mapping/survey mission planning

### 3.6 Comparison Summary

| Software | Mini 3 Support | Grid Missions | Cost | Ease of Use |
|---|---|---|---|---|
| **Litchi Pilot + Grid Planner** | YES | Via CSV import | ~$25 one-time | Medium |
| **Dronelink** | YES | Built-in | Subscription ($15+/mo) | Medium-High |
| **Maven** | YES | Built-in | Freemium | Medium |
| **WaypointMap** | Uncertain | Built-in | Free | Easy |
| **DJI Fly** | YES (manual only) | NO | Free | Easy |

---

## 4. Photogrammetry / Orthomosaic Software

### 4.1 OpenDroneMap / WebODM (Free, Open Source) - RECOMMENDED

**URLs:**
- https://opendronemap.org/
- https://github.com/OpenDroneMap/WebODM
- Cloud version: https://webodm.net/

**Overview:**
- Completely **free and open source** (self-hosted)
- WebODM provides a user-friendly web interface
- Can also be used from command line (ODM)
- Processes up to 3,000 images per task

**Outputs:**
- Georeferenced orthomosaics (GeoTIFF)
- Digital Surface Models (DSM)
- Digital Terrain Models (DTM)
- 3D textured meshes
- Point clouds (LAS/LAZ)

**Key Processing Parameters:**
- `--dsm` / `--dtm` flags to generate elevation models
- `--orthophoto-resolution` - cm/pixel (default: 5)
- `--dem-resolution` - recommended 1/4 of orthophoto resolution
- Point cloud quality: ultra/high/medium/low (medium default; each step up = ~4x processing time)
- SMRF filter parameters for DTM: `--smrf-scalar`, `--smrf-slope`, `--smrf-threshold`, `--smrf-window`
- `--mesh-octree-depth` - 8-12 recommended (default 11)

**DJI Mini 3 Compatibility:**
- Fully compatible - reads EXIF/XMP GPS data from JPEG and DNG files
- Proven results: users report ~1.4cm GSD at 40m altitude, ~2cm after processing
- GPS error of ~0.47m achievable without GCPs

**Installation (Docker):**
```bash
git clone https://github.com/OpenDroneMap/WebODM
cd WebODM
./webodm.sh start
```

### 4.2 Agisoft Metashape

**URL:** https://www.agisoft.com/

- **Desktop-based** professional photogrammetry software
- **One-time perpetual license** (no subscription): ~$179 Standard, ~$3,499 Professional
- Maximum control over processing pipeline
- Supports GCPs (Ground Control Points) for survey-grade accuracy
- Excellent for large datasets
- **Standard Edition** is sufficient for orthomosaics and DEMs
- Works with all DJI Mini 3 images (JPEG, DNG)
- Outputs: orthomosaics, DEMs, point clouds, 3D models, contour maps

**Advantages:** Buy-once model, local processing, extremely flexible, wide format support
**Disadvantages:** Steeper learning curve, requires good hardware (RAM-intensive)

### 4.3 Pix4D

**URL:** https://www.pix4d.com/

- **Cloud + Desktop** platform
- Products: Pix4Dmapper (desktop), Pix4Dcloud (cloud), Pix4Dfields (agriculture), Pix4Dreact (emergency)
- **Subscription pricing**: ~$350/month or ~$4,990 perpetual for Pix4Dmapper
- Very user-friendly, automated processing
- Built-in quality reports
- Compatible with DJI Mini 3 imagery
- Drone pilots with no prior experience can produce usable orthomosaics in an afternoon

**Advantages:** Easy to use, excellent documentation, cloud processing option
**Disadvantages:** Expensive subscription model

### 4.4 DroneDeploy

**URL:** https://www.dronedeploy.com/

- **Fully cloud-based** platform
- Subscription pricing (~$329/month for Advanced)
- Automated processing pipeline
- Real-time mapping and collaboration features
- Best for teams and enterprise deployments
- Compatible with DJI Mini 3 images (upload and process)

**Advantages:** Easiest to use, real-time collaboration, no local hardware needed
**Disadvantages:** Most expensive, requires internet, cloud-only

### 4.5 Other Free/Open Source Options

| Software | Description | Limitations |
|---|---|---|
| **3DF Zephyr Free** | Desktop photogrammetry | Max 50 photos per project |
| **Meshroom (AliceVision)** | Open source, GPU-accelerated | Primarily 3D reconstruction, limited orthomosaic support |
| **COLMAP** | Open source SfM + MVS | Command-line, no orthomosaic export |
| **VisualSFM** | Open source structure from motion | Outdated, limited features |

### 4.6 Software Comparison Summary

| Software | Cost | Processing | Best For | DJI Mini 3 |
|---|---|---|---|---|
| **WebODM/ODM** | Free (self-hosted) | Local | Budget-conscious, full control | YES |
| **WebODM Lightning** | Pay per task | Cloud | Occasional use, no hardware | YES |
| **Agisoft Metashape** | $179-$3,499 once | Local | Professional, long-term | YES |
| **Pix4Dmapper** | $350/mo or $4,990 | Local/Cloud | Professional, easy workflow | YES |
| **DroneDeploy** | $329/mo | Cloud | Teams, enterprise | YES |
| **3DF Zephyr Free** | Free | Local | Small projects (<50 photos) | YES |

---

## 5. Best Practices for DJI Mini 3 Orthomapping

### 5.1 Optimal Flight Altitude

| Altitude (AGL) | Approx GSD (48MP) | Approx GSD (12MP) | Use Case |
|---|---|---|---|
| 30m | ~0.7 cm/px | ~1.4 cm/px | Detailed inspection, small areas |
| 40m | ~1.0 cm/px | ~1.9 cm/px | High-detail mapping |
| 50m | ~1.2 cm/px | ~2.4 cm/px | **General purpose mapping (recommended)** |
| 60m | ~1.4 cm/px | ~2.9 cm/px | Medium detail mapping |
| 80m | ~1.9 cm/px | ~3.8 cm/px | Larger area coverage |
| 100m | ~2.4 cm/px | ~4.8 cm/px | Maximum coverage per battery |
| 120m | ~2.9 cm/px | ~5.7 cm/px | Large-area overview |

**GSD Formula:**
```
GSD (cm/px) = (Sensor Width mm * Altitude m * 100) / (Focal Length mm * Image Width px)
```

For DJI Mini 3 at 48MP (sensor ~9.6mm, focal ~6.7mm, width 8064px):
```
GSD = (9.6 * H * 100) / (6.7 * 8064) = 0.01776 * H cm/px
```

### 5.2 Overlap Settings

| Parameter | Minimum | Recommended | High Quality |
|---|---|---|---|
| **Front (Forward) Overlap** | 65% | 75% | 80% |
| **Side (Lateral) Overlap** | 60% | 70% | 75% |

- **Higher overlap = better stitching** but more photos, longer flight, more processing time
- For areas with **homogeneous textures** (water, sand, uniform crops): use 80%/75%
- For areas with **varied features** (buildings, mixed vegetation): 75%/70% is sufficient
- **Never go below 60% side overlap** - stitching will likely fail

### 5.3 Camera Settings for Mapping

**Recommended settings:**
- **Shoot in 48MP mode** for maximum resolution (DNG + JPEG if storage allows)
- **Gimbal pitch: -90 degrees** (straight down / nadir)
- **Manual exposure** preferred:
  - ISO: as low as possible (100-200 in bright conditions)
  - Shutter speed: 1/500 or faster to avoid motion blur
  - Adjust EV in small increments to get aperture between f/4000-5000 equivalent exposure
- **Focus: set to infinity** after reaching operating altitude (autofocus first, then lock)
- **White balance: fixed** (e.g., Sunny) - do not use Auto WB as it changes between shots
- **Photo format: JPEG** is sufficient for most orthomosaics; DNG (RAW) for maximum quality
- **Interval shooting:** use timed interval or distance-based triggering via mission planner

### 5.4 Flight Speed

| Altitude | Recommended Speed | Notes |
|---|---|---|
| 30-50m | 3-4 m/s (~7-9 mph) | Slower for sharp images at low altitude |
| 50-80m | 4-6 m/s (~9-13 mph) | Good balance of speed and quality |
| 80-120m | 5-8 m/s (~11-18 mph) | Can go faster at higher altitude |

**Rule of thumb:** At 250ft (76m), 6 mph with photos every 4 seconds achieves approximately 75%/75% overlap.

### 5.5 Coverage and Photos per Hectare

**Approximate calculations at 50m altitude, 75% front / 70% side overlap:**

- Image footprint (48MP): approximately 72m x 54m
- Effective advance per photo (75% front overlap): ~13.5m
- Line spacing (70% side overlap): ~21.6m
- **Photos per hectare: approximately 35-45 photos**
- **Coverage per battery (standard, ~25 min effective):** approximately 5-8 hectares
- **Coverage per battery (Plus, ~35 min effective):** approximately 8-12 hectares

**At 80m altitude, 75%/70% overlap:**
- **Photos per hectare: approximately 15-20 photos**
- **Coverage per battery (Plus):** approximately 15-25 hectares

These are rough estimates. Actual numbers depend on wind, terrain, turnaround time at grid edges, and safety margins.

### 5.6 Battery Management

- **Always plan to land with >20% battery** remaining
- The DJI Mini 3 Fly More Combo with 3 batteries is highly recommended for mapping
- **Litchi Pilot v5.0+** supports resuming missions after battery swap
- **Drone Grid Mission Planner** can auto-split missions for multi-battery flights
- **Plan flights in calm conditions** - wind significantly reduces the Mini 3's effective flight time
- **Pro tip:** Fly the farthest points first, closest points last (so if battery runs low, you're closer to home)

### 5.7 Pre-Flight Checklist for Mapping

1. Charge all batteries fully
2. Format SD card (use high-speed card, V30 or better)
3. Check weather - winds under 20 km/h ideal for Mini 3
4. Plan mission in grid planner, export CSV/KMZ
5. Import and sync mission to flight app
6. Set camera to 48MP, manual exposure, infinity focus
7. Set white balance to fixed (Sunny/Cloudy)
8. Enable GPS logging
9. Fly test pass to verify settings
10. Execute mapping mission

---

## 6. GIS Analysis Tools

### 6.1 QGIS (Free, Open Source)

**URL:** https://qgis.org/

QGIS is the most capable free GIS platform for working with drone orthomosaics.

**Key capabilities:**
- **Load orthomosaics:** directly open GeoTIFF files from WebODM/Pix4D/Metashape
- **Load DEMs:** DSM/DTM as raster layers
- **Raster Calculator:** compute vegetation indices (VARI, TGI, ExG) from RGB bands
- **Zonal Statistics:** extract statistics per plot/polygon from raster layers
- **Contour generation** from DEMs
- **Volume calculations** using DSM data
- **Slope and aspect analysis** from DTMs
- **Change detection:** compare orthomosaics from different dates
- **Map layouts and export** for reports

**Useful QGIS Plugins for Drone Orthomosaics:**
- **LFTools** - comprehensive drone mapping, surveying, image processing, spatial analysis
- **Camera2Geo** - converts raw drone images to georeferenced GeoTIFFs
- **UAV Mapping Path Generator (drone_path)** - generates Litchi-compatible CSV flight paths from polygon layers
- **GeoFlight Planner** - drone flight planning within QGIS
- **ViewDrone** - viewshed analysis for drone mission planning
- **Semi-Automatic Classification Plugin (SCP)** - land cover classification from raster imagery

**Basic orthomosaic analysis workflow in QGIS:**
```
1. Load orthomosaic GeoTIFF (Layer > Add Raster Layer)
2. Load DSM/DTM if available
3. Use Raster Calculator for vegetation indices:
   - VARI = (Green - Red) / (Green + Red - Blue)
   - TGI = Green - 0.39*Red - 0.61*Blue
   - ExG = 2*Green - Red - Blue
4. Classify using Reclassify or SCP plugin
5. Create map layout for export
```

### 6.2 PostGIS (Spatial Database)

**URL:** https://postgis.net/

- Extension for PostgreSQL that adds spatial capabilities
- Store orthomosaics, vector data, and metadata in a spatial database
- Perform server-side spatial queries and analysis
- **Raster support:** can store and query raster tiles (orthomosaics, DEMs)
- Ideal for multi-temporal analysis (compare surveys over time)
- Supports spatial indexing for fast queries on large datasets

**Use cases with drone orthomosaics:**
- Store multiple orthomosaics from different dates
- Query spatial intersections (e.g., which parcels overlap with areas of vegetation change)
- Serve data to QGIS, GeoServer, and web applications
- Automated change detection pipelines

**Example setup:**
```sql
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_raster;

-- Import orthomosaic
raster2pgsql -s 4326 -I -C -M orthomosaic.tif public.ortho_2025 | psql -d mydb

-- Import vector boundaries
shp2pgsql -s 4326 parcels.shp public.parcels | psql -d mydb

-- Spatial query example
SELECT p.id, ST_Area(p.geom) as area
FROM parcels p
WHERE ST_Intersects(p.geom, ST_MakeEnvelope(-8.5, 39.5, -8.4, 39.6, 4326));
```

### 6.3 GeoServer (Map Server)

**URL:** https://geoserver.org/

- Open source server for sharing geospatial data
- Serves orthomosaics as WMS/WFS/WMTS tiles
- Integrates with PostGIS as data source
- Enables web-based viewing of orthomosaics without downloading full files
- Supports OGC standards (WMS, WFS, WCS, WMTS)

**Use cases:**
- Publish orthomosaics as web map services
- Allow multiple users to view/analyze orthomosaics via web browser
- Integrate with Leaflet/OpenLayers web mapping applications
- Time-series visualization of multiple survey dates

### 6.4 Full Open-Source GIS Stack

```
Drone (DJI Mini 3)
    |
    v
Flight Planning (Litchi + Drone Grid Planner)
    |
    v
Image Processing (WebODM/OpenDroneMap)
    |
    v
Spatial Database (PostgreSQL + PostGIS)
    |
    v
Map Server (GeoServer) --> Web Applications
    |
    v
Analysis & Visualization (QGIS)
```

---

## 7. AI/ML Tools for Drone Imagery Analysis

### 7.1 Vegetation Analysis (RGB-Based Indices)

Since the DJI Mini 3 has an **RGB camera only** (no multispectral/NIR), true NDVI is not possible. However, several RGB-based proxies exist:

| Index | Formula | Effectiveness |
|---|---|---|
| **VARI** (Visible Atmospherically Resistant Index) | (G - R) / (G + R - B) | Good for plant health, accounts for atmospheric effects |
| **TGI** (Triangular Greenness Index) | G - 0.39*R - 0.61*B | Good proxy for chlorophyll content in high leaf cover |
| **ExG** (Excess Green) | 2*G - R - B | Simple green vegetation detection |
| **GLI** (Green Leaf Index) | (2*G - R - B) / (2*G + R + B) | Normalized green detection |
| **vNDVI** (Visible NDVI / Synthetic NDVI) | Uses R and G bands to predict NDVI | Requires calibration, less accurate than true NDVI |

**Important caveats:**
- RGB indices are **not as reliable as true NDVI** from multispectral cameras
- VARI and TGI work reasonably well for relative comparisons within a single survey
- Results vary with lighting conditions, time of day, and vegetation type
- Best used for **relative health comparison** (healthy vs stressed areas), not absolute measurements
- A University of Illinois study showed that **RGB + AI deep learning** can provide equivalent crop prediction at a fraction of multispectral camera cost

**QGIS Workflow for RGB Vegetation Indices:**
```
Raster Calculator:
  VARI = ("ortho@2" - "ortho@1") / ("ortho@2" + "ortho@1" - "ortho@3")

  Where: @1 = Red band, @2 = Green band, @3 = Blue band
```

### 7.2 Object Detection

#### YOLO (You Only Look Once) Models

- **YOLOv8 / YOLOv11** are the current state-of-the-art for real-time object detection
- Can detect and count objects in drone orthomosaics: trees, vehicles, buildings, animals, crop rows
- **Roboflow** (https://roboflow.com/) provides:
  - Pre-trained models for aerial/drone imagery
  - Dataset hosting and annotation tools
  - Training infrastructure
  - 1,863+ open-source YOLO aerial datasets available
  - Edge deployment (NVIDIA Jetson, etc.)
- **RF-DETR** (March 2025): Roboflow's new real-time detection model, small enough for edge deployment

**Workflow for drone imagery object detection:**
```
1. Collect orthomosaic or individual drone images
2. Annotate objects using Roboflow, CVAT, or Label Studio
3. Train YOLOv8/v11 model (can use Roboflow or local training)
4. Run inference on orthomosaic tiles
5. Georeference detections back to map coordinates
6. Visualize in QGIS
```

**Example use cases with DJI Mini 3 imagery:**
- Tree counting and canopy measurement
- Vehicle detection in parking lots
- Building footprint extraction
- Livestock counting
- Weed detection in agriculture
- Solar panel inspection

#### Other Object Detection Frameworks

- **Detectron2** (Meta) - instance segmentation and detection
- **MMDetection** - comprehensive detection toolbox
- **DOTA dataset** - standard benchmark for aerial object detection

### 7.3 Land Use / Land Cover Classification

**Tools and approaches:**

1. **Semi-Automatic Classification Plugin (SCP) for QGIS**
   - Supervised and unsupervised classification
   - Works with RGB orthomosaics
   - Supports Random Forest, SVM, and other classifiers
   - Free and integrated into QGIS

2. **Google Earth Engine** (cloud-based)
   - Can upload drone orthomosaics for classification
   - Machine learning classifiers (Random Forest, CART, SVM)
   - Free for research use

3. **Scikit-learn / TensorFlow / PyTorch** (custom)
   - Train custom land use classifiers
   - Pixel-based or object-based classification
   - Can use transfer learning from pre-trained models (ResNet, EfficientNet)

4. **Segment Anything Model (SAM)** by Meta
   - Zero-shot segmentation of drone imagery
   - Can segment features without training
   - Useful for initial feature extraction

### 7.4 Change Detection

**Comparing orthomosaics from different dates:**

1. **Image differencing** in QGIS Raster Calculator
2. **Band math** to create difference maps
3. **Deep learning** change detection:
   - Siamese networks
   - U-Net based architectures
   - Pre-trained models on aerial change detection datasets

**Practical workflow:**
```python
# Python example with rasterio and numpy
import rasterio
import numpy as np

with rasterio.open('ortho_date1.tif') as src1:
    img1 = src1.read()
with rasterio.open('ortho_date2.tif') as src2:
    img2 = src2.read()

# Simple difference map
diff = np.abs(img2.astype(float) - img1.astype(float))

# Threshold to detect significant changes
change_mask = np.mean(diff, axis=0) > threshold
```

### 7.5 Recommended Open-Source AI/ML Stack for Drone Analysis

```
Data Collection: DJI Mini 3 + Litchi Pilot
Processing: WebODM (orthomosaic generation)
Analysis Platform: Python (rasterio, geopandas, shapely)
Vegetation: QGIS Raster Calculator (VARI, TGI, ExG)
Object Detection: YOLOv8 + Roboflow
Classification: Scikit-learn or SCP (QGIS)
Segmentation: Segment Anything Model (SAM)
Change Detection: rasterio + numpy or deep learning
Visualization: QGIS + GeoServer
Database: PostGIS
```

---

## Key Sources and References

### Litchi & Flight Planning
- [Litchi for DJI Drones](https://flylitchi.com/)
- [Litchi Mission Hub](https://flylitchi.com/hub)
- [Litchi Help Documentation](https://flylitchi.com/help)
- [Litchi Pilot Changelog](https://flylitchi.com/whats-new?a=com.flylitchi.litchipilot.dji&c=beta)
- [Free Drone Grid Mission Planner](https://www.dronegrid.web.id/)
- [QGIS UAV Mapping Path Generator Plugin](https://plugins.qgis.org/plugins/drone_path/)
- [Litchi Forum - Smart Grid & 3D Terrain Mission Planning](https://forum.flylitchi.com/t/smart-grid-3d-terrain-based-mission-planning-tool-for-litchi/23630)
- [DJIFlightPlanner + Litchi Tutorial](https://www.djiflightplanner.com/documents/Using_DJIFlightPlanner_with_Litchi.pdf)
- [UgCS + Litchi Integration](https://www.sphengineering.com/flight-planning/ugcs/litchi)

### Flight Planning Alternatives
- [Dronelink](https://www.dronelink.com/)
- [Maven Pilot](https://www.mavenpilot.com/)
- [WaypointMap](https://www.waypointmap.com/)
- [DJI Mini 3 Specs](https://www.dji.com/mini-3/specs)

### Photogrammetry Software
- [OpenDroneMap](https://opendronemap.org/)
- [WebODM GitHub](https://github.com/OpenDroneMap/WebODM)
- [WebODM Lightning (Cloud)](https://webodm.net/)
- [ODM Documentation - Options & Flags](https://docs.opendronemap.org/arguments/)
- [Agisoft Metashape](https://www.agisoft.com/)
- [Pix4D](https://www.pix4d.com/)
- [DroneDeploy](https://www.dronedeploy.com/)
- [Litchi Pilot Beta with Mini 3 Pro - ODM Community](https://community.opendronemap.org/t/litchi-pilot-beta-with-mini-3-pro/19194)

### Best Practices & GSD
- [DJI Mini 3 Pro for Mapping - Droneblog](https://www.droneblog.com/dji-mini-3-pro-for-mapping/)
- [Precision Mapping with DJI Mini 3 Pro and Litchi - sUAS News](https://www.suasnews.com/2023/11/precision-mapping-with-the-dji-mini-3-pro-and-litchi/)
- [Understanding GSD for Drone Surveying - heliguy](https://www.heliguy.com/blogs/posts/understanding-gsd-for-drone-surveying/)
- [Orthomosaics: How to Produce High-Quality Maps - Mapware](https://mapware.com/2025/02/04/orthomosaics-how-to-produce-high-quality-orthomosaic-maps/)
- [Mapping Settings Discussion - MavicPilots](https://mavicpilots.com/threads/mapping-settings.140830/)

### GIS Tools
- [QGIS](https://qgis.org/)
- [PostGIS](https://postgis.net/)
- [GeoServer](https://geoserver.org/)
- [LFTools QGIS Plugin](https://plugins.qgis.org/plugins/lftools/)
- [Drone Mapping in QGIS Tutorial](https://qgis-in-mineral-exploration.readthedocs.io/en/latest/source/drone_mapping/index.html)
- [QGIS for Drone Mapping Display and Analysis](https://manyatechnologies.com/qgis-drone-mapping-display-analysis/)

### AI/ML & Vegetation Analysis
- [Understanding Vegetation Indices - DroneDeploy](https://help.dronedeploy.com/hc/en-us/articles/1500004860841-Understanding-Vegetation-Indices)
- [vNDVI Research Paper](https://swfrec.ifas.ufl.edu/docs/pdf/precision-ag-eng/2020-172-Ampatzidis-Computers-Electronics-Agriculture.pdf)
- [Vegetation Indices - Pix4D](https://www.pix4d.com/blog/pix4dfields-vegetation-indices-for-precision-agriculture)
- [RGB Camera + AI for Vegetation Data - University of Illinois](https://aces.illinois.edu/news/using-standard-rgb-camera-and-ai-obtain-vegetation-data)
- [Roboflow Universe](https://universe.roboflow.com/)
- [YOLOv8](https://yolov8.com/)
- [QGIS SCP Plugin for Classification](https://plugins.qgis.org/plugins/tags/drone/)

---

## 8. Regions Near Belo Horizonte for Drone Orthomapping

**Research compiled: March 2026**

This section covers ten regions near Belo Horizonte, Minas Gerais, Brazil that present excellent opportunities for drone orthomapping with a DJI Mini 3, along with comprehensive Brazilian drone regulations.

---

### 8.1 Brazilian Drone Regulations (ANAC / DECEA)

#### 8.1.1 ANAC RBAC-E No. 94

The Brazilian National Civil Aviation Agency (ANAC) regulates drone operations through RBAC-E No. 94 (Regulamento Brasileiro de Aviacao Civil Especial). Key rules:

**Weight Categories:**
- **Class 3:** Up to 25 kg (includes DJI Mini 3 at 248g)
- **Class 2:** 25 kg to 150 kg
- **Class 1:** Above 150 kg

**Sub-250g Exemptions (critical for DJI Mini 3):**
- Drones under 250g (like the DJI Mini 3 at 248g) are **exempt from ANAC registration** for recreational use
- No mandatory third-party liability insurance required for under 250g
- No remote pilot license required for recreational flights under 120m AGL
- **IMPORTANT:** Using the DJI Intelligent Flight Battery Plus increases weight to ~290g, which pushes the aircraft above the 250g threshold, requiring ANAC registration and insurance

**General Operating Rules (all categories):**
- Maximum altitude: 120 m (400 ft) AGL unless special authorization
- Visual Line of Sight (VLOS) required at all times
- Minimum 30 m horizontal distance from uninvolved persons
- Minimum pilot age: 18 years
- Night flights require special authorization
- Flights over people are prohibited without authorization

**Upcoming Changes:**
- ANAC is developing RBAC No. 100 to replace RBAC-E No. 94, introducing risk-based operations classification using SORA (Specific Operations Risk Assessment) methodology. Public consultation deadline was July 2025.

Sources:
- [ANAC Drones Page](https://www.gov.br/anac/en/topics/drones)
- [RBAC-E No. 94 (English PDF)](https://www.anac.gov.br/en/drones/files/rbac-e-no-94-amdt-00-english.pdf)
- [Brazil Drone Laws 2025](https://drone-laws.com/drone-laws-in-brazil/)

#### 8.1.2 DECEA ICA 100-40

The Department of Airspace Control (DECEA) manages airspace access for drones through ICA 100-40/2023:

**SARPAS System (Sistema de Acesso de Aeronaves Remotamente Pilotadas):**
- All drone flights in controlled airspace or near airports must be registered via SARPAS (now SARPAS NG)
- Flight requests must be submitted in advance
- The system provides automated authorization for lower-risk flights

**Airspace Integration Categories:**
- **Segregated:** Other aircraft are kept out of the area during drone operation (most common for small drones)
- **Accommodated:** Drone allowed with special conditions (corridors, time windows)
- **Integrated:** Drone integrates with normal traffic (rarely possible for small drones)

**Airport Proximity Restrictions:**
- 5.4 km minimum from airports at low altitude
- ~9 km minimum when flying up to 120 m AGL
- CTR (Control Zone) and TMA (Terminal Maneuvering Area) require SARPAS authorization

**Prohibited Areas:**
- Airport safety zones
- Penitentiaries
- Critical infrastructure (power plants, energy stations)
- Military installations
- Any public area flight requires express DECEA authorization

Sources:
- [DECEA Drone Page](https://www.decea.mil.br/drone/en/)
- [SARPAS Access System](https://servicos.decea.mil.br/sarpas/)

#### 8.1.3 Belo Horizonte Metropolitan Area Airspace Restrictions

The BH metro area has complex airspace due to multiple airports:

**Airports affecting drone operations:**
1. **Tancredo Neves/Confins International Airport (SBCF)** - ICAO: SBCF, located 35 km north of BH center in Confins municipality. Major international airport with large CTR/TMA.
2. **Pampulha/Carlos Drummond de Andrade Airport (SBBH)** - Located within the urban area of Belo Horizonte. Restricted to smaller aircraft but creates a significant no-fly zone in central BH.
3. **Lagoa Santa Air Base (SBLS)** - Military airbase, ICAO: SBLS, coordinates -19.6618, -43.8974. Located near Confins. Creates additional restricted airspace.

**Practical Impact:**
- The northern portions of the BH metro (toward Lagoa Santa and Confins) are heavily restricted due to the overlapping CTR/TMA of SBCF and SBLS
- Central BH is restricted due to Pampulha Airport
- Southern and western areas (toward Nova Lima, Brumadinho, Itabirito) generally have less airspace conflict
- SARPAS authorization is mandatory for any flight within these controlled airspace zones

#### 8.1.4 National Parks and Conservation Units (ICMBio)

**Federal Conservation Units (managed by ICMBio):**
- Drone flights in national parks are **prohibited without prior authorization from ICMBio**
- Authorization is granted on a case-by-case basis, primarily for research and official documentation
- Application must include: research justification, flight plan, equipment details, insurance
- Process can take weeks to months
- Commercial/touristic drone flights are generally denied

**State Parks (managed by IEF-MG / Instituto Estadual de Florestas):**
- Similar restrictions apply; authorization from the state environmental agency (IEF) is required
- Each park administration may have specific additional rules

**Practical Approach for Researchers:**
- Partner with a Brazilian university or research institution
- Submit research project through ICMBio's SISBIO system (Sistema de Autorizacao e Informacao em Biodiversidade)
- Include drone flights explicitly in the research permit application

Sources:
- [ICMBio](https://www.gov.br/icmbio/)
- [Drone Laws in Brazilian National Parks](https://www.flyingglass.com.au/drone-laws-brazil/)

---

### 8.2 Serra do Cipo (Parque Nacional da Serra do Cipo)

**GPS Coordinates:** 19 deg 20'S, 43 deg 32'W (park center)
**Distance from BH center:** ~100 km northeast (approximately 1.5-2 hours by car via MG-010)
**Area:** 31,639 hectares (national park) + 100,000+ hectares (APA Morro da Pedreira buffer zone)

#### Location and Access
Serra do Cipo is located in the southern portion of the Espinhaco Range, one of the oldest mountain chains in South America (formed over 1 billion years ago). The park spans municipalities including Santana do Riacho, Jaboticatubas, Morro do Pilar, and Itambe do Mato Dentro.

#### What Makes It Interesting for Aerial Mapping

**Vegetation Types:**
- **Campos rupestres (rocky grasslands):** The dominant vegetation above ~900m, growing on quartzite outcrops. Extremely high endemism -- more endemic plant species than any other Brazilian ecoregion
- **Cerrado (Brazilian savanna):** Multiple physiognomies from campo limpo (grassland) to cerradao (woodland)
- **Atlantic Forest patches (capo de mata):** Forest islands within the grassland matrix
- **Gallery forests:** Along watercourses, providing dramatic contrast for aerial imagery
- **Over 1,600 catalogued plant species** including endemic bromeliads, orchids, and Velloziaceae (canela-de-ema)

**Geological Features:**
- Quartzite outcrops and ridges formed from marine deposits ~1.7 billion years ago
- Maximum altitude ~1,700 m
- Dramatic erosional landscapes, canyons, and waterfalls
- Visible geological layering and folding in exposed rock faces
- Sandy soils derived from quartzite weathering

**Endemic Fauna:**
- Cipo canastero (Asthenes luizae) -- endemic bird
- Cipo cinclodes (Cinclodes espinhacensis) -- endemic bird
- Hyacinth visorbearer hummingbird (Augastes scutatus)
- Numerous endemic reptiles and amphibians

#### Research/Analysis Opportunities with Drone Orthomaps
1. **Vegetation mapping and classification:** Distinguish campos rupestres, cerrado physiognomies, and forest patches using RGB imagery and derived vegetation indices (vNDVI, ExG)
2. **Erosion monitoring:** Track soil erosion on hiking trails and exposed quartzite areas
3. **Fire scar mapping:** Cerrado and campos rupestres experience frequent fires; orthomaps can track recovery
4. **Species habitat modeling:** Map microhabitat distribution for endemic species
5. **Phenology monitoring:** Seasonal changes in the striking flowering of campos rupestres plants (especially Vellozia spp.)
6. **Hydrological mapping:** Map headwater streams and wetlands

#### Drone Flight Restrictions
- **CRITICAL:** This is a Federal National Park managed by ICMBio. Drone flights require prior authorization through ICMBio/SISBIO
- Located far from major airports; airspace is generally uncontrolled (Class G) at the park's altitude
- SARPAS registration still recommended
- Low commercial air traffic in the area

#### Environmental Issues for Monitoring
- Fire management and recovery dynamics
- Trail erosion from increasing tourism
- Invasive species encroachment (especially grasses)
- Mining threats at park boundaries (quartzite extraction)
- Climate change impacts on high-altitude vegetation

Sources:
- [Serra do Cipo National Park - Wikipedia](https://en.wikipedia.org/wiki/Serra_do_Cip%C3%B3_National_Park)
- [Serra do Cipo - USP](https://serradocipo.ib.usp.br/serra-do-cipo.html)
- [Campos Rupestres DEIMS-SDR](https://deims.org/fc558c06-d187-4dff-89b8-35df90297db8)
- [Campo Rupestre Biodiversity - FAPESP](https://agencia.fapesp.br/campo-rupestre-brazils-montane-savanna-is-a-hotspot-of-plant-life-diversity/28196)

---

### 8.3 Serra do Rola-Moca State Park (Parque Estadual da Serra do Rola-Moca)

**GPS Coordinates:** 20 deg 02'S, 44 deg 00'W (park center)
**Distance from BH center:** ~15-20 km south (within the metropolitan area)
**Area:** 3,941.09 hectares

#### Location and Access
The park is divided between four municipalities: Belo Horizonte, Nova Lima, Ibirite, and Brumadinho. It is one of the largest urban parks in Brazil, located within the Quadrilatero Ferrifero (Iron Quadrangle) region.

#### What Makes It Interesting for Aerial Mapping

**Vegetation Types:**
- **Ferruginous campos rupestres (campos ferruginosos):** Extremely rare vegetation growing on iron-rich canga crust. Found globally only in the Quadrilatero Ferrifero (MG) and Serra dos Carajas (PA)
- **Cerrado:** Various physiognomies
- **Atlantic Forest remnants:** Especially in valleys and south-facing slopes
- **Alpine/high-altitude grasslands**

**Geological Features:**
- **Canga (ferruginous laterite crust):** Iron-ceite hardpan formed by weathering of itabirite. Extremely hard, porous substrate that supports unique plant communities
- Located at the transition zone between Cerrado and Atlantic Forest biomes
- Part of the Espinhaco Mountain Range Complex

**Water Resources:**
- Contains springs critical to Belo Horizonte's water supply
- Multiple headwater streams

#### Research/Analysis Opportunities with Drone Orthomaps
1. **Canga vegetation mapping:** High-resolution mapping of the extremely rare ferruginous campo rupestre
2. **Urban-wildland interface monitoring:** Track urban encroachment, informal settlements, and edge effects
3. **Water source protection:** Map riparian zones and spring catchments feeding BH water supply
4. **Fire scar analysis:** Track prescribed burns and wildfire impacts
5. **Mining impact assessment:** Monitor proximity of mining operations to park boundaries
6. **Biodiversity corridor mapping:** Assess connectivity between park fragments

#### Drone Flight Restrictions
- State Park managed by IEF-MG; authorization required
- Proximity to Belo Horizonte urban area means potential overlap with Pampulha Airport CTR -- check SARPAS
- Southern portions are farther from airport influence
- Relatively accessible for repeated survey flights due to urban proximity

#### Environmental Issues for Monitoring
- Urban expansion pressure from all surrounding municipalities
- Mining activity at boundaries (Quadrilatero Ferrifero region)
- Water quality in springs supplying Belo Horizonte
- Illegal encroachments and informal construction
- Fire management in dry season

Sources:
- [Serra do Rola-Moca State Park - Wikipedia](https://en.wikipedia.org/wiki/Serra_do_Rola-Mo%C3%A7a_State_Park)
- [FIP Cerrado - Serra do Rola-Moca](https://csr.ufmg.br/fipcerrado/serra-do-rola-moca-state-park/)

---

### 8.4 Inhotim (Instituto Inhotim)

**GPS Coordinates:** 20 deg 07'S, 44 deg 13'W (approximate)
**Distance from BH center:** ~60 km west (approximately 1.5 hours by car)
**Total Area:** 1,942 acres (~786 hectares); visitation area: 140 hectares; RPPN (Private Natural Heritage Reserve): 250 hectares

#### Location and Access
Located in the municipality of Brumadinho, Minas Gerais, within the Atlantic Forest biome. Opened to the public in 2006.

#### What Makes It Interesting for Aerial Mapping

**Botanical Garden:**
- Over 4,300 native Brazilian plant species plus exotic specimens from around the world
- Certified botanical garden with active research programs
- 140 hectares of visitable gardens mixing forest fragments and curated landscapes
- 250 hectares of RPPN (private nature reserve) with Atlantic Forest

**Art Installations Visible from Air:**
- ~24 art "pavilions" distributed across the landscape
- Over 500 artworks currently on display from 100+ artists from 30 countries
- Large-scale outdoor sculptures and installations are clearly visible from aerial perspective
- Notable aerial-visible installations include large mirror works, colored pavilions, and landscape-integrated sculptures
- The geometric layout of galleries and paths creates interesting patterns when viewed from above

**Landscape:**
- Mix of curated botanical gardens, natural Atlantic Forest, lakes, and architectural structures
- Rolling terrain with water features
- Clear contrast between managed gardens and surrounding natural vegetation

#### Research/Analysis Opportunities with Drone Orthomaps
1. **Botanical garden canopy mapping:** Species distribution and canopy health monitoring across the gardens
2. **Art-landscape integration study:** How large-scale installations interact with natural topography (unique academic niche)
3. **RPPN Atlantic Forest monitoring:** Track forest health, canopy gaps, and regeneration in the 250-hectare reserve
4. **Visitor flow modeling:** Correlate pathway design with landscape features
5. **Water body monitoring:** Map artificial lakes and natural water features
6. **Urban-rural transition:** Study land use in surrounding areas post-Brumadinho dam disaster

#### Drone Flight Restrictions
- **Private property:** Authorization from Instituto Inhotim administration is required
- Not a public conservation unit (ICMBio/IEF not involved), but the RPPN portion has legal protections
- Located far from major airports; airspace likely uncontrolled (Class G)
- Brumadinho is ~25 km from Pampulha Airport -- should be outside the CTR but verify with SARPAS
- Note proximity to Brumadinho dam disaster site; some areas may have temporary flight restrictions

#### Environmental Context
- **Brumadinho Dam Disaster (January 25, 2019):** The Vale S.A. tailings dam collapsed ~10 km from Inhotim, releasing 12 million cubic meters of toxic tailings, killing 270 people, and devastating the Paraopeba River. Drone monitoring of ongoing environmental recovery in the surrounding region is highly relevant
- Atlantic Forest fragments in the region are under pressure from mining, agriculture, and urbanization

Sources:
- [Inhotim - Wikipedia](https://en.wikipedia.org/wiki/Inhotim)
- [Inhotim Botanical Garden](https://www.inhotim.org.br/en/institutional/botanical-garden/)
- [Brumadinho Dam Disaster - Wikipedia](https://en.wikipedia.org/wiki/Brumadinho_dam_disaster)

---

### 8.5 Serra da Piedade

**GPS Coordinates:** 19 deg 49'S, 43 deg 40'W (summit area)
**Distance from BH center:** ~50 km east
**Maximum Altitude:** 1,746 m

#### Location and Access
Located in the municipality of Caete, at the eastern border of the Belo Horizonte metropolitan region, within the Iron Quadrangle. The summit hosts a historic sanctuary (Santuario da Serra da Piedade).

#### Geological and Ecological Interest

**Geology:**
- Composed primarily of **itabirite** (banded iron formation) of the Caue Formation, Minas Supergroup
- Large outcrops showing intercalations of iron-rich and silica-rich layers
- Beautiful ductile structures: folds in various styles, shear zones, and faults
- Iron-bearing canga crust appears at ~1,200 m elevation
- Also contains quartz and gneiss formations
- The banded iron formations date to the Proterozoic era (~2.4 Ga minimum age)
- One of the best geological exposures of itabirite in the Quadrilatero Ferrifero

**Vegetation:**
- Ferruginous campos rupestres on canga at higher elevations
- Cerrado and Atlantic Forest at lower elevations
- High-altitude grasslands with endemic species

#### Research/Analysis Opportunities with Drone Orthomaps
1. **Geological outcrop mapping:** High-resolution 3D models of folded itabirite exposures for structural geology studies
2. **Canga ecosystem mapping:** Delineate and monitor the rare ferruginous campo rupestre
3. **Mining proximity assessment:** Monitor mining operations approaching from surrounding areas
4. **Erosion and weathering studies:** Track changes in exposed geological formations
5. **Religious heritage documentation:** 3D model of the historic sanctuary complex
6. **Altitudinal vegetation transects:** Map vegetation zonation from base to summit

#### Drone Flight Restrictions
- The summit area is a religious site; coordination with local authorities needed
- Not within a national/state park, but has natural monument protection
- Located east of BH; relatively far from Pampulha Airport but check for SBLS (Lagoa Santa) influence
- SARPAS authorization recommended

#### Environmental Issues
- Mining expansion in surrounding areas threatens the geological heritage
- Geoconservation of itabirite outcrops is a major concern in the Quadrilatero Ferrifero
- Tourism pressure on summit trails and vegetation

Sources:
- [Serra da Piedade Geology - ResearchGate](https://www.researchgate.net/figure/Map-showing-Espinhaco-Mountain-Range-EMR-a-Serra-da-Piedade-Range-Minas-Gerais_fig1_262616169)
- [Geoconservation in Quadrilatero Ferrifero - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2577444122000867)
- [Iron Quadrangle - Mindat](https://www.mindat.org/loc-21133.html)

---

### 8.6 Parque Nacional da Serra do Gandarela

**GPS Coordinates:** ~20 deg 00'S, 43 deg 40'W (approximate center)
**Distance from BH center:** ~40-60 km southeast
**Area:** 312.7 km2 (31,270 hectares)

#### Location and Access
Created on October 13, 2014, the park spans eight municipalities: Nova Lima, Raposos, Caete, Santa Barbara, Mariana, Ouro Preto, Itabirito, and Rio Acima. Located at the heart of the Quadrilatero Ferrifero in the southern Espinhaco Range.

#### Mining Impact
- The park was created specifically to **protect Belo Horizonte's water sources from iron ore mining**
- During creation negotiations, compromises were made allowing some mining operations: Mundo Minerals (Rio Acima), Ferro Puro (Santa Barbara), MSOL (Itabirito), and Pedreira Um (Santa Barbara)
- Vale S.A. has sought approval to build iron ore mines adjacent to the park, creating ongoing tension between conservation and mining interests
- The park boundary was controversially drawn to exclude some mining concessions

#### Water Resources
- Contains critical aquifers that supply water to several cities including Belo Horizonte
- The ferruginous canga formations act as natural water filters and reservoirs
- Headwaters of important tributaries of the Rio das Velhas and Rio Doce basins
- Wetlands and veredas (palm swamps) within the park

#### Research/Analysis Opportunities with Drone Orthomaps
1. **Mining buffer zone monitoring:** Track mining activity encroachment at park boundaries
2. **Water resource mapping:** Map springs, streams, wetlands, and aquifer recharge zones
3. **Canga integrity assessment:** Monitor the condition of ferruginous canga formations that serve as natural aquifers
4. **Deforestation tracking:** Multi-temporal analysis of forest cover changes
5. **Tailings dam monitoring:** Document proximity and condition of mining tailings facilities near the park (post-Brumadinho awareness)
6. **Ecological corridor mapping:** Assess connectivity between the park and other protected areas in the Iron Quadrangle

#### Drone Flight Restrictions
- **Federal National Park:** ICMBio authorization mandatory via SISBIO system
- Located south/southeast of BH; generally outside major airport CTR zones
- Some municipalities (e.g., Nova Lima) may have local restrictions
- SARPAS authorization required

#### Environmental Issues for Monitoring
- Active mining operations at and near park boundaries
- Water quality threats from mining runoff
- Deforestation pressure from mining, eucalyptus plantations, and cattle ranching
- Risk of tailings dam failures in surrounding mining areas
- Fire management

Sources:
- [Serra do Gandarela National Park - Wikipedia](https://en.wikipedia.org/wiki/Serra_do_Gandarela_National_Park)
- [Vale mining near Serra do Gandarela - Mining Weekly](https://www.miningweekly.com/article/vale-seeks-go-ahead-to-build-iron-ore-mine-by-biodiversity-haven-2024-07-16)
- [Geoecological Profile of Serra do Gandarela](https://seer.ufu.br/index.php/sociedadenatureza/article/view/57012)

---

### 8.7 Serra do Curral

**GPS Coordinates:** ~19 deg 58'S, 43 deg 54'W (approximate, along the ridgeline)
**Distance from BH center:** ~5-10 km south (forms the southern "frame" of Belo Horizonte)
**Maximum Altitude:** 1,538 m (Pico Belo Horizonte)

#### Location and Access
The Serra do Curral is the mountain range that defines the southern boundary of Belo Horizonte, extending into Sabara and Nova Lima. It is the principal natural landmark of BH's landscape and is formally protected as cultural heritage (the city's skyline silhouette).

#### Urban/Nature Interface

**Cultural Significance:**
- Known since at least 1701 by bandeirantes exploring Minas Gerais
- The ridgeline silhouette is BH's iconic visual identity, protected as cultural heritage
- The city of Belo Horizonte was planned in the 1890s with the Serra as its backdrop

**Water Resources:**
- Harbors springs belonging to the Rio das Velhas and Paraopeba basins
- Supplies approximately 70% of BH's capital water and 40% of the metropolitan region's water

**Vegetation:**
- Atlantic Forest remnants
- Cerrado vegetation
- Ferruginous campos rupestres on iron-bearing canga
- Located just 150 m from Pico Belo Horizonte

**Mining Conflict:**
- Iron ore mining has occurred along the Serra since the 1960s
- Company Tamisa Mineracao S.A. has been attempting for 7+ years to install a mining complex in preserved Serra do Curral area in Nova Lima, at the border with BH and Sabara
- Licensed in 2022, the site would include three open pits, roads, tailings dams, and administrative buildings
- Mining company Gute Sicht has received over R$1.2 million in fines for environmental impacts but continues operations
- After 6 years of legal battles, courts authorized return of mining in 2024-2025
- BH city hall has promised intensified inspection

#### Research/Analysis Opportunities with Drone Orthomaps
1. **Mining encroachment monitoring:** Multi-temporal orthomaps to document mining expansion vs. conservation boundaries
2. **Urban sprawl analysis:** Map the urban-wildland interface and informal construction
3. **Cultural landscape documentation:** 3D model of the iconic ridgeline for heritage preservation
4. **Water catchment mapping:** Identify and monitor springs and headwater streams
5. **Vegetation health assessment:** Track impacts of mining dust, urban pollution on vegetation
6. **Legal evidence gathering:** High-resolution documentation for environmental litigation (mining permits vs. conservation)

#### Drone Flight Restrictions
- **Very close to urban BH:** Likely within Pampulha Airport CTR -- SARPAS mandatory
- Cultural heritage protection may impose additional restrictions
- Areas on the Nova Lima side may be slightly less restricted
- High visibility location: expect public attention to drone flights
- Active mining areas may have their own security restrictions

#### Environmental Issues
- The most contentious conservation vs. mining conflict in the BH region
- Active legal battles between municipal government, mining companies, and environmentalists
- Deforestation for mining directly threatens BH's water supply
- Air quality impacts from mining dust on adjacent urban areas
- This is an ideal location for drone-based environmental documentation for legal and advocacy purposes

Sources:
- [Serra do Curral Mining Conflict - CMIO](https://cmio.org/en/brazil/670852-belo-horizonte-takes-action-against-mining-in-serra-do-curral)
- [Mining in Serra do Curral Water Impact](https://newsbulletin247.com/opinion/94110.html)
- [Struggling over Serra do Curral - Academic Paper](https://epress.lib.uts.edu.au/journals/index.php/mcs/article/view/8296)
- [Projeto Manuelzao - Serra do Curral](https://manuelzao.ufmg.br/moldura-de-belo-horizonte-serra-do-curral-pode-perder-mais-terreno-para-a-mineracao/)

---

### 8.8 Lagoa Santa / Peter Lund Caves Region

**GPS Coordinates:** ~19 deg 38'S, 43 deg 53'W (Lagoa Santa city center)
**Distance from BH center:** ~30 km north
**Karst Area:** Extensive, covering much of the Lagoa Santa municipality and surroundings

#### Location and Access
Lagoa Santa is located approximately 30 km north of BH center. The karst region is developed in limestones of the Sete Lagoas Formation (Bambui Group), consisting of very pure calcarenites (CaCO3 >94%).

#### Archaeological Interest

**Peter Lund's Pioneering Work:**
- Danish naturalist Peter Wilhelm Lund investigated caves and rock shelters from 1833 to 1843
- Described numerous new genera and species of extinct megafauna
- At Sumidouro Cave, found human remains apparently associated with extinct megafauna -- one of the first such associations documented worldwide

**Key Archaeological Sites:**
- **Lapa Vermelha IV:** Discovery site of "Luzia," one of the oldest human skeletons in the Americas (11,000-11,500 years old)
- **Lapa do Santo:** Major archaeological site with early Holocene burials and rock art
- **Sumidouro Cave:** Lund's most important excavation site
- Over 1,000 documented caves in the region

**Karst Landscape Features:**
- Limestone cliffs and karst towers
- Karst lakes (including Lagoa Santa itself)
- Karst plains and dolines (sinkholes)
- Solution features visible from aerial perspective
- Subterranean drainage systems

#### Research/Analysis Opportunities with Drone Orthomaps
1. **Karst geomorphology mapping:** High-resolution terrain models of dolines, sinkholes, and karst features
2. **Cave entrance inventory:** Systematic aerial survey to locate and document cave openings
3. **Archaeological site documentation:** Orthomaps of rock shelter locations and their spatial relationships
4. **Urban expansion on karst:** Monitor construction on geologically unstable karst terrain (subsidence risk)
5. **Land use change analysis:** Track agricultural and urban encroachment on archaeologically sensitive areas
6. **Paleoenvironmental reconstruction:** Map relict landscape features for understanding past environments

#### Drone Flight Restrictions
- **CRITICAL AIRSPACE:** Located very close to Confins International Airport (SBCF) and Lagoa Santa Air Base (SBLS)
- This area is almost certainly within the TMA/CTR of SBCF
- SARPAS authorization is mandatory and may be difficult to obtain
- Flights may be restricted to very low altitudes or specific time windows
- This is the most airspace-restricted area among all ten locations in this list
- Consider: early morning flights when air traffic is lighter, or target areas on the western/southern edges of the karst farther from the airport

#### Environmental Issues
- Rapid urban expansion of Lagoa Santa and Vespasiano threatening karst features
- Limestone quarrying destroying caves and archaeological sites
- Groundwater contamination in the karst aquifer
- Construction-induced sinkhole formation
- Loss of cave fauna habitat

Sources:
- [Lagoa Santa Karst - Springer](https://link.springer.com/book/10.1007/978-3-030-35940-9)
- [SIGEP - Lagoa Santa Karst](http://sigep.cprm.gov.br/sitio015/sitio015english.htm)
- [Lapa do Santo - Wikipedia](https://en.wikipedia.org/wiki/Lapa_do_Santo)
- [Lagoa Santa Archaeological Province - Encyclopedia.com](https://www.encyclopedia.com/humanities/encyclopedias-almanacs-transcripts-and-maps/lagoa-santa)

---

### 8.9 Serra da Moeda

**GPS Coordinates:** ~20 deg 10'S, 43 deg 55'W (approximate)
**Distance from BH center:** ~40-50 km south/southwest
**Orientation:** Runs roughly north-south, forming the western boundary of the Quadrilatero Ferrifero

#### Location and Access
Serra da Moeda is a rocky ridge that defines municipal boundaries in the Iron Quadrangle region, serving as the western boundary of Itabirito municipality. It contains the Serra da Moeda syncline, a major geological structure in the western Iron Quadrangle.

#### Geological Features

**Rock Formations:**
- **Moeda Formation quartzites:** Detrital sedimentary rocks, with maximum deposition age of 2.62 Ga (billion years) based on U-Pb dating of zircon and xenotime
- **Caue Formation itabirites (banded iron formations):** Iron-rich layers alternating with silica-rich layers
- **Cenozoic deposits on highlands:** Sedimentary cover recording landscape evolution over millions of years
- The syncline structure creates a dramatic "trough" visible from aerial perspective

**Landscape Features:**
- Prominent escarpment with panoramic views
- Exposed geological cross-sections
- Waterfalls along the escarpment edge
- Mining scars visible from considerable distance
- Cenozoic weathering profiles on ancient Precambrian rocks

#### Research/Analysis Opportunities with Drone Orthomaps
1. **Geological structure mapping:** Orthomaps and 3D models of the syncline for structural geology studies
2. **Mining impact documentation:** Track open-pit expansion and landscape changes over time
3. **Escarpment erosion monitoring:** Document mass wasting and erosion on the steep Serra face
4. **Cenozoic deposit mapping:** Identify and map ancient weathering surfaces and deposits
5. **Vegetation vs. geology correlation:** Map how vegetation patterns follow geological substrates
6. **Geotourism route planning:** Create detailed 3D models for geological interpretation trails

#### Drone Flight Restrictions
- Not within a national or state park, but some areas may have municipal or environmental protection
- Located south/southwest of BH, generally outside major airport CTR
- Mining companies operating in the area may restrict access to their concessions
- SARPAS registration recommended; standard DECEA rules apply

#### Environmental Issues
- Active iron ore mining continues to modify the landscape
- Eucalyptus plantation expansion
- Road construction and urban expansion from Itabirito and Moeda municipalities
- Water quality concerns in streams draining mining areas
- Loss of geological heritage to mining activity

Sources:
- [Iron Quadrangle - Wikipedia](https://en.wikipedia.org/wiki/Iron_Quadrangle)
- [Cenozoic Deposits of Quadrilatero Ferrifero - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0341816220303635)
- [Geological and Mining Heritage of QF - ResearchGate](https://www.researchgate.net/publication/282559616_Geological_and_mining_heritage_of_iron_quadrangle_Minas_Gerais_-_Characterization_and_strategies_for_education_and_geotourism)

---

### 8.10 Quadrilatero Ferrifero (Iron Quadrangle) - Overview

**GPS Coordinates:** Roughly 19 deg 30'S to 20 deg 30'S, 43 deg 20'W to 44 deg 10'W
**Distance from BH center:** BH sits at the northern edge; the QF extends ~100 km south and ~80 km east-west
**Area:** ~7,000 km2

#### Overview
The Quadrilatero Ferrifero is Brazil's primary iron ore producing region, occupying a position among the world's leading mining areas. It is a geological province defined by a roughly quadrilateral arrangement of Precambrian mountain ranges surrounding a central lowland.

#### Mining Landscape Changes

**Historical Land Use Analysis (1985-2018 and projected to 2053):**
- Farming class decreased by 12%, with area converted to other uses
- Forest and mining patches increased by 4% and 0.2% respectively
- Forest fragments tend to disaggregate (become less connected)
- Mining areas tend to become more connected (consolidating)
- Mining accounted for 14% of vegetation loss since 1990
- Remaining vegetation loss caused by cattle pastures, eucalyptus plantations, and urbanization
- In 2010, only 20% of the region was under some form of conservation tenure
- Less than 0.05% of native vegetation was protected specifically for environmental compensation

**Key Mining Companies Operating:**
- Vale S.A. (largest)
- CSN Mineracao
- Usiminas
- Samarco (Mariana dam disaster, 2015)
- Numerous smaller operators

#### Research/Analysis Opportunities with Drone Orthomaps
1. **Multi-temporal landscape change:** Repeated orthomapping surveys to document mining expansion
2. **Tailings dam monitoring:** Regular surveys of dam structures, seepage, and vegetation on dam faces (critical post-Brumadinho/Mariana)
3. **Rehabilitation assessment:** Monitor mining site reclamation and vegetation reestablishment
4. **Acid mine drainage (AMD) mapping:** Identify AMD indicators in water bodies using RGB-derived indices
5. **Geological heritage documentation:** 3D models of significant geological outcrops before they are destroyed by mining
6. **Biodiversity corridor connectivity:** Assess fragmentation of natural vegetation between mining areas

#### Drone Flight Restrictions
- Varies by specific location within the QF
- Mining company concessions may restrict access (private property)
- Some areas within national/state parks require ICMBio/IEF authorization
- Generally outside major airport CTR zones (except northern portions near BH)
- SARPAS authorization recommended for all flights

#### Environmental Issues
- Ongoing large-scale iron ore extraction with landscape transformation
- Tailings dam safety (post-Mariana 2015 and Brumadinho 2019 disasters)
- Water contamination from mining runoff
- Loss of rare canga ecosystems
- Deforestation for mining and agriculture
- Mercury contamination in sediments from historical gold mining
- Geoconservation of Proterozoic geological heritage

Sources:
- [Mining Landscape Dynamics in QF - Journal of Hyperspectral Remote Sensing](https://periodicos.ufpe.br/revistas/index.php/jhrs/article/view/252158)
- [Mining, Deforestation, and Conservation in QF - Academia.edu](https://www.academia.edu/49630777/Mining_deforestation_and_conservation_opportunities_a_case_study_of_the_Quadril%C3%A1tero_Ferr%C3%ADfero_land_use_change_dynamics)
- [Geoconservation in QF - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2577444122000867)
- [Iron Quadrangle - Mindat](https://www.mindat.org/loc-21133.html)

---

### 8.11 Rio das Velhas Basin

**GPS Coordinates:** The basin extends from ~20 deg 15'S, 43 deg 30'W (headwaters near Ouro Preto) to ~17 deg 15'S, 44 deg 50'W (confluence with Sao Francisco River)
**Upper Course Area:** 1,943 km2 (the section most relevant for BH-based drone work)
**Distance from BH center:** The Rio das Velhas flows through/near BH; the upper basin is 0-60 km from BH center

#### Location and Access
The Rio das Velhas is a major tributary of the Sao Francisco River. Its upper course encompasses Belo Horizonte, Contagem, and Caete, making it the primary hydrological feature of the BH metropolitan region. The river supplies approximately 50% of the BH metropolitan population (~2 million inhabitants).

#### Water Quality Monitoring Potential

**Current Water Quality Issues:**
- Receives untreated or partially treated sewage from the BH metropolitan region
- The Arrudas and Onca streams (crossing BH) discharge heavily polluted water into the Rio das Velhas
- Yellow water coloration from iron in regional soils
- Extremely polluted and acidic in urban reaches
- Monitoring stations AV310 and AV320 identified as having the worst water quality in the entire network

**Existing Monitoring Infrastructure:**
- 65 surface water quality monitoring stations throughout the basin
- 16 water quality parameters sampled quarterly
- Data available from 2008 onward (at minimum)
- Managed by IGAM (Instituto Mineiro de Gestao das Aguas)

#### Research/Analysis Opportunities with Drone Orthomaps
1. **Riparian zone mapping:** Assess riparian vegetation health and coverage along river reaches
2. **Turbidity and algae mapping:** RGB-derived water indices to estimate turbidity, chlorophyll, and sediment load
3. **Sewage discharge points:** Identify and document informal sewage outfalls
4. **Erosion source identification:** Map erosion hotspots contributing sediment to the river
5. **Floodplain mapping:** High-resolution elevation models for flood risk assessment
6. **Restoration monitoring:** Track vegetation recovery in areas undergoing riparian restoration (Projeto Manuelzao and others)
7. **Mining runoff tracking:** Document sediment plumes from mining areas entering tributaries
8. **Informal settlement mapping:** Document informal construction in floodplains and riparian protection areas (APPs)

#### Drone Flight Restrictions
- Urban reaches near BH are likely within Pampulha Airport CTR
- Rural/upstream sections generally have fewer restrictions
- River corridors near highways and bridges may have additional considerations
- SARPAS authorization required for controlled airspace sections
- Areas near Confins Airport (northern basin) are heavily restricted

#### Environmental Issues
- Sewage pollution is the primary issue in urban reaches
- Mining runoff from the Quadrilatero Ferrifero affects upper basin tributaries
- Deforestation of riparian zones (violation of Brazil's Forest Code APPs)
- Urban flooding due to impermeabilization and channel modification
- Invasive aquatic species
- Historical mercury contamination from colonial gold mining
- Ongoing water treatment challenges for BH's water supply

Sources:
- [Rio das Velhas - Wikipedia](https://en.wikipedia.org/wiki/Rio_das_Velhas)
- [Water Quality Assessment Rio das Velhas - Springer](https://link.springer.com/article/10.1007/s10661-019-7281-y)
- [Natural Infrastructure in BH Water System - WRI Brasil (PDF)](https://www.wribrasil.org.br/sites/default/files/2023-08/Natural-infrastructure-BH-English.pdf)
- [Urbanization and Water Quality in Rio das Velhas - Academia.edu](https://www.academia.edu/15285477/The_Effects_of_Urbanization_on_Biodiversity_and_Water_Quality_In_the_Rio_Das_Velhas_Basin_Brazil)

---

### 8.12 Summary Comparison Table

| Location | Distance from BH | Airspace Risk | ICMBio/IEF Permit | Key Research Focus | Ease of Access |
|---|---|---|---|---|---|
| Serra do Cipo | 100 km NE | Low | Yes (National Park) | Biodiversity, campos rupestres | Moderate |
| Serra do Rola-Moca | 15-20 km S | Medium | Yes (State Park) | Canga vegetation, urban edge | Easy |
| Inhotim | 60 km W | Low | Private (institution) | Art+nature, Atlantic Forest | Easy |
| Serra da Piedade | 50 km E | Medium | Partial (monument) | Itabirite geology | Moderate |
| Serra do Gandarela | 40-60 km SE | Low | Yes (National Park) | Mining vs. water resources | Moderate |
| Serra do Curral | 5-10 km S | High | Varies | Mining conflict, heritage | Easy |
| Lagoa Santa Karst | 30 km N | Very High | Varies | Archaeology, karst | Difficult (airspace) |
| Serra da Moeda | 40-50 km SW | Low | No (mostly) | Geological structures | Easy |
| Quadrilatero Ferrifero | 0-100 km | Varies | Varies | Mining landscape changes | Varies |
| Rio das Velhas | 0-60 km | Varies | No (mostly) | Water quality, riparian | Varies |

### 8.13 Recommendations for DJI Mini 3 Orthomapping Priority

**Best for beginners / easiest access:**
1. **Serra da Moeda** -- Open areas, low airspace risk, dramatic geology, no park permit needed
2. **Inhotim surroundings** -- Low airspace risk, interesting landscape, private permission easier than government

**Best scientific value:**
1. **Serra do Cipo** -- Globally significant biodiversity, campos rupestres mapping
2. **Serra do Gandarela** -- Mining vs. conservation conflict, water resources
3. **Rio das Velhas Basin** -- Water quality monitoring, practical environmental applications

**Most urgent environmental monitoring:**
1. **Serra do Curral** -- Active mining conflict threatening BH's iconic landscape and water supply
2. **Quadrilatero Ferrifero** -- Tailings dam monitoring, post-disaster landscape assessment
3. **Lagoa Santa Karst** -- Rapid urban expansion destroying archaeological heritage

**DJI Mini 3 Advantages for These Sites:**
- At 248g, it falls below Brazil's 250g threshold for ANAC registration (recreational use)
- Small size and quiet operation reduces disturbance in conservation areas
- 4K camera adequate for orthomosaic generation at typical mapping altitudes
- 38-minute flight time allows coverage of ~10-15 hectares per battery at typical orthomapping settings (60-80m AGL, 70-80% overlap)
- True vertical shooting capability is excellent for nadir orthomapping captures
- **Limitation:** No RTK capability means lower absolute positional accuracy; use ground control points (GCPs) for precision work
