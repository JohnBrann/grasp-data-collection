#!/bin/bash
set -e
xhost +local:docker

docker run -it --rm --gpus all \
  --net=host \
  -v "$HOME/grasp-data-collection:/grasp-data-collection_2:rw" \
  -v "/tmp/.X11-unix:/tmp/.X11-unix:rw" \
  -e DISPLAY="$DISPLAY" \
  --workdir /grasp-data-collection \
  grasp-data-collection \
  bash -lc '
    python convonet_setup.py build_ext --inplace;
    exec bash
  '

 # -v "$HOME/grasp-data-collection/object_sets:/grasp-data-collection/object_sets:rw" \