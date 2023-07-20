import cv2
import numpy as np


def crop(img, pts):
    mask = np.zeros(img.shape[0:2], dtype=np.uint8)
    cv2.drawContours(mask, [pts], -1, (255, 255, 255), -1, cv2.LINE_AA)
    res = cv2.bitwise_and(img, img, mask = mask)
    rect = cv2.boundingRect(pts)
    cropped = res[rect[1]: rect[1] + rect[3], rect[0]: rect[0] + rect[2]]
    return cropped

def order_points(pts):
    rect = np.zeros((4, 2), dtype = "float32")
    s = pts.sum(axis = 1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis = 1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def rotate(img, pts):
	rect = order_points(pts)
	(tl, tr, br, bl) = rect
	widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
	widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
	maxWidth = max(int(widthA), int(widthB))
	heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
	heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
	maxHeight = max(int(heightA), int(heightB))
	dst = np.array([
		[0, 0],
		[maxWidth - 1, 0],
		[maxWidth - 1, maxHeight - 1],
		[0, maxHeight - 1]], dtype = "float32")
	M = cv2.getPerspectiveTransform(rect, dst)
	warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
	return warped
    
def quantization(img, clusters=8, rounds=1):
    h, w = img.shape[:2]
    samples = np.zeros([h*w, 3], dtype=np.float32)
    count = 0
    for x in range(h):
        for y in range(w):
            samples[count] = img[x][y]
            count += 1
    compactness, labels, centers = cv2.kmeans(
        samples,
        clusters,
        None,
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10000, 0.0001),
        rounds,
        cv2.KMEANS_PP_CENTERS
    )
    centers = np.uint8(centers)
    res = centers[labels.flatten()]
    return res.reshape((img.shape))


def warning():
    print(f'[WARNING]: Exceeding the level')

def check(img, cnts, cnt_idx):
    cnt = cnts[cnt_idx]['contour']
    bnds = cnts[cnt_idx]['bounds']
    wrns = cnts[cnt_idx]['warnings']

    rotated = rotate(img, cnt)
    # cells = cell_split(rotated, rows, cols)

    _mean_val = rotated.mean()
    _std_val = 0
    _median_val = 0

    mean_val = (_mean_val - bnds['mean'][0]) / (bnds['mean'][1] - bnds['mean'][0])
    std_val = 0
    median_val = 0

    is_warning = mean_val >= wrns['mean'] and \
        std_val >= wrns['std'] and \
        median_val >= wrns['median']
    if is_warning:
        warning()

    cnts[cnt_idx]['result'] = {
        'is_warning': is_warning,
        'values': {
            'mean': mean_val,
            'std': std_val,
            'median': median_val,
        }
    }