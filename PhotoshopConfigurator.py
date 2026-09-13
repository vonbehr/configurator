import os
import re
from typing import List, Optional, Tuple, Union

import cv2
import numpy as np
import OpenImageIO as oiio
import psapi
from OpenImageIO import ImageBuf, ImageBufAlgo


LayeredFile = Union[psapi.LayeredFile_8bit, psapi.LayeredFile_16bit, psapi.LayeredFile_32bit]
Layer = Union[psapi.Layer_8bit, psapi.Layer_16bit, psapi.Layer_32bit]
GroupLayer = Union[psapi.GroupLayer_8bit, psapi.GroupLayer_16bit, psapi.GroupLayer_32bit]


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
    converted_file = os.path.join(path, file + ".png")

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


def get_images_from_folder(path: str, extension: str) -> List[str]:
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


def parse_carpaint_filename(filename: str) -> Tuple[str, str]:
    '''
    Extract the carpaint color name and its render-pass group name from a
    render filename, e.g. "0001renderRenderBlue_PhytonicBlueMetallic_v001.exr".

    Args:
        filename (str): Render filename (not a full path)

    Returns:
        Tuple[str, str]: (color_name, group_name)

    Raises:
        ValueError: If the filename does not match the expected naming convention.
    '''
    group_match = re.findall(r"[0-9a-zA-z]*renderRender([a-zA-Z]*)_[0-9a-zA-z.]*", filename)
    color_match = re.findall(r"[0-9a-zA-z]*renderRender[a-zA-Z]*_([0-9a-zA-z]*)_[a-zA-Z0-9.]*", filename)

    if not group_match or not color_match:
        raise ValueError(f"Filename does not match expected carpaint render naming convention: {filename}")

    return color_match[0], group_match[0]


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


def export_layers(filepath: str, out_path: str) -> None:
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


def write_layer(layer: psapi.ImageLayer_8bit, out_path: str) -> None:
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

    cv2.imwrite(os.path.join(out_path, name + ".png"), packed_array)


def create_ps_file(width: int, height: int, color_mode: psapi.enum.ColorMode, bitdepth: int) -> LayeredFile:
    '''
    Create a layered Photoshop file object

    Args:
        width (int): Width in pixel
        height (int): Height in pixel
        color_mode (psapi.enum.ColorMode): Colormode, usually RGB or CMYK e.g. psapi.enum.ColorMode.rgb
        bitdepth (int): color depth, can be 8, 16 or 32

    Returns:
        LayeredFile: layered Photoshop file object
    '''

    if bitdepth == 8:
        ps_document = psapi.LayeredFile_8bit(color_mode, width, height)
    elif bitdepth == 16:
        ps_document = psapi.LayeredFile_16bit(color_mode, width, height)
    elif bitdepth == 32:
        ps_document = psapi.LayeredFile_32bit(color_mode, width, height)
    else:
        raise ValueError(f"Unsupported bitdepth: {bitdepth}. Must be 8, 16 or 32.")

    return ps_document


def read_ps_file(filepath: str) -> Tuple[LayeredFile, int, int, "psapi.enum.BitDepth"]:
    '''
    Read a Photoshop file from disc and return the document along with its dimensions and bit depth.

    Args:
        filepath (str): Filepath to the Photoshop file

    Returns:
        Tuple[LayeredFile, int, int, psapi.enum.BitDepth]: The document, width, height and bit depth.
    '''
    ps_document = psapi.LayeredFile.read(filepath)

    width = ps_document.width
    height = ps_document.height
    bit_depth = psapi.PhotoshopFile.find_bitdepth(filepath)

    return ps_document, width, height, bit_depth


def create_layer(image: np.ndarray, width: int, height: int, color_mode: psapi.enum.ColorMode, bitdepth: int, name: str) -> Layer:
    '''
    Create a Photoshop layer object.

    Args:
        image (np.ndarray): Image object
        width (int): image width
        height (int): image height
        color_mode (psapi.enum.ColorMode): Colormode, usually RGB or CMYK e.g. psapi.enum.ColorMode.rgb
        bitdepth (int): color depth, can be 8, 16 or 32
        name (str): layer name

    Returns:
        Layer: layer object
    '''

    # Construct our layer instance, width and height must be specified for this to work!
    if bitdepth == 8:
        layer = psapi.ImageLayer_8bit(image, layer_name=name, width=width, height=height, color_mode=color_mode)
    elif bitdepth == 16:
        layer = psapi.ImageLayer_16bit(image, layer_name=name, width=width, height=height, color_mode=color_mode)
    elif bitdepth == 32:
        layer = psapi.ImageLayer_32bit(image, layer_name=name, width=width, height=height, color_mode=color_mode)
    else:
        raise ValueError(f"Unsupported bitdepth: {bitdepth}. Must be 8, 16 or 32.")

    return layer


def create_group_layer(width: int, height: int, color_mode: psapi.enum.ColorMode, bitdepth: int, name: str) -> GroupLayer:
    '''
    Create a group layer object.

    Args:
        width (int): image width
        height (int): image height
        color_mode (psapi.enum.ColorMode): Colormode, usually RGB or CMYK e.g. psapi.enum.ColorMode.rgb
        bitdepth (int): color depth, can be 8, 16 or 32
        name (str): group layer name

    Returns:
        GroupLayer: group layer object
    '''
    # Construct our layer instance, width and height must be specified for this to work!
    if bitdepth == 8:
        group_layer = psapi.GroupLayer_8bit(layer_name=name, width=width, height=height, color_mode=color_mode)
    elif bitdepth == 16:
        group_layer = psapi.GroupLayer_16bit(layer_name=name, width=width, height=height, color_mode=color_mode)
    elif bitdepth == 32:
        group_layer = psapi.GroupLayer_32bit(layer_name=name, width=width, height=height, color_mode=color_mode)
    else:
        raise ValueError(f"Unsupported bitdepth: {bitdepth}. Must be 8, 16 or 32.")

    return group_layer


def add_layer_to_group(ps_document: LayeredFile, layer: Layer, group_layer: GroupLayer) -> None:
    '''
    Add a Photoshop layer to a layer group.

    Args:
        ps_document (LayeredFile): Photoshop document the layer belongs to
        layer (Layer): Layer to add
        group_layer (GroupLayer): Group layer to add the layer to
    '''
    group_layer.add_layer(ps_document, layer)


def add_layer_to_document(ps_document: LayeredFile, layer: Layer) -> None:
    '''
    Add a layer (image or group) to the top level of a Photoshop document.

    Args:
        ps_document (LayeredFile): Photoshop document to add the layer to
        layer (Layer): Layer or group layer to add
    '''
    ps_document.add_layer(layer)


def save_ps(ps_document: LayeredFile, filepath: str) -> None:
    '''
    Save a Photoshop document to disc.

    Args:
        ps_document (LayeredFile): Photoshop document to save
        filepath (str): Destination filepath
    '''
    ps_document.write(filepath)


def get_size(filepath: str) -> Optional[Tuple[int, int]]:
    '''
    Get the pixel resolution of a given image file

    Args:
        filepath (str): Filepath of the file

    Returns:
        Optional[Tuple[int, int]]: (width, height) in pixels, or None if the file could not be opened.
    '''

    inbuffer = oiio.ImageInput.open(filepath)

    if inbuffer:
        spec = inbuffer.spec()
        width = spec.width
        height = spec.height
        inbuffer.close()

        return width, height

    return None


def ingest(filepath: str, output_path_ str, ocio_path: str) -> None:
    '''
    Build a layered Photoshop document from a folder of rendered EXR frames.

    Reads every ``.exr`` file below filepath, converts each to sRGB PNG, and
    adds it to a new Photoshop document as an image layer, grouped by render
    pass (base car vs. two-tone roof vs. individual carpaint colors).

    Args:
        filepath (str): Root folder to search for .exr render files.
    '''
    # set env var for color conversion
    os.environ["OCIO"] = ocio_path

    # colormode of the ps doc
    colormode = psapi.enum.ColorMode.rgb

    # get exr files from folder
    exr_files = get_images_from_folder(filepath, "exr") or []

    if not exr_files:
        raise FileNotFoundError(f"No .exr files found under {filepath}")

    # get the pixel dimensions from the first exr file. We assume all files have the same size.
    size = get_size(exr_files[0])
    if size is None:
        raise ValueError(f"Could not read image dimensions from {exr_files[0]}")
    width, height = size

    # create a Photoshop doc with the right colormode and dimensions
    ps_document = create_ps_file(width, height, colormode, 8)

    # create a list of needed group layers
    group_layer_names = []
    car_group_name: Optional[str] = None
    twotone_group_name: Optional[str] = None

    for file in exr_files:
        filename = os.path.basename(file)

        if "renderRenderCar" in filename:
            car_group_name = "Car"
            continue

        elif "TwoTone" in filename:
            twotone_group_name = "Two Tone"
            continue

        else:
            _, group_name = parse_carpaint_filename(filename)

        group_layer_names.append(group_name)

    if car_group_name is None:
        raise ValueError("No 'renderRenderCar' file found - cannot determine the base car group.")
    if twotone_group_name is None:
        raise ValueError("No 'TwoTone' file found - cannot determine the two-tone group.")

    # convert to a set, back to a list and sort it to get rid of duplicates
    group_layer_names = sorted(set(group_layer_names))

    # add base car and two tone groups. Car group will be at the bottom, two tone at the top
    group_layer_names.insert(0, twotone_group_name)
    group_layer_names.append(car_group_name)

    # create needed layer groups and add them to dict
    group_layer_dict = {}
    for name in group_layer_names:
        group_layer = create_group_layer(width, height, colormode, 8, name)

        # add group layer to ps doc
        add_layer_to_document(ps_document, group_layer)

        # add name and group layer object to dict
        group_layer_dict.update({name: group_layer})

    # convert exr files from ACEScg to sRGB in PNG and add them to the PS doc
    for file in exr_files:
        # just the filename from the exr file
        filename = os.path.basename(file)

        print(f"Processing {filename}")

        # get layer and group name
        if "renderRenderCar" in filename:
            layer_name = "Base Car"
            group_name = "Car"

        elif "TwoToneBlack" in filename:
            layer_name = "Two Tone Black"
            group_name = "Two Tone"

        elif "TwoToneGray" in filename:
            layer_name = "Two Tone Gray"
            group_name = "Two Tone"

        else:
            layer_name, group_name = parse_carpaint_filename(filename)

        # convert exr file
        png_image = convert_exr(file)

        # create a layer object
        layer_image = load_image(png_image)
        layer = create_layer(layer_image, width, height, colormode, 8, layer_name)

        add_layer_to_group(ps_document, layer, group_layer_dict[group_name])

    save_ps(ps_document, output_path)


def compose(filepath: str, output_path: str, ocio_path: str) -> None:
    '''
    Composite each carpaint render over the base car render and the two-tone
    gray roof render, writing one output PNG per color.

    Args:
        filepath (str): Root folder to search for .exr render files.
    '''
    # set env var for color conversion
    os.environ["OCIO"] = ocio_path

    # get exr files from folder
    exr_files = get_images_from_folder(filepath, "exr") or []

    carpaint_renders = []
    car_render: Optional[str] = None
    twotonegray_render: Optional[str] = None

    for file in exr_files:
        filename = os.path.basename(file)

        if "renderRenderCar" in filename:
            car_render = file

        elif "TwoTone" in filename:
            if "TwoToneGray" in filename:
                twotonegray_render = file

        else:
            carpaint_renders.append(file)

    if car_render is None:
        raise ValueError("No 'renderRenderCar' file found - cannot determine the base car render.")
    if twotonegray_render is None:
        raise ValueError("No 'TwoToneGray' file found - cannot determine the two-tone gray render.")

    car_buf = ImageBuf(car_render)
    twotonegray_buf = ImageBuf(twotonegray_render)

    for file in carpaint_renders:
        # just the filename from the exr file
        filename = os.path.basename(file)

        print(f"Processing {filename}")

        color_name, colorgroup_name = parse_carpaint_filename(filename)
        carpaint_buf = ImageBuf(file)

        comp1_buf = ImageBufAlgo.over(carpaint_buf, car_buf)
        comp2_buf = ImageBufAlgo.over(twotonegray_buf, comp1_buf)

        # convert from ACEScg to sRGB
        out_buf = ImageBufAlgo.colorconvert(comp2_buf, "ACES - ACEScg", "out_srgb")

        out_filename = f"{colorgroup_name}_{color_name}.png"

        # write image in 8 Bit
        out_buf.write(os.path.join(output_path, out_filename), "uint8")


if __name__ == "__main__":
    # create Photoshop composites
    ingest("//PATH/TO/RENDERS")

    # create PNG composites
    # compose("//PATH/TO/RENDERS")
