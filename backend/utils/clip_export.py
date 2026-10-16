"""Project-scoped raster clipping and format conversion."""

import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.mask import mask


def clip_raster_aoi(source_path, target_path, projected_geometry):
    with rasterio.open(source_path) as src:
        pixels, transform = mask(src, [projected_geometry], crop=True, filled=False)
        valid = ~np.ma.getmaskarray(pixels[0])
        if not valid.any():
            raise ValueError('Area sem pixels validos para recorte')
        profile = src.profile.copy()
        profile.update(driver='GTiff', width=pixels.shape[2], height=pixels.shape[1],
                       transform=transform, compress='lzw')
        with rasterio.open(target_path, 'w', **profile) as dst:
            dst.write(pixels.filled(src.nodata if src.nodata is not None else 0))
            dst.write_mask(valid.astype('uint8') * 255)
        return {'width': int(pixels.shape[2]), 'height': int(pixels.shape[1]),
                'valid_pixels': int(valid.sum()), 'bands': int(src.count)}


def _run(command):
    result = subprocess.run(command, capture_output=True, text=True, timeout=600)
    if result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or 'Falha ao converter arquivo')


def export_dataset(source, fmt, crs, destination):
    source = Path(source)
    destination = Path(destination)
    vector = source.suffix.lower() in {'.geojson', '.json', '.gpkg', '.shp', '.kml'}
    if vector:
        if fmt not in {'geojson', 'kml', 'shapefile'}:
            raise ValueError('Formato incompativel com camada vetorial')
        if fmt in {'geojson', 'kml'} and crs != 'EPSG:4326':
            raise ValueError('GeoJSON e KML devem usar EPSG:4326')
        driver = {'geojson': 'GeoJSON', 'kml': 'KML', 'shapefile': 'ESRI Shapefile'}[fmt]
        if fmt == 'shapefile':
            folder = destination.parent / 'shapefile'
            folder.mkdir()
            shape_path = folder / 'camada.shp'
            _run(['ogr2ogr', '-f', driver, '-t_srs', crs, str(shape_path), str(source)])
            with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
                for part in folder.iterdir():
                    archive.write(part, part.name)
            shutil.rmtree(folder)
        else:
            _run(['ogr2ogr', '-f', driver, '-t_srs', crs, str(destination), str(source)])
    else:
        if fmt not in {'geotiff', 'png', 'jpeg'}:
            raise ValueError('Formato incompativel com camada raster')
        with rasterio.open(source) as ds:
            if ds.crs is None:
                raise ValueError('Raster sem CRS')
            if fmt in {'png', 'jpeg'} and (ds.count not in {1, 3} or ds.dtypes[0] != 'uint8'):
                raise ValueError('PNG/JPEG requer raster de 8 bits com 1 ou 3 bandas; use GeoTIFF')
        if fmt == 'geotiff':
            _run(['gdalwarp', '-q', '-of', 'GTiff', '-t_srs', crs, '-co', 'COMPRESS=LZW',
                  str(source), str(destination)])
        else:
            intermediate = destination.parent / 'reprojected.tif'
            _run(['gdalwarp', '-q', '-of', 'GTiff', '-t_srs', crs, str(source), str(intermediate)])
            _run(['gdal_translate', '-q', '-of', 'PNG' if fmt == 'png' else 'JPEG',
                  str(intermediate), str(destination)])
            intermediate.unlink()
    if not destination.is_file() or destination.stat().st_size == 0:
        raise ValueError('Arquivo de exportacao vazio')
    return destination
