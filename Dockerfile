#FROM doduo1.umcn.nl/uokbaseimage/base:tf2.5-pt1.9
# Use the argument in the FROM instruction
FROM tensorflow/tensorflow:2.9.3-gpu

ENV DEBIAN_FRONTEND=noninteractive

# Install ASAP 2.1
RUN : \
    && apt-get update \
    && apt-get -y install curl \
    && curl --remote-name --location "https://github.com/computationalpathologygroup/ASAP/releases/download/ASAP-2.1-(Nightly)/ASAP-2.1-Ubuntu2004.deb" \
    && dpkg --install ASAP-2.1-Ubuntu2004.deb || true \
    && apt-get -f install --fix-missing --fix-broken --assume-yes \
    && ldconfig -v \
    && apt-get clean \
    && echo "/opt/ASAP/bin" > /usr/local/lib/python3.8/dist-packages/asap.pth \
    && rm ASAP-2.1-Ubuntu2004.deb \
    && :

RUN apt-get install git --assume-yes

ADD https://api.github.com/repos/DIAGNijmegen/pathology-whole-slide-data/git/refs/heads/main version.json
RUN  pip install git+https://github.com/DIAGNijmegen/pathology-whole-slide-data.git@main
ADD https://api.github.com/repos/DIAGNijmegen/pathology-hooknet/git/refs/heads/master version.json
RUN  pip install git+https://github.com/DIAGNijmegen/pathology-hooknet.git@master

COPY ./ /home/user/pathology-hooknet-tls/
RUN : \
    && echo "/home/user/pathology-hooknet-tls/" > /usr/local/lib/python3.8/dist-packages/hooknettls.pth \
    && pip install numpy==1.23.5 scipy==1.8.0 shapely==1.8.4 tqdm \ 
    && :

RUN mkdir -p /output/images/
RUN mkdir -p /home/user/tmp/
RUN mkdir -p /input/images

# WORKDIR /home/user
