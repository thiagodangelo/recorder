# Multi Input and Output Video Recorder

This is an OpenCV-based command-line tool for recording videos from multiple sources simultaneously.

## Features

- [ ] TODO

## Installing dependencies

- pip3 install opencv-python

## Usage example

1. Default behavior - It records video from /dev/video0 and saves it to an "avi" file:
    - python3 recorder.py --record --view

2. Custom behavior through command-line options - In this example, it records videos from multiple cameras and saves them to different "avi" files in the Desktop folder:
    - python3 recorder.py --sources 0 1 --filenames dev_video_0.avi dev_video_1.avi --fps 30 --output ~/Desktop/ --resize_factor 0.5 --record --view
