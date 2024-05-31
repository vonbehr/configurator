import psapi
import numpy as np
import cv2

document_color_mode = psapi.enum.ColorMode.rgb
width = 4000
height = 2250
file = psapi.LayeredFile_8bit(document_color_mode, width, height)

# CV2 reads images in packed BGR order by default, we now need to go from packed to planar
# e.g. from BGR BGR BGR BGR -> RRRR BBBB GGGG
image = cv2.imread("C:/Users/florianbehr/Desktop/configurator/The_Scope_Polaroid_Team_Florian.jpg")

transformed_image = np.zeros((image.shape[2], image.shape[0], image.shape[1]), np.uint8)
transformed_image[0] = image[:, :, 2]   # Use numpy slicing to get the third channel of bgr
transformed_image[1] = image[:, :, 1]
transformed_image[2] = image[:, :, 0]

img_lr = psapi.ImageLayer_8bit(
        transformed_image,
        layer_name="layer 001",
        width=width,
        height=height,
        color_mode=document_color_mode)

group_layer = psapi.GroupLayer_8bit(
        layer_name="Groupie",
        width=width,
        height=height,
        color_mode=document_color_mode)

# add layer to group
group_layer.add_layer(file, img_lr)

# Add to the file and write out
file.add_layer(group_layer)
file.write("C:/Users/florianbehr/Desktop/configurator/Out_grp.psd")
