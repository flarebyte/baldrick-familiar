#!/bin/bash

mkdir -p temp/github
python script/snapshotter.py 
python script/copy_by_filename.py
cp -r temp/github/learning temp/data/learning
cp -r temp/github/baldrick-reserve/data temp/data/baldrick-reserve-data
cp -r temp/github/baldrick-reserve/template temp/data/baldrick-reserve-template