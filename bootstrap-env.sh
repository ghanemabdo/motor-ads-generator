#!/bin/bash
wget https://repo.continuum.io/archive/Anaconda3-5.0.1-MacOSX-x86_64.sh
bash Anaconda3-5.0.1-MacOSX-x86_64.sh
conda create -n qmotor python=3.6
source activate qmotor
pip install Pillow json requests lxml shutil unicodedata datetime python-bidi
pip install git+https://github.com/mpcabd/python-arabic-reshaper
