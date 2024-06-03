from matplotlib.mlab import psd
import psapi
import numpy as np
import cv2
import os
from OpenImageIO import ImageBuf, ImageBufAlgo



def convert_exr(image_file: str) -> str:
    """
    Convert exr files to png

    Args:
        image_file (str): image file + path to convert

    Returns:
        string: filepath of the converted image
    """

    # We assume image_file is an exr in ACEScg colorspace.
    path, filename = os.path.split(image_file)
    file, ext = os.path.splitext(filename)
    converted_file = path + "/" + file + ".png"

    # read image
    inbuffer = ImageBuf(image_file)

    # copy only RGB
    outbuffer = ImageBuf()
    ImageBufAlgo.channels(outbuffer, inbuffer, ("R", "G", "B", "A"))

    # convert from ACEScg to sRGB
    dst = ImageBufAlgo.colorconvert(outbuffer, "ACES - ACEScg", "out_srgb")

    # write image in 8 Bit
    dst.write(converted_file, "uint8")

    return converted_file

def get_images_from_folder(path: str, extension: str) -> list:
    '''
    Parse a dir and all subfolders and add all files with the specified extension to a list.

    Args:
        path (str): Start path for parsing
        extension (str): Extension of files to add to list

    Returns:
        list: List of filepaths
    '''

    files_found = []

    for dirpath, subdirs, files in os.walk(path):
        for i in files:
            if i.endswith("." + extension):
                files_found.append(os.path.join(dirpath, i))

    return files_found

def load_image(filepath: str) -> np.ndarray:
    '''
    Read an image from the filepath and return it in the correct format for PhotoshopAPI.

    Args:
        filepath (str): Path to the file

    Returns:
        np.ndarray: ndarray in the correct format for PhotoshopAPI
    '''
    # read image with alpha channel, returns np.array
    image = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)

    # CV2 reads images in packed BGR order by default, we now need to go from packed to planar
    # e.g. from BGR BGR BGR BGR -> RRRR BBBB GGGG
    transformed_image = np.zeros((image.shape[2], image.shape[0], image.shape[1]), np.uint8)
    transformed_image[0] = image[:, :, 2]   # Use numpy slicing to get the third channel of bgr
    transformed_image[1] = image[:, :, 1]
    transformed_image[2] = image[:, :, 0]
    transformed_image[3] = image[:, :, 3]

    return transformed_image

def export_layers(filepath: str, out_path: str):
    '''
    Parse Phgotoshop file for image layers and call function to write them to disc.

    Args:
        filepath (str): Filepath to Photoshop file
        out_path (str): Output path
    '''

    # read PS document
    ps_document = psapi.LayeredFile.read(filepath)

    # iterate over top level layers in PS file
    for layer in ps_document.layers:

        # if layer is group layer, look for image layers beneath it
        if isinstance(layer, psapi.GroupLayer_8bit):
            for sub_layer in layer.layers:
                if isinstance(sub_layer, psapi.ImageLayer_8bit):
                    write_layer(sub_layer, out_path)

        # if layer is image layer
        elif isinstance(layer, psapi.ImageLayer_8bit):
            write_layer(layer, out_path)

def write_layer(layer: psapi.ImageLayer_8bit, out_path: str):
    '''
    Write a given Photoshop layer to disc.

    Args:
        layer (psapi.ImageLayer_8bit): Photoshop layer object
        out_path (str): Path where image is written
    '''
    # get name of layer for filename
    name = layer.name

    # shuffle dict to get the right order for cv2
    R = layer.image_data[0]
    G = layer.image_data[1]
    B = layer.image_data[2]
    A = layer.image_data[-1]

    # pack array for right order
    packed_array = np.dstack((B, G, R, A))

    cv2.imwrite(out_path + "/" + name + ".png", packed_array)


def create_ps_file(width: int, height: int, color_mode: str, bitdepth: int):
    '''
    Create a layered Photoshop file object

    Args:
        width (int): Width in pixel
        height (int): Height in pixel
        color_mode (str): Colormode, usually RGB or CMYK e.g. psapi.enum.ColorMode.rgb
        bitdepth (int): color depth, can be 8, 16 or 32

    Returns:
        psapi.LayeredFile_*N*bit: layered Photoshop file object
    '''

    if bitdepth is 8:
        ps_document = psapi.LayeredFile_8bit(color_mode, width, height)
    elif bitdepth is 16:
        ps_document = psapi.LayeredFile_16bit(color_mode, width, height)
    elif bitdepth is 32:
        ps_document = psapi.LayeredFile_32bit(color_mode, width, height)

    return ps_document

def read_ps_file(filepath):

    ps_document = psapi.LayeredFile.read(filepath)


    width = ps_document.width
    height = ps_document.height
    bit_depth: psapi.enum.BitDepth = psapi.PhotoshopFile.find_bitdepth(filepath)

    return ps_document, bit_depth

def create_layer(image, width: int, height: int, color_mode: str, bitdepth: int, name: str):
    '''
    Create a Photoshop layer object.

    Args:
        image (np.ndarray): Image object
        width (int): image width
        height (int): image height
        color_mode (str): Colormode, usually RGB or CMYK e.g. psapi.enum.ColorMode.rgb
        bitdepth (int): color depth, can be 8, 16 or 32
        name (str): layer name

    Returns:
        psapi.Layer_*N*bit: layer object
    '''

    # Construct our layer instance, width and height must be specified for this to work!
    if bitdepth is 8:
        layer = psapi.ImageLayer_8bit(image, layer_name=name, width=width, height=height, color_mode=color_mode)
    elif bitdepth is 16:
        layer = psapi.ImageLayer_16bit(image, layer_name=name, width=width, height=height, color_mode=color_mode)
    elif bitdepth is 32:
        layer = psapi.ImageLayer_32bit(image, layer_name=name, width=width, height=height, color_mode=color_mode)

    return layer

def create_group_layer(width: int, height: int, color_mode: str, bitdepth: int, name: str):
    '''
    Create a group layer object.

    Args:
        width (int): image width
        height (int): image height
        color_mode (str): Colormode, usually RGB or CMYK e.g. psapi.enum.ColorMode.rgb
        bitdepth (int): color depth, can be 8, 16 or 32
        name (str): group layer name

    Returns:
        psapi.GroupLayer_*N*bit: group layer object
    '''
    # Construct our layer instance, width and height must be specified for this to work!
    if bitdepth is 8:
        group_layer = psapi.GroupLayer_8bit(layer_name=name, width=width, height=height, color_mode=color_mode)
    elif bitdepth is 16:
        group_layer = psapi.GroupLayer_16bit(layer_name=name, width=width, height=height, color_mode=color_mode)
    elif bitdepth is 32:
        group_layer = psapi.GroupLayer_32bit(layer_name=name, width=width, height=height, color_mode=color_mode)

    return group_layer

def add_layer_to_group(ps_document, layer, group_layer):
    # add a ps layer to a layer group
    group_layer.add_layer(ps_document, layer)

def add_layer_to_document(layer, ps_document):
    # layer can be group layer or image layer
    ps_document.add_layer(layer)

def save_ps(ps_document, filepath):
    # save a ps file to disc
    ps_document.write(filepath)

