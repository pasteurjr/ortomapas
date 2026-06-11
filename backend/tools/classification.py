"""
Land-cover classification tools for ortomapas.

Provides supervised classification using scikit-learn (Random Forest, SVM),
model persistence via joblib, and accuracy assessment (confusion matrix, kappa).
"""

import logging
import os
import tempfile
from typing import Optional

import joblib
import numpy as np
import rasterio
from rasterio.mask import mask as rasterio_mask
from scipy.ndimage import generic_filter
from shapely import wkt as shapely_wkt
from shapely.geometry import mapping as shapely_mapping
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    classification_report,
)
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC

logger = logging.getLogger(__name__)

CLASS_NAMES = [
    "vegetacao_densa",
    "vegetacao_rasteira",
    "solo_exposto",
    "agua",
    "urbano",
    "agricola",
    "rocha",
]


# ---------------------------------------------------------------------------
# Feature extraction helpers
# ---------------------------------------------------------------------------

def _extract_features_from_bands(R: np.ndarray, G: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    Build a feature array from R, G, B arrays of the same shape.

    Features per pixel: R, G, B, VARI, TGI, ExG  (6 features).

    Parameters
    ----------
    R, G, B : ndarray
        1-D or 2-D arrays with the same shape.

    Returns
    -------
    ndarray of shape (n_pixels, 6)
    """
    R = R.astype(np.float64).ravel()
    G = G.astype(np.float64).ravel()
    B = B.astype(np.float64).ravel()

    eps = 1e-10
    denom_vari = G + R - B
    denom_vari[np.abs(denom_vari) < eps] = eps
    vari = (G - R) / denom_vari

    tgi = G - 0.39 * R - 0.61 * B
    exg = 2.0 * G - R - B

    features = np.column_stack([R, G, B, vari, tgi, exg])
    features[~np.isfinite(features)] = 0.0
    return features


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_classifier(
    ortomapa_path: str,
    training_samples: list[dict],
    algorithm: str = "random_forest",
    output_model_path: Optional[str] = None,
) -> dict:
    """
    Train a supervised classifier from labelled geometry samples.

    Parameters
    ----------
    ortomapa_path : str
        Path to the RGB ortomapa raster.
    training_samples : list[dict]
        Each element: {"class_name": str, "geometry_wkt": str}.
        class_name must be one of CLASS_NAMES.
    algorithm : str
        "random_forest" or "svm".
    output_model_path : str, optional
        Where to save the trained model (joblib). If None, a temp file is used.

    Returns
    -------
    dict
        model_path, accuracy, kappa, classification_report, classes.
    """
    if algorithm not in ("random_forest", "svm"):
        raise ValueError(f"Unsupported algorithm: {algorithm}. Use 'random_forest' or 'svm'.")

    # Build class label mapping
    class_to_idx = {name: idx for idx, name in enumerate(CLASS_NAMES)}

    X_all = []
    y_all = []

    with rasterio.open(ortomapa_path) as src:
        for sample in training_samples:
            class_name = sample["class_name"]
            geom_wkt = sample["geometry_wkt"]

            if class_name not in class_to_idx:
                logger.warning("Unknown class '%s', skipping sample.", class_name)
                continue

            label = class_to_idx[class_name]
            geom = shapely_wkt.loads(geom_wkt)
            geojson_geom = shapely_mapping(geom)

            try:
                out_image, out_transform = rasterio_mask(
                    src, [geojson_geom], crop=True, nodata=0
                )
            except Exception as exc:
                logger.warning("Could not extract sample for class '%s': %s", class_name, exc)
                continue

            R = out_image[0]
            G = out_image[1]
            B = out_image[2]

            # Mask out nodata pixels (all bands zero)
            valid = (R != 0) | (G != 0) | (B != 0)
            if not np.any(valid):
                continue

            features = _extract_features_from_bands(
                R[valid], G[valid], B[valid]
            )
            labels = np.full(features.shape[0], label, dtype=np.int32)

            X_all.append(features)
            y_all.append(labels)

    if not X_all:
        raise ValueError("No valid training samples could be extracted.")

    X = np.vstack(X_all)
    y = np.concatenate(y_all)

    logger.info(
        "Training data: %d pixels, %d classes present.",
        X.shape[0],
        len(np.unique(y)),
    )

    # Train/test split for accuracy evaluation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    if algorithm == "random_forest":
        clf = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            n_jobs=-1,
            random_state=42,
        )
    else:
        clf = SVC(kernel="rbf", C=10.0, gamma="scale", random_state=42)

    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = float(accuracy_score(y_test, y_pred))
    kappa = float(cohen_kappa_score(y_test, y_pred))

    present_classes = sorted(set(y_test) | set(y_pred))
    target_names = [CLASS_NAMES[i] for i in present_classes]
    report = classification_report(
        y_test, y_pred, labels=present_classes, target_names=target_names, output_dict=True
    )

    # Save model
    if output_model_path is None:
        fd, output_model_path = tempfile.mkstemp(suffix=".joblib")
        os.close(fd)

    joblib.dump({"classifier": clf, "class_names": CLASS_NAMES, "algorithm": algorithm}, output_model_path)

    result = {
        "model_path": output_model_path,
        "accuracy": round(acc, 4),
        "kappa": round(kappa, 4),
        "classification_report": report,
        "classes": CLASS_NAMES,
        "n_training_pixels": int(X_train.shape[0]),
        "n_test_pixels": int(X_test.shape[0]),
    }

    logger.info("Classifier trained: accuracy=%.4f, kappa=%.4f", acc, kappa)
    return result


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_raster(
    ortomapa_path: str,
    model_path: str,
    output_path: str,
) -> str:
    """
    Classify all pixels in an ortomapa using a trained model.

    Applies a 3x3 majority filter to smooth the result.

    Parameters
    ----------
    ortomapa_path : str
        Path to the RGB ortomapa.
    model_path : str
        Path to the joblib model file.
    output_path : str
        Destination for the classified GeoTIFF.

    Returns
    -------
    str
        output_path on success.
    """
    model_data = joblib.load(model_path)
    clf = model_data["classifier"]

    with rasterio.open(ortomapa_path) as src:
        R = src.read(1)
        G = src.read(2)
        B = src.read(3)
        profile = src.profile.copy()
        height, width = R.shape

    features = _extract_features_from_bands(R, G, B)
    predictions = clf.predict(features).astype(np.int16)
    classified = predictions.reshape(height, width)

    # 3x3 majority filter
    def _majority(values):
        values = values.astype(np.int16)
        counts = np.bincount(values, minlength=len(CLASS_NAMES))
        return np.argmax(counts)

    classified_smooth = generic_filter(
        classified.astype(np.float64),
        function=_majority,
        size=3,
        mode="reflect",
    ).astype(np.int16)

    profile.update(
        dtype=rasterio.int16,
        count=1,
        compress="lzw",
        nodata=-1,
    )

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(classified_smooth, 1)

    logger.info("Classified raster written to %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# Accuracy assessment
# ---------------------------------------------------------------------------

def accuracy_assessment(
    classified_path: str,
    reference_samples: list[dict],
) -> dict:
    """
    Assess classification accuracy against reference samples.

    Parameters
    ----------
    classified_path : str
        Path to the classified GeoTIFF.
    reference_samples : list[dict]
        Each element: {"class_name": str, "geometry_wkt": str}.

    Returns
    -------
    dict
        overall_accuracy, kappa, confusion_matrix, per_class_accuracy.
    """
    class_to_idx = {name: idx for idx, name in enumerate(CLASS_NAMES)}
    y_true = []
    y_pred = []

    with rasterio.open(classified_path) as src:
        for sample in reference_samples:
            class_name = sample["class_name"]
            geom_wkt = sample["geometry_wkt"]

            if class_name not in class_to_idx:
                continue

            label = class_to_idx[class_name]
            geom = shapely_wkt.loads(geom_wkt)
            geojson_geom = shapely_mapping(geom)

            try:
                out_image, _ = rasterio_mask(src, [geojson_geom], crop=True, nodata=-1)
            except Exception:
                continue

            classified_pixels = out_image[0]
            valid = classified_pixels != -1
            if not np.any(valid):
                continue

            pred_values = classified_pixels[valid].ravel()
            true_values = np.full_like(pred_values, label)

            y_true.extend(true_values.tolist())
            y_pred.extend(pred_values.tolist())

    if not y_true:
        raise ValueError("No valid reference samples could be extracted.")

    y_true = np.array(y_true, dtype=np.int32)
    y_pred = np.array(y_pred, dtype=np.int32)

    overall_acc = float(accuracy_score(y_true, y_pred))
    kappa = float(cohen_kappa_score(y_true, y_pred))

    present_classes = sorted(set(y_true) | set(y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=present_classes)

    per_class = {}
    for i, cls_idx in enumerate(present_classes):
        cls_name = CLASS_NAMES[cls_idx] if cls_idx < len(CLASS_NAMES) else f"class_{cls_idx}"
        row_total = cm[i].sum()
        correct = cm[i, i]
        per_class[cls_name] = {
            "accuracy": round(float(correct / row_total), 4) if row_total > 0 else 0.0,
            "total_samples": int(row_total),
            "correct": int(correct),
        }

    result = {
        "overall_accuracy": round(overall_acc, 4),
        "kappa": round(kappa, 4),
        "confusion_matrix": cm.tolist(),
        "confusion_matrix_labels": [
            CLASS_NAMES[i] if i < len(CLASS_NAMES) else f"class_{i}"
            for i in present_classes
        ],
        "per_class_accuracy": per_class,
    }

    logger.info("Accuracy assessment: OA=%.4f, Kappa=%.4f", overall_acc, kappa)
    return result
