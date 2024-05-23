import psapi
import numpy as np
import cv2

document_color_mode = psapi.enum.ColorMode.rgb
width = 4000
height = 2250
file = psapi.LayeredFile_8bit(document_color_mode, width, height)

# CV2 reads images in packed BGR order by default, we now need to go from packed to planar
# e.g. from BGR BGR BGR BGR -> RRRR BBBB GGGG
image = cv2.imread("C:/Users/florianbehr/Desktop/configurator/white_BrilliantWhiteMetallic.png", cv2.IMREAD_UNCHANGED)

print(type(image))

transformed_image = np.zeros((image.shape[2], image.shape[0], image.shape[1]), np.uint8)
transformed_image[0] = image[:, :, 2]   # Use numpy slicing to get the third channel of bgr
transformed_image[1] = image[:, :, 1]
transformed_image[2] = image[:, :, 0]
transformed_image[3] = image[:, :, 3]

print(type(transformed_image))

# Construct our layer instance, width and height must be specified for this to work!
img_lr = psapi.ImageLayer_8bit(
        transformed_image,
        layer_name="layer 001",
        width=width,
        height=height,
        color_mode=document_color_mode)

# Add to the file and write out
# file.add_layer(img_lr)
# file.write("C:/Users/florianbehr/Desktop/configurator/Out.psd")

def load_image(filepath: str) -> np.ndarray:
    # read image with alpha channel
    image = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)

    # CV2 reads images in packed BGR order by default, we now need to go from packed to planar
    # e.g. from BGR BGR BGR BGR -> RRRR BBBB GGGG
    transformed_image = np.zeros((image.shape[2], image.shape[0], image.shape[1]), np.uint8)
    transformed_image[0] = image[:, :, 2]   # Use numpy slicing to get the third channel of bgr
    transformed_image[1] = image[:, :, 1]
    transformed_image[2] = image[:, :, 0]
    transformed_image[3] = image[:, :, 3]

    return transformed_image

def create_ps(width, height, document_color_mode, bitdepth):
    pass
    # create ps document

    return ps_document

def create_layer(width, height, document_Color_mode, name):
    pass
    # create a ps layer
    return layer

def create_layer_group(name):
    pass
    # create a ps layer group
    return layer_group

def add_layer_to_group(layer, group):
    pass
    # add a ps layer to a layer group

def save_ps(ps_document, filepath):
    pass
    # save a ps file to disc
    ps_document.write(filepath)

