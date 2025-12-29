# Data Collection for Volumetric Grasping Models
This repository provides added features from its original for ease of use for our labs data collection and testing purposes. Specifically dataset modularity for mass data collection and docker workflows.

## Installation

1. Create a conda environment.

2. Install packages list in [requirements.txt](requirements.txt).

3. Go to the root directory and install the project locally using `pip`

```
pip install -e .
```

4. Build ConvONets dependents by running `python convonet_setup.py build_ext --inplace`.

5. (Optional) You can install [graspnet-baseline](https://github.com/graspnet/graspnet-baseline) to speed up your data collection.

## Docker Setup
Pre-built image is hosted on Docker Hub:

```bash
docker pull johnbrann/grasp-data-collection
```

Contains:

- The ability to collect training data for various 6DoF grasping algorithms. 

## Requirements

- Docker and/or Docker Compose installed on a Linux machine
- Not tested outside of Linux, instructions are for Ubuntu but should work on any machine capable of running Docker

## Setup Instructions

### 1. Installing Docker & Compose on your machine

```bash
sudo apt update
sudo apt install docker.io docker-compose
```

### 2. Clone the repository

```bash
git clone https://github.com/JohnBrann/grasp-data-collection
cd grasp-data-collection
```

### 3. Start the container

```bash
docker-compose up -d
```

Then enter the container:

```bash
docker exec -it grasp-data-collection bash
```

#### 3.1 (Optional alternative: no docker compose)
If you do not wish to use docker compose but still don't want to build the image yourself:

<pre>
# Enable X11 access from Docker containers
xhost +local:docker

# Run the container
docker run -it --rm --gpus all \
  --net=host \
  -e DISPLAY=$DISPLAY \
  -v "/tmp/.X11-unix:/tmp/.X11-unix:rw" \
  -v "$HOME/vgn/data:/vgn/data:rw" \
  grasp-data-collection
</pre>

#### 3.2  (Optional alternative: local image build)
Lastly, if you wish to build the docker image yourself:

<pre>
# Build the image
docker build -t grasp-data-collection:latest .

# Enable X11 access from Docker containers
xhost +local:docker
  
# Run the container
docker run -it --rm --gpus all \
  --net=host \
  -e DISPLAY=$DISPLAY \
  -v "/tmp/.X11-unix:/tmp/.X11-unix:rw" \
  -v "$HOME/vgn/data:/vgn/data:rw" \
  grasp-data-collection
</pre>

## Object Datasets

This repository has been modified to work with the MOADv2 dataset. This dataset can be used and download at acces point [here] (https://github.com/pgavriel/MOADv2). After dowloaded the desired objects and creating the objects urdf files as stated in the linked repository, copy the entire folder into this repository into a folder named "object_sets". When generating data make sure to include the name of this folder as an argument i.e. --obeject-set <object-set name>

## Self-supervised Data Generation

### Raw synthetic grasping trials

You can run these scripts to generate data

```bash
python3 generate_data_giga.py --object-set <object_set>
```


```bash
python3 generate_data_contact.py --object-set <object_set>
```

Argument: 
- **Data collection mode**: (i) `giga` denotes the way to collect grasps in [GIGA](https://github.com/UT-Austin-RPL/GIGA), in which the grasp approaching vector is aligned with the surface normal. (ii) `graspnet` denotes using [graspnet-baseline](https://github.com/graspnet/graspnet-baseline) to collect grasps. (iii) `contact` denotes the way to collect grasps in EdgeGraspNet, ICGNet and OrbitGrasp, in which the contact normal is aligned with the surface normal.
- **Scene**: `pile` or `packed`.
- **Raw data path**
- **Number of Grasps**: it is only valid in `giga` and `graspnet` modes.
- **Random view**: `True` or `False`. it is only valid in `giga` and `graspnet` modes.

### Data clean and processing

First clean and balance the data using:

```bash
python scripts/clean_balance_data.py /path/to/raw/data
```

Then construct the dataset (add noise):

```bash
python scripts/construct_dataset_parallel.py --num-proc 40 --single-view --add-noise (dex | norm) /path/to/raw/data /path/to/new/data
```

### Save occupancy data

Sampling occupancy data on the fly can be very slow and block the training, so I sample and store the occupancy data in files beforehand:

```bash
python scripts/save_occ_data_parallel.py /path/to/raw/data 100000 2 --num-proc 40
```

Please run `python scripts/save_occ_data_parallel.py -h` to print all options.



