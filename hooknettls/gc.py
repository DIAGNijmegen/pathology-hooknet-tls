import json
from functools import partial
from pathlib import Path

from wholeslidedata.annotation.wholeslideannotation import WholeSlideAnnotation
from wholeslidedata.image.wholeslideimage import WholeSlideImage
from wholeslidedata.interoperability.asap.imagewriter import write_mask


def px_to_mm(px: int, spacing: float):
    return px * spacing / 1000

def save_to_gc_outputs(image_path, post_processed_path):
    wsi = WholeSlideImage(image_path, backend='asap')
    wsa = WholeSlideAnnotation(post_processed_path)
    write_mask(wsi, wsa, wsi.spacings[2], output_folder=Path('/output/images/tls-gc/'), suffix='_hooknet_tls.tif')

    convert_points = partial(px_to_mm, spacing=wsi.spacings[0])

    json_data = {
        "name": "HookNet-TLS",
        "type": "Multiple polygons",
        "polygons": [],
        "version": { "major": 1, "minor": 0 }
    }
    for idx, annotation in enumerate(wsa.annotations):
        coords = list(annotation.geometry.exterior.coords)
        path_points =  [list(map(convert_points, sublist)) + [0.5009999871253967] for sublist in coords]
        item = {
            "name": f"Annotation {idx}",
            "seed_point": path_points[0],
            "path_points": path_points,
            "sub_type": "brush",
            "groups": [annotation.label.name],
            "probability": 1.0,

        }
        json_data['polygons'].append(item)

    # Writing JSON data
    with open('/output/tls-gc-polygons.json', 'w') as outfile:
        json.dump(json_data, outfile, indent=4)


# {
#     "name": "Areas of interest",
#     "type": "Multiple polygons",
#     "polygons": [
#         {
#             "name": "Area 1",
#             "seed_point": [ 55.82666793823242, 90.46666717529297, 0.5009999871253967 ],
#             "path_points": [
#                 [ 55.82667599387105, 90.46666717529297, 0.5009999871253967 ],
#                 [ 55.93921357544119, 90.88666314747366, 0.5009999871253967 ],
#                 [ 56.246671966051736, 91.1941215380842, 0.5009999871253967 ],
#                 [ 56.66666793823242, 91.30665911965434, 0.5009999871253967 ]
#             ],
#             "sub_type": "brush",
#             "groups": [ "manual"],
#             "probability": 0.67
#         },
#         {
#             "name": "Area 2",
#             "seed_point": [ 90.22666564941406, 96.06666564941406, 0.5009999871253967 ],
#             "path_points": [
#                 [ 90.22667370505269, 96.06666564941406, 0.5009999871253967 ],
#                 [ 90.33921128662283, 96.48666162159475, 0.5009999871253967 ],
#                 [ 90.64666967723338, 96.7941200122053, 0.5009999871253967 ]
#             ],
#             "sub_type": "brush",
#             "groups": [],
#             "probability": 0.92
#         }
#     ],
#     "version": { "major": 1, "minor": 0 }