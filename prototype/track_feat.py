#!/usr/bin/env python3

import os
import argparse
import numpy as np
import cv2

DATA_FOLDER = os.path.join('..', 'data')
DEFAULT_VIDEO = 'pan.avi'
DETECTOR = cv2.xfeatures2d.SIFT_create()

def parse_args():
    parser = argparse.ArgumentParser(description='Match features of video frames.')
    parser.add_argument('file', nargs='?', type=str, help='Video file inside data folder that shall be processed.')
    parser.add_argument('--debug', action='store_true')

    args = parser.parse_args()
    if args.file is None:
        args.file = DEFAULT_VIDEO
    args.file = os.path.join(DATA_FOLDER, args.file)
    return args

def readVideo(file):
    video = cv2.VideoCapture(file)
    if not video.isOpened():
        print("Error: Could not open video '{}'.".format(file))
        return None
    frames = []
    while True:
        okay, frame = video.read()
        if not okay:
            break
        frames.append(frame)
    video.release()
    return frames

def main():
    args = parse_args()

    # Input
    frames = readVideo(args.file)
    if frames is None:
        exit(1)

    # Process
    for i in range(len(frames) - 1):
        frame_current = frames[i]
        frame_next = frames[i + 1]
        keypoints_current, descriptors_current = DETECTOR.detectAndCompute(frame_current, None)
        keypoints_next, descriptors_next = DETECTOR.detectAndCompute(frame_next, None)

        matcher = cv2.BFMatcher()
        all_matches = matcher.knnMatch(descriptors_current, descriptors_next, k = 2)

        good_matches = []
        for m, n in all_matches:
            # Only use match if it is significantly better than next best match.
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)

        pts_current = np.float32([ keypoints_current[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        pts_next = np.float32([ keypoints_next[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        # Debug viz
        if args.debug:
            def to_int_tuple(pt):
                return tuple(*np.int32(pt).tolist())
            for pt_current, pt_next in zip(pts_current, pts_next):
                pt_src, pt_dest = to_int_tuple(pt_current), to_int_tuple(pt_next)
                cv2.arrowedLine(frame_current, pt_src, pt_dest, (255, 120, 120))

        # Estimate homography
        homography, mask = cv2.findHomography(pts_next, pts_current, cv2.RANSAC)
        #homography[0, 2] = 0 # Stabilize only y axis.

        height, width, channels = frame_next.shape
        frame_next = cv2.warpPerspective(frame_next, homography, (width, height))
        frames[i + 1] = frame_next

    # Visualize
    cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
    i = 0
    while True:
        f = frames[i]
        cv2.imshow('frame', f)
        key = cv2.waitKey()
        if key == 27:
            break
        if key == 0x6a:
            # j
            i = (i + 1) % len(frames)
        if key == 0x6B:
            # k
            i = (i - 1) % len(frames)

    # Set down
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()