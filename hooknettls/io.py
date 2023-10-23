
from dataclasses import dataclass
from pathlib import Path


class PathDoesNotExistsError(Exception):
    ...


@dataclass
class IOPaths:
    prediction_path: Path
    tls_heatmap_path: Path
    gc_heatmap_path: Path
    polygons_path: Path
    polygons_with_confidence_path: Path
    tls_filtered_path: Path
    gc_filtered_path: Path
    filtered_path: Path
    post_processed_path: Path


def get_io_paths(
    image_path: str,
    model_name: str,
    output_folder: Path,
) -> IOPaths:
    paths = {}

    image_name = Path(image_path).stem
    output_folder = Path(output_folder)
    paths["prediction_path"] = output_folder / (image_name + model_name + ".tif")
    paths["tls_heatmap_path"] = output_folder / (image_name + model_name + "_heat1.tif")
    paths["gc_heatmap_path"] = output_folder / (image_name + model_name + "_heat2.tif")

    for path in paths.values():
        if not path.exists():
            raise PathDoesNotExistsError(str(path))

    # Make dirs
    output_folder.mkdir(parents=True, exist_ok=True)

    raw_folder = output_folder / "raw"
    raw_folder.mkdir(parents=True, exist_ok=True)

    filtered_folder = output_folder / "filtered"
    filtered_folder.mkdir(parents=True, exist_ok=True)

    post_processed_folder = output_folder / "post-processed"
    post_processed_folder.mkdir(parents=True, exist_ok=True)

    paths["polygons_path"] = raw_folder / f"{image_name}_{model_name}.xml"
    paths["polygons_with_confidence_path"] = (
        raw_folder / f"{image_name}_{model_name}_with_confidence.json"
    )
    paths["tls_filtered_path"] = (
        filtered_folder / f"{image_name}_{model_name}_tls_filtered.json"
    )
    paths["gc_filtered_path"] = (
        filtered_folder / f"{image_name}_{model_name}_gc_filtered.json"
    )
    paths["filtered_path"] = filtered_folder / f"{image_name}_{model_name}_filtered.xml"
    paths["post_processed_path"] = (
        post_processed_folder / f"{image_name}_{model_name}_post_processed.xml"
    )

    return IOPaths(**paths)