ARG APPDIR=/app
FROM nvcr.io/nvidia/pytorch:22.07-py3 as base

ENV TZ='Asia/Singapore' \
    DEBIAN_FRONTEND=noninteractive
ARG APPDIR
WORKDIR $APPDIR

# ------------
# build image
FROM base as build

ARG APPDIR

ARG PIP_TRUSTED_HOST="--trusted-host pypi.org --trusted-host files.pythonhosted.org"
ARG PYPI_INTERNET_INDEX_URL=https://pypi.org/simple
ARG PYPI_TORCH_INDEX_URL=https://download.pytorch.org/whl/torch_stable.html

# To avoid Nvidia GPG error
# RUN rm /etc/apt/sources.list.d/cuda.list
# RUN rm /etc/apt/sources.list.d/nvidia-ml.list

RUN apt-get -y update
RUN apt-get -y install git sox libsndfile1 ffmpeg

# copy application source
COPY . $APPDIR/
RUN pip install --verbose -r requirements.txt
RUN python -m pip install git+https://github.com/NVIDIA/NeMo.git@v1.11.0#egg=nemo_toolkit[asr]
RUN pip install torch torchvision torchaudio -f https://download.pytorch.org/whl/cu113

# Run the application:
ENTRYPOINT [ "/bin/sh" ]