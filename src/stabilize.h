#pragma once

#include <vector>

// OpenCV
#include "opencv2/calib3d.hpp"
#include "opencv2/features2d.hpp"
#include "opencv2/xfeatures2d.hpp"

#include "video.h"

template<typename T>
std::vector<cv::Mat> stabilize(Video& frames, const bool debug) {
  const auto eye = cv::Mat::eye(3, 3, CV_64F);
  std::vector<cv::Mat> tfs(frames.size(), eye);
  cv::Ptr<T> detector = T::create();

  for (size_t i = 0; i < frames.size() - 1; i++) {
    auto& frame_current = frames[i];
    auto& frame_next = frames[i + 1];

    // Apply detector.
    std::vector<cv::KeyPoint> keypoints_current, keypoints_next;
    cv::Mat descriptors_current, descriptors_next;
    detector->detectAndCompute(frame_current, cv::Mat(), keypoints_current, descriptors_current);
    detector->detectAndCompute(frame_next, cv::Mat(), keypoints_next, descriptors_next);

    // Find keypoint matches.
    cv::FlannBasedMatcher matcher;
    std::vector<std::vector<cv::DMatch>> matches_all;
    matcher.knnMatch(descriptors_current, descriptors_next, matches_all, 2);

    // Filter matches.
    std::vector<cv::DMatch> matches_good;
    for (const auto& neighbours : matches_all) {
      if (neighbours[0].distance < 0.75 * neighbours[1].distance) {
        matches_good.push_back(neighbours[0]);
      }
    }

    // Extract corresponding keypoints.
    std::vector<cv::Point2f> pts_current, pts_next;
    for (const auto& match : matches_good) {
      pts_current.push_back(keypoints_current[match.queryIdx].pt);
      pts_next.push_back(keypoints_next[match.trainIdx].pt);
    }

    // Debug visualize correspondencies.
    if (debug) {
      for (size_t j = 0; j < pts_current.size(); j++) {
        cv::arrowedLine(frame_current, static_cast<cv::Point2i>(pts_current[j]), static_cast<cv::Point2i>(pts_next[j]), cv::Scalar(255, 120, 120));
      }
    }

    // Estimate transformation.
    auto& tf_next = tfs[i + 1];
    tf_next = cv::findHomography(pts_next, pts_current, cv::RANSAC);
    tf_next = tfs[i] * tf_next; // Accumulate transforms.
  }
}

std::vector<cv::Point2f> extract_centers(Video& frames, std::vector<cv::Mat> transforms, const bool debug);
