import win32gui
import win32ui
from ctypes import windll
from PIL import Image
import numpy as np
import skimage.transform as T
import skimage.color as C
import skimage.measure as M
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from scipy.ndimage import label, center_of_mass
from sklearn.cluster import DBSCAN
import replay_utils as RU
import cv2


def getBars(im, colours, res):
    lower_black, upper_black = np.array([7, 7, 7]), np.array([21, 21, 21])
    im_binary = cv2.inRange(im,lower_black, upper_black)
    im_rgb = applyColourMask(im, colours)
    labeled_binary = M.label(im_binary, connectivity=1)

    # Initialize an empty list to store the percentage HP for each health bar
    health_percentages = []

    # Iterate over each labeled region
    for region in M.regionprops(labeled_binary):
        # Get the coordinates of the bounding box
        min_row, min_col, max_row, max_col = region.bbox
        
        # Extract the corresponding region from the RGB image
        health_bar_region = im_rgb[min_row+1:max_row-1, min_col+1:max_col-1]
        
        # Calculate the percentage HP
        total_pixels = np.prod(health_bar_region.shape[:2])
        value_pixels = np.sum(health_bar_region.sum(axis=-1) > 0)  # Counting non-zero pixels
        percentage_hp = (value_pixels / total_pixels) * 100
        if percentage_hp > 0:
            # Append the percentage HP to the list
            health_percentages.append(percentage_hp)

    # Print the percentage HP for each health bar
    return np.array(health_percentages), len(health_percentages)

def getScreenshot(window):
    hwnd = win32gui.FindWindow(None, 'League of Legends (TM) Client')

    # Uncomment the following line if you use a high DPI display or >100% scaling size
    # windll.user32.SetProcessDPIAware()

    # Change the line below depending on whether you want the whole window
    # or just the client area. 
    #left, top, right, bot = win32gui.GetClientRect(hwnd)
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    w = right - left
    h = bot - top

    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)

    saveDC.SelectObject(saveBitMap)

    # Change the line below depending on whether you want the whole window
    # or just the client area. 
    #result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 1)
    result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
    print(result)

    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)

    im = Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1)

    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)

    if result == 1:
        #PrintWindow Succeeded
        return im
    else:
        return 0

def resizeImage(im, reduce_factor = 2):
    out_im = T.resize(im, (im.shape[0]//reduce_factor, im.shape[1]//reduce_factor), anti_aliasing=True)
    return np.array(out_im*255, dtype=np.uint8)
def applyMonoMask(im, colour_idx = 0, mask_limit = 200):
    out_im = im.copy()
    out_im[out_im[:,:,colour_idx] < mask_limit] = 0
    return out_im
def applyColourMask(im, colours):
    out_im = np.zeros_like(im)
    for colour in colours:
        mask = np.all(im == colour, axis=-1)
        out_im[mask] = im[mask]
    return out_im

def findBars(im):
    # Assuming 'image' is your binary image with shape (M, N)
    # Let's create a sample binary image with white horizontal bars (for demonstration purposes)
    im = im.copy()
    im = C.rgb2gray(im)
    im[im > 0.1] = 1
    # Label connected components
    labeled_image, num_features = label(im)

    # Find the center of mass (centroid) for each labeled cluster
    centroids = center_of_mass(im, labeled_image, range(1, num_features + 1))

    # Display the image and mark the centroids
    fig, ax = plt.subplots()
    ax.imshow(im, cmap='gray')

    for centroid in centroids:
        ax.plot(centroid[1], centroid[0], 'ro')  # Note: plot expects (x, y) coordinates

    plt.show()

    # Print the centroids coordinates
    print("Centroids of clusters (y, x):", centroids)

def findClusters2(im):
    im = im.copy()
    im = C.rgb2gray(im)
    im[im > 0.1] = 1

    # Parameters
    M = 30  # Maximum distance between bars to be considered in the same cluster

    # Find coordinates of white pixels
    white_pixel_coords = np.column_stack(np.where(im == 1))

    # Apply DBSCAN to cluster white pixels
    db = DBSCAN(eps=M, min_samples=1, metric='euclidean').fit(white_pixel_coords)
    labels = db.labels_

    # Find centroids of clusters
    centroids = []
    for label in np.unique(labels):
        cluster_coords = white_pixel_coords[labels == label]
        centroid = cluster_coords.mean(axis=0)
        centroids.append(centroid)

    centroids = np.array(centroids)

    # Display the image and mark the centroids
    fig, ax = plt.subplots()
    ax.imshow(im, cmap='gray')

    for centroid in centroids:
        ax.plot(centroid[1], centroid[0], 'ro')  # Note: plot expects (x, y) coordinates

    # plt.show()

    # Print the centroids coordinates
    print("Centroids of clusters (y, x):", centroids)
    return centroids

def findClusters(im, size = (70,70), n_steps = 8):
    im = im.copy()
    im = C.rgb2gray(im)
    toplane_coords = [(400, 485),
                      (240, 320),
                      (230, 210),
                      (410, 41)]
    mid_coords = [(480, 500),
                  (480, 60)]
    
    botlane_coords = [(560, 485),
                      (730, 320),
                      (720, 210),
                      (550, 41)]
    full_coords = [toplane_coords, mid_coords, botlane_coords]
    max_coords = []
    rects = []
    half_m_size = int(size[0]/2)
    half_n_size = int(size[1]/2)
    for coords in full_coords:
        values = []
        for i in range(len(coords)-1):
            ms = np.array(np.linspace(coords[i][1], coords[i+1][1],n_steps), dtype=np.int32)
            ns = np.array(np.linspace(coords[i][0], coords[i+1][0],n_steps), dtype=np.int32)
            values_i = []
            for j in range(min(len(ms),len(ns))):
                values_i.append(im[ms[j]-half_m_size:ms[j]+half_m_size, ns[j]-half_n_size:ns[j]+half_n_size].sum())
            values.append(values_i)
        max_values = list(map(max,values))
        max_i = np.argmax(max_values)
        ms = np.linspace(coords[max_i][1], coords[max_i+1][1],n_steps)
        ns = np.linspace(coords[max_i][0], coords[max_i+1][0],n_steps)
        max_values_val = values[max_i]
        max_values_i = np.argmax(max_values_val)
        max_coords.append((ms[max_values_i], ns[max_values_i]))
        rects.append(patches.Rectangle((ns[max_values_i]-half_n_size, ms[max_values_i]-half_m_size), size[0], size[1], linewidth=1, edgecolor='r', facecolor='none'))
    plt.close()
    fig, ax = plt.subplots()
    ax.imshow(im, cmap='gray')
    for rect in rects:
        ax.add_patch(rect)
    plt.show()
    return max_coords
        
# getScreenshot('League of Legends (TM) Client').save('screenshot.png')