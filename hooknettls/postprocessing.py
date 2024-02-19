import cv2
import numpy as np
from scipy.ndimage.morphology import binary_dilation, binary_erosion, binary_fill_holes
from shapely.geometry import MultiPolygon
from shapely.geometry import Polygon as ShapelyPolygon
from shapely.geometry import box
from shapely.strtree import STRtree
from wholeslidedata.annotation.labels import Label
from wholeslidedata.annotation.types import Annotation
from wholeslidedata.annotation.utils import (
    convert_annotations_to_json,
    write_json_annotations,
)
from wholeslidedata.annotation.wholeslideannotation import WholeSlideAnnotation
from wholeslidedata.image.wholeslideimage import WholeSlideImage
from wholeslidedata.interoperability.asap.annotationwriter import write_asap_annotation


### core functions

def cv2_polygonize(
    mask,
    spacing,
    dilation_iterations=0,
    erose_iterations=0,
    fill_holes=False,
    values=None,
    offset=(0, 0),
):

    downsampling = mask.get_downsampling_from_spacing(spacing)
    mask = mask.get_slide(spacing)

    if values is None:
        values = np.unique(mask)

    all_polygons = {}

    for value in values:
        tmp_mask = np.copy(mask).squeeze()
        tmp_mask[tmp_mask != value] = 0
        tmp_mask[tmp_mask == value] = 1

        if dilation_iterations > 0:
            tmp_mask = binary_dilation(tmp_mask, iterations=dilation_iterations).astype(
                np.uint8
            )

        if fill_holes:
            tmp_mask = binary_fill_holes(tmp_mask).astype(np.uint8)

        if erose_iterations > 0:
            tmp_mask = binary_erosion(tmp_mask, iterations=erose_iterations).astype(
                np.uint8
            )

        tmp_mask = np.pad(
            array=tmp_mask, pad_width=1, mode="constant", constant_values=0
        )

        polygons, _ = cv2.findContours(
            tmp_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE, offset=(-1, -1)
        )

        polygons = [
            (np.array(polygon[:, 0, :] * downsampling)) + np.array(offset)
            for polygon in polygons
            if len(polygon) >= 3
        ]
        all_polygons[value] = polygons
    return all_polygons


def convert_polygons_to_annotations(polygons):
    inv_label_map = {2: "tls", 3: "gc"}
    color_map = {"tls": "purple", "gc": "yellow"}
    annotations = []
    index = 0
    for key, polys in polygons.items():
        for polygon in polys:
            p = ShapelyPolygon(polygon).buffer(0)
            label = Label(
                name=inv_label_map[key], value=key, color=color_map[inv_label_map[key]]
            )

            if isinstance(p, MultiPolygon):
                polygons = list(p.geoms)
            else:
                polygons = [p]

            for q in polygons:
                if len(q.exterior.coords) >= 3:
                    try:
                        annotation = Annotation.create(
                            index=index,
                            label=label.todict(),
                            coordinates=q.exterior.coords,
                        )
                    except Exception as e:
                        print(q.exterior.coords)
                        raise e

                    annotations.append(annotation)
                    index += 1


    return annotations



def filter_tls_annotations(
    tls_annotations, tls_confidence, tls_confidence_area, scale=1.0, multiplier=1
):
    filtered_tls_annotations = []
    for tls_annotation in tls_annotations:
        pixels = sum(
            [
                v
                for k, v in tls_annotation.label.confidence_map.items()
                if int(float(k) * multiplier) >= tls_confidence
            ]
        )
        if pixels * scale >= tls_confidence_area * tls_confidence_area:
            filtered_tls_annotations.append(tls_annotation)
    return filtered_tls_annotations


def in_tls(tls_tree, gc_geom: ShapelyPolygon):
    tls_annotations: list[ShapelyPolygon] = tls_tree.query(gc_geom)
    for tls_annotation in tls_annotations:
        tls_box = box(*tls_annotation.bounds)
        if (gc_geom.intersection(tls_box).area / gc_geom.area) >= 0.5:
            return True
    return False

def filter_gc_annotations(
    tls_annotations,
    gc_annotations,
    gc_confidence,
    gc_confidence_area,
    scale=1.0,
    multiplier=1,
):
    filtered_gc_annotations = []
    tls_tree = STRtree([annotation.geometry for annotation in tls_annotations])
    for gc_annotation in gc_annotations:
        if not in_tls(tls_tree, gc_annotation.geometry):
            continue
        pixels = sum(
            [
                v
                for k, v in gc_annotation.label.confidence_map.items()
                if int(float(k) * multiplier) >= gc_confidence
            ]
        )
        if pixels * scale >= gc_confidence_area * gc_confidence_area:
            filtered_gc_annotations.append(gc_annotation)
    return filtered_gc_annotations



# public functions

def convert_to_annotations(prediction_mask_path, spacing):
    # load mask
    prediction_mask = WholeSlideImage(prediction_mask_path, backend="asap")

    # convert mask to annotations -> tls and gc
    polygons = cv2_polygonize(
        prediction_mask,
        spacing=spacing,
        dilation_iterations=1,
        erose_iterations=1,
        fill_holes=True,
        values=[2, 3],
    )
    return convert_polygons_to_annotations(polygons)


def insert_confidence_map(
    raw_prediction_annotation_path,
    tls_heatmap_path,
    gc_heatmap_path,
    spacing,
):
    wsa_tls = WholeSlideAnnotation(raw_prediction_annotation_path, labels=["tls"])
    wsa_gc = WholeSlideAnnotation(raw_prediction_annotation_path, labels=["gc"])
    tls_heat_mask = WholeSlideImage(tls_heatmap_path, backend="asap")
    gc_heat_mask = WholeSlideImage(gc_heatmap_path, backend="asap")

    tls_annotations = wsa_tls.annotations
    gc_annotations = wsa_gc.annotations

    json_data = []
    for tls_annotation in tls_annotations:
        tls_json = tls_annotation.todict()
        tls_heat_values = tls_heat_mask.get_region_from_annotations([tls_annotation], spacing=spacing)
        tls_json["label"]["confidence_map"] = {
            int(key): int(value)
            for key, value in dict(
                zip(*np.unique(tls_heat_values, return_counts=True))
            ).items()
        }
        json_data.append(tls_json)

    for gc_annotation in gc_annotations:
        gc_json = gc_annotation.todict()
        gc_heat_values = gc_heat_mask.get_region_from_annotations([gc_annotation], spacing=spacing)
        gc_json["label"]["confidence_map"] = {
            int(key): int(value)
            for key, value in dict(
                zip(*np.unique(gc_heat_values, return_counts=True))
            ).items()
        }
        json_data.append(gc_json)

    return json_data


def tls_filtering(input_path, output_path, filter_settings):
    wsa_tls = WholeSlideAnnotation(input_path, labels=["tls"])
    filtered_tls_annotations = filter_tls_annotations(
        wsa_tls.annotations,
        filter_settings["confidence_value"],
        filter_settings["confidence_count"],
    )
    json_annotations = convert_annotations_to_json(filtered_tls_annotations)
    print(f"writing json file: {output_path}")
    write_json_annotations(output_path, json_annotations)


def gc_filtering(input_path, tls_input_path, output_path, filter_settings):
    wsa_gc = WholeSlideAnnotation(input_path, labels=["gc"])
    wsa_tls = WholeSlideAnnotation(tls_input_path, labels=["tls"])
    filtered_tls_annotations = filter_gc_annotations(
        wsa_tls.annotations,
        wsa_gc.annotations,
        filter_settings["confidence_value"],
        filter_settings["confidence_count"],
    )
    json_annotations = convert_annotations_to_json(filtered_tls_annotations)
    print(f"writing json file: {output_path}")
    write_json_annotations(output_path, json_annotations)


def combine_annotations(json1, json2, output_path):
    combined_annotatations = []
    combined_annotatations.extend(WholeSlideAnnotation(json1).annotations)
    combined_annotatations.extend(WholeSlideAnnotation(json2).annotations)
    write_asap_annotation(combined_annotatations, output_path=output_path)

