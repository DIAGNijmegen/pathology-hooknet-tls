
# HookNet-TLS


A cutting-edge deep learning solution for detecting Tertiary Lymphoid Structures and Germinal Centers in whole-slide images.



---

## About HookNet-TLS

HookNet-TLS is a deep learning algorithm designed to accurately detect Tertiary Lymphoid Structures (TLS) and Germinal Centers within whole-slide pathology images. Building on the foundation of the HookNet architecture, HookNet-TLS is a useful tool for pathologists and researchers examining Tertiary Lymphoid Structures (TLS) and Germinal Centers


## Quick Start 


### Installation

Ensure you have Docker installed and running on your system. Clone this repository and build the Docker image:

```bash
git clone https://github.com/DIAGNijmegen/pathology-hooknet-tls.git
cd hooknet-tls
docker build -t hooknet-tls .
```

### Usage

<blockquote style="color: #8a6d3b; background-color: #fcf8e3; border-left: 2px solid #faebcc;">
  <p><strong>Note.</strong> The algorithm expects that the input whole-slide-image contains the spacing corresponding to approximately 0.5µm and 2.0µm.</p>
</blockquote>

```bash
python3 -m hooknettls \
    hooknettls.default.image_path=/tmp/TCGA-21-5784-01Z-00-DX1.tif \
    hooknettls.default.mask_path=/tmp/TCGA-21-5784-01Z-00-DX1_tb_mask.tif
```

### Related packages 
HookNet-TLS uses the following packages

- [WholeSlideData](wholeslidedata-link)
- [HookNet](hooknet-link)


## Support 

If you are having issues, please let us know or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE.md)


---
