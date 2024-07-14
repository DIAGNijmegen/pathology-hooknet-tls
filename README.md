
# HookNet-TLS

HookNet-TLS is a deep learning algorithm designed to accurately detect Tertiary Lymphoid Structures and Germinal Centers (GC) within whole-slide pathology images. Building on the foundation of the HookNet architecture, HookNet-TLS is a useful tool for pathologists and researchers examining  TLSs and GCs.


## Quick Start 


### Installation

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

### Usage



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
