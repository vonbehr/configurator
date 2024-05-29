import psapi
import numpy as np
import cv2

color_mode = psapi.enum.ColorMode.rgb
width = 4000
height = 2250
file = psapi.LayeredFile_8bit(color_mode, width, height)
print(type(file))

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
        color_mode=color_mode)

# Add to the file and write out
# file.add_layer(img_lr)
# file.write("C:/Users/florianbehr/Desktop/configurator/Out.psd")


def convert_exr(self, image_file: str, extension: str) -> str:
    """
    Convert exr files to another format

    Args:
        image_file (str): image file + path to convert
        extension (str): extension of the converted file

    Returns:
        string: filepath of the converted image
    """

    # We assume image_file is an exr in linear colorspace.
    path, filename = os.path.split(image_file)
    file, ext = os.path.splitext(filename)
    converted_file = self.output_dir + "/images/" + file + "." + extension

    # read image
    inbuffer = ImageBuf(image_file)

    # copy only RGB
    outbuffer = ImageBuf()
    ImageBufAlgo.channels(outbuffer, inbuffer, ("R", "G", "B"))

    # convert from linear to sRGB
    dst = ImageBufAlgo.colorconvert(outbuffer, "ACES - ACEScg", "out_srgb")

    # write image in 8 Bit
    dst.write(converted_file, "uint8")

    return converted_file

def load_image(filepath: str) -> np.ndarray:
    '''
    Read an image from the filepath and return it in the correct format for PhotoshopAPI.

    Args:
        filepath (str): PAth to the file

    Returns:
        np.ndarray: ndarray in the correct format for PhotoshopAPI
    '''
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

def create_ps(width: int, height: int, color_mode: str, bitdepth: int):
    '''
    Create a layered Photoshop file object

    Args:
        width (int): Width in pixel
        height (int): Height in pixel
        color_mode (str): Colormode, usually RGB or CMYK e.g. psapi.enum.ColorMode.rgb
        bitdepth (int): color depth, can be 8, 16 or 32

    Returns:
        psapi.LayeredFile_Nbit: layered Photoshop file object
    '''

    if bitdepth is 8:
        ps_document = psapi.LayeredFile_8bit(color_mode, width, height)
    elif bitdepth is 16:
        ps_document = psapi.LayeredFile_16bit(color_mode, width, height)
    elif bitdepth is 32:
        ps_document = psapi.LayeredFile_32bit(color_mode, width, height)

    return ps_document

def create_layer(width: int, height: int, color_mode: str, bitdepth: int, name: str):

    # Construct our layer instance, width and height must be specified for this to work!

    if bitdepth is 8:
        layer = psapi.ImageLayer_8bit(transformed_image, layer_name=name, width=width, height=height, color_mode=color_mode)
    elif bitdepth is 16:
        layer = psapi.ImageLayer_16bit(transformed_image, layer_name=name, width=width, height=height, color_mode=color_mode)
    elif bitdepth is 32:
        layer = psapi.ImageLayer_32bit(transformed_image, layer_name=name, width=width, height=height, color_mode=color_mode)

    return layer

def create_layer_group(name):
    pass
    # create a ps layer group
    return layer_group

def add_layer_to_group(layer, group):
    pass
    # add a ps layer to a layer group

def add_layer_to_document(layer, ps_document):
    file.add_layer(ps_document)

def save_ps(ps_document, filepath):
    pass
    # save a ps file to disc
    ps_document.write(filepath)

