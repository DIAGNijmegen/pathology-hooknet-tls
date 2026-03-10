
# HookNet-TLS

HookNet-TLS is a deep learning algorithm designed to accurately detect Tertiary Lymphoid Structures and Germinal Centers (GC) within whole-slide pathology images. Building on the foundation of the HookNet architecture, HookNet-TLS is a useful tool for pathologists and researchers examining  TLSs and GCs.


## Quick Start 


### Installation

❗ this algorithm requires openslide==3.4.1

Ensure you have Docker installed and running on your system. 

- Clone this repository
- Download the weights [here](https://zenodo.org/records/10614942) and put them in the repository folder.
- Build the Docker image

E.g.,

```bash
git clone https://github.com/DIAGNijmegen/pathology-hooknet-tls.git
cd hooknet-tls
wget https://zenodo.org/records/10614942/files/weights.h5
docker build -t hooknet-tls .
```


## Preprocessing

Before running HookNet-TLS, your whole-slide image must be converted to a dense pyramid TIF and a tissue-background mask must be created. A dedicated Docker image is provided for this in the `preprocessing/` folder.

### Build

```bash
docker build -t preprocessing preprocessing/
```

### Usage

```bash
docker run --rm \
  -v /path/to/input:/input \
  -v /path/to/output:/output \
  preprocessing \
  /input/<slide>.svs \
  /output/<slide>.tif \
  /output/<slide>_mask.tif
```

This runs two steps in sequence:
1. **Convert WSI** — extracts the image at level 1 from the SVS and saves it as a tiled pyramid TIF using ASAP (`saveatlevel.py`)
2. **Create mask** — computes a tissue-background mask via Otsu thresholding + morphological cleanup and saves it as a pyramid TIF (`createmask.py`)

The resulting `<slide>.tif` and `<slide>_mask.tif` are the inputs expected by the HookNet-TLS algorithm.


## Usage


<blockquote style="color: #8a6d3b; background-color: #fcf8e3; border-left: 2px solid #faebcc;">
  <p><strong>Note.</strong> The algorithm expects that the input whole-slide-image contains the spacing corresponding to approximately 0.5µm and 2.0µm.</p>
</blockquote>

```bash
docker run -it -v /output/:/output/ hooknet-tls /bin/bash
```

```bash
python3 -m hooknettls \
    hooknettls.default.image_path=/tmp/TCGA-21-5784-01Z-00-DX1.tif \
    hooknettls.default.mask_path=/tmp/TCGA-21-5784-01Z-00-DX1_tb_mask.tif
```


### Related packages 
HookNet-TLS uses the following packages

- [WholeSlideData](https://github.com/DIAGNijmegen/pathology-whole-slide-data)
- [HookNet](https://github.com/DIAGNijmegen/pathology-hooknet)

### Data
- HookNet-TLS Weights: https://zenodo.org/records/10614942
- HookNet-TLS Annotations: https://zenodo.org/records/10614928
- HookNet-TLS Annotations Masks: https://zenodo.org/records/10635034



## Support 

If you are having issues, please let us know or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE.md)


---
