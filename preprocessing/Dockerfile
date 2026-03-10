FROM --platform=linux/amd64 ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies first
RUN apt-get update && apt-get -y install curl python3 python3-pip

# Download ASAP
RUN curl -L -o /tmp/ASAP.deb "https://github.com/computationalpathologygroup/ASAP/releases/download/ASAP-2.1-%28Nightly%29/ASAP-2.1-Ubuntu2004.deb"

# Install ASAP and fix dependencies
RUN dpkg --install /tmp/ASAP.deb || true \
    && apt-get -f install --fix-missing --fix-broken --assume-yes \
    && ldconfig \
    && rm /tmp/ASAP.deb

# Verify ASAP installed
RUN ls -la /opt/ASAP/bin/

# Add ASAP Python bindings to path
ENV PYTHONPATH=/opt/ASAP/bin

# Install Python dependencies
RUN pip3 install numpy scikit-image

# Copy scripts
COPY saveatlevel.py /opt/saveatlevel.py
COPY createmask.py /opt/createmask.py
COPY run.sh /opt/run.sh
RUN chmod +x /opt/run.sh

WORKDIR /opt

ENTRYPOINT ["/opt/run.sh"]
