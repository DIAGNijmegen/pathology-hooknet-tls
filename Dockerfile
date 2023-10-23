FROM nvidia/cuda:11.1.1-cudnn8-runtime-ubuntu20.04

ENV TZ=Europe/Amsterdam
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone


# Install python3.8
RUN : \
    && apt-get update \
    && apt-get install -y --no-install-recommends software-properties-common \
    && add-apt-repository -y ppa:deadsnakes \
    && apt-get install -y --no-install-recommends python3.8-venv \
    && apt-get install libpython3.8-dev -y \
    && apt-get clean \
    && :

# Add env to PATH
RUN python3.8 -m venv /venv
ENV PATH=/venv/bin:$PATH

# Install ASAP
RUN : \
    && apt-get update \
    && apt-get -y install curl \
    && curl --remote-name --location "https://github.com/computationalpathologygroup/ASAP/releases/download/ASAP-2.1-(Nightly)/ASAP-2.1-Ubuntu2004.deb" \
    && dpkg --install ASAP-2.1-Ubuntu2004.deb || true \
    && apt-get -f install --fix-missing --fix-broken --assume-yes \
    && ldconfig -v \
    && apt-get clean \
    && echo "/opt/ASAP/bin" > /venv/lib/python3.8/site-packages/asap.pth \
    && rm ASAP-2.1-Ubuntu2004.deb \
    && :

# Install git
RUN apt-get install -y --no-install-recommends git

# # Install algorithm
COPY ./ /home/user/pathology-hooknet-tls/
RUN : \
    && pip install wheel==0.37.0 \
    && pip install /home/user/pathology-hooknet-tls \
    && rm -r /home/user/pathology-hooknet-tls \
    && :

# Make user
RUN groupadd -r user && useradd -r -g user user
RUN chown user /home/user/
RUN mkdir /output/
RUN chown user /output/
USER user
WORKDIR /home/user

ENTRYPOINT ["python"]
CMD ["-mhooknettls"]