"""Side-by-side and difference views of a rendered frame against the poster.

    python3 video/scripts/compare.py build/so/stills/frame-899.png [out_prefix]
"""
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
poster = cv2.imread(os.path.join(ROOT, "assets", "subjects-offered", "poster.png"))
frame = cv2.imread(sys.argv[1])
prefix = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(sys.argv[1])[0]
side = np.hstack([poster, frame])
cv2.imwrite(prefix + "-side.png", cv2.resize(side, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
diff = np.abs(poster.astype(int) - frame.astype(int)).max(2)
print("mean abs diff %.2f, pixels > 40: %.1f%%" % (diff.mean(), 100 * (diff > 40).mean()))
# Overlay: poster in red/blue, render in green, so misaligned edges show colour fringes.
pg = cv2.cvtColor(poster, cv2.COLOR_BGR2GRAY)
fg = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
cv2.imwrite(prefix + "-overlay.png", np.dstack([pg, fg, pg]))
