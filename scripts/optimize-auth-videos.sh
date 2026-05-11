#!/bin/sh
set -eu

optimize_video() {
  input="$1"
  output="${input%.mp4}.optimized.mp4"

  if [ ! -f "$input" ]; then
    echo "Skipping missing video: $input"
    return
  fi

  echo "Optimizing $input"
  ffmpeg -hide_banner -loglevel error -y \
    -i "$input" \
    -vf "scale='if(gt(a,1),-2,480)':'if(gt(a,1),480,-2)',fps=20" \
    -an \
    -c:v libx264 \
    -profile:v main \
    -pix_fmt yuv420p \
    -preset veryfast \
    -crf 34 \
    -movflags +faststart \
    "$output"
  mv "$output" "$input"
}

optimize_video public/video/login-visual.mp4
optimize_video public/video/register-visual.mp4
optimize_video public/video/fp_v3.mp4
