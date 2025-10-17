#!/bin/bash
set -e
xhost +local:docker

docker run -it --rm --gpus all \
  --net=host \
  -v "$HOME/grasp-data-collection:/grasp-data-collection:rw" \
  -v "/tmp/.X11-unix:/tmp/.X11-unix:rw" \
  -e DISPLAY="$DISPLAY" \
  --workdir /grasp-data-collection \
  grasp-data-collection-dev \
  bash -lc '
    source /opt/conda/etc/profile.d/conda.sh && conda activate grasp-data-collection
    export PYTHONPATH="/grasp-data-collection/src:$PYTHONPATH";
    python convonet_setup.py build_ext --inplace;
    exec bash
  '