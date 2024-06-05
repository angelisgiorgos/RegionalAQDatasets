#!/bin/bash

# Print a message that downloads are starting
echo "...Starting downloads..."

# wget https://zenodo.org/records/11220965/files/athens.csv
# wget https://zenodo.org/records/11220965/files/ancona.csv
# wget https://zenodo.org/records/11220965/files/zaragoza.csv


# wget https://zenodo.org/records/11220965/files/spatiotemporal.zip


# # Create the folder 'data'
# mkdir -p data

# # Move the downloaded files into the 'data' folder
# mv athens.csv data/
# mv ancona.csv data/
# mv zaragoza.csv data/

# mv spatiotemporal.zip data/
unzip data/spatiotemporal.zip -d data/

rm -rf data/spatiotemporal.zip

# Print a message indicating the downloads and move are complete
echo "Downloads complete. Files have been moved to the 'data' folder."