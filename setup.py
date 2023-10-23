from setuptools import setup, find_packages

setup(
    name="hooknettls",
    version="0.0.1",
    author="Mart van Rijthoven",
    author_email="mart.vanrijthoven@gmail.com",
    packages=find_packages(),
    license="LICENSE.txt",
    
    install_requires = [
        'wholeslidedata @ git+https://github.com/DIAGNijmegen/pathology-whole-slide-data@main',
        'hooknet @ git+https://github.com/DIAGNijmegen/pathology-hooknet@master'
    ]


)