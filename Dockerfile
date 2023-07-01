FROM nvcr.io/nvidia/pytorch:21.07-py3

ENV TZ='Asia/Singapore' \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg libsndfile1

ARG APPDIR=/app
WORKDIR $APPDIR

ARG PIP_TRUSTED_HOST="--trusted-host pypi.org --trusted-host files.pythonhosted.org"

COPY ./requirements.txt ./
RUN pip install --verbose -r requirements.txt --no-cache-dir
RUN pip install -qq https://github.com/pyannote/pyannote-audio/archive/refs/heads/develop.zip

# copy application source
COPY . $APPDIR/

# Run the application:
ENTRYPOINT [ "/bin/sh" ]
