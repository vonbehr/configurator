import pandas as pd
from colormath.color_objects import sRGBColor
import colormath
import math
import colour
import numpy
import maya.app.renderSetup.model.renderSetup as renderSetup
import maya.api.OpenMaya as om
import maya.cmds as cmds

'''
    The car has two VRaySwitchMaterials assigned to the correct geo:
    base_paint, twotone_paint.

    base_paint has two shaders connected:
        0: solid_carpaint (VRayMtl):
        1: metallic_carpaint (VRayCarpaint)

    twotone_paint has four shaders conencted:
        0: solid_carpaint
        1: metallic_carpaint
        2: twowone_black (VrayCarpaint2)
        3: twotone_gray (VRayCarpaint2)

    All frozen carpaints are metallic.
    All two-tone carpaints are metallic.

    Two-tone black = [ 0.01168132  0.01224731  0.01620415]
    Two-tone gray = [ 0.61188067  0.59859144  0.5638031 ]

    There is one renderlayer per color variation (only one color, two-tone black, two tone grey).
    Each renderlayer has one collection for each switch material (filter: shaders).
    Each collection has an absolute override on the .materialsSwitch Attribute to select the correct shader for the layer.
'''


def read_excel_rows(filepath: str) -> list:
    '''
    Read the Excel file passed as an agument and return the rows as a list

    Args:
        filepath (str): Excel file to read

    Returns:
        list: The rows of the file as a list of lists
    '''
    # Load the Excel file
    try:
        df = pd.read_excel(filepath)
    except FileNotFoundError:
        om.MGlobal.displayInfo(f"Excel file not found. {filepath}")
        return None

    # Convert each row to a list and collect them in a list
    rows_as_lists = df.values.tolist()

    # return the list
    return rows_as_lists

def create_rl(rl_name: str, shader1: int, shader2: int, color: tuple, clearcoat: bool):
    '''
    Create renderlayers, collections and overrides based on the arguments.

    Args:
        rl_name (str): Name of the renderlayer
        shader1 (int): Switch shader ID to use
        shader2 (int): Switch shader ID to use
        color (tuple): color for the override
        clearcoat (bool): Is this a clearcoat or frozen shader
    '''

    # set glossiness for override
    if clearcoat is True:
        coat_glossiness = 0.97
    elif clearcoat is False:
        coat_glossiness = 0.78

    rs = renderSetup.instance()

    rs.switchToLayerUsingLegacyName("defaultRenderLayer")

    # Create and append the render layer for the paint variant
    renderlayer = rs.createRenderLayer(rl_name)

    # Create collections for everything.
    mainCol = renderlayer.createCollection("mainCol01")
    # Set up collection 1 to contain the whole scene, and the other collections the sahders
    mainCol.getSelector().setPattern('*')

    ####################
    # Switch materials #
    ####################

    # create collections
    switch1_col = renderlayer.createCollection("switch1Col001")
    switch2_col = renderlayer.createCollection("switch2Col001")

    # set filter to shader
    switch1_col.getSelector().setFilterType(3)
    switch2_col.getSelector().setFilterType(3)

    # add the shader to the collections
    switch1_col.getSelector().staticSelection.set(["base_paint"])
    switch2_col.getSelector().staticSelection.set(["twotone_paint"])

    # create the overrides
    switch1_override = switch1_col.createAbsoluteOverride("switch001", "materialsSwitch")
    switch2_override = switch2_col.createAbsoluteOverride("switch002", "materialsSwitch")

    # set the values
    switch1_override.setAttrValue(shader1)
    switch2_override.setAttrValue(shader2)


    ###################
    # Carpaint shader #
    ###################

    # create collection
    carpaint_col = renderlayer.createCollection("carpaint_col001")

    # set filter to shader
    carpaint_col.getSelector().setFilterType(3)

    # add shader to collection and create overrides
    # for metallic carpaints
    if shader1 == 1:
        carpaint_col.getSelector().staticSelection.set(["metallic_carpaint"])
        color_override = carpaint_col.createAbsoluteOverride("carpaint_color_override001", "base_color")
        clearcoat_override = carpaint_col.createAbsoluteOverride("carpaint_clearcoat_override001", "coat_glossiness")
        color_override.setAttrValue(color)
        clearcoat_override.setAttrValue(coat_glossiness)

    # and for solid carpaints
    elif shader1 == 0:
        carpaint_col.getSelector().staticSelection.set(["solid_carpaint"])
        color_override = carpaint_col.createAbsoluteOverride("carpaint_color_override001", "color")
        color_override.setAttrValue(color)

def hex_to_rgb(hex: str) ->tuple:
    '''
    Convert a hex color into an RGB tuple. RGB value has a range of 0 - 1.

    Args:
        hex (str): Color in hex

    Returns:
        tuple: Color in RGB
    '''
    srgb_obj = colormath.color_objects.sRGBColor.new_from_rgb_hex(hex)

    return colormath.color_objects.sRGBColor.get_value_tuple(srgb_obj)

def srgb_to_aces(srgb_color: tuple) -> list:
    '''
    Convert color values from sRGB to ACEScg colorspace.

    Args:
        srgb_color (tuple): A tuple (or list) with 3 RGB values in the range from 0 to 1.

    Returns:
        list: 3 color values in the range from 0 to 1.
    '''

    cs_sRGB = colour.RGB_COLOURSPACES["sRGB"]
    cs_ACEScg = colour.RGB_COLOURSPACES["ACEScg"]

    source = numpy.array(srgb_color, dtype=numpy.core.float32)
    converted = source.astype(dtype=numpy.core.float32)
    acescg_color = colour.RGB_to_RGB(
        converted,
        cs_sRGB,
        cs_ACEScg,
        chromatic_adaptation_transform="CAT02",
        # remove the sRGB transfer-function
        apply_cctf_decoding=True,
        # ACEScg defined a linear encode so will not do anything anyway
        apply_cctf_encoding=True,
    )

    return acescg_color

def configurator(filepath: str):
    '''
    Parse the rows of the excel file and create renderlayers based on the info.

    Args:
        filepath (str): FIlepath to Excel file with config.
    '''

    rows = read_excel_rows(filepath)

    # Colorcode Name    SKIP    Hex SKIP    Type    SKIP    duotone SKIP
    #   0       1       2       3   4       5       6       7       8

    if rows != None:
        # iterate over rows, extract data and call function to create render layer.
        for row in rows:
            rl_name = row[0]

            hex_color = row[3][1:]
            srgb_color = hex_to_rgb(hex_color)
            aces_color = srgb_to_aces(srgb_color)

            if row[5] == "Metallic":
                shader1 = 1
                clearcoat = True
            elif row[5] == "Uni":
                shader1 = 0
                clearcoat = True
            elif row[5] == "Frozen":
                shader1 = 1
                clearcoat = False
            else:
                om.MGlobal.displayInfo("Could not parse correct Clearcoat info. Please check Excel file.")
                continue

            if row[7] == "Individual TT":
                twotone = True
            elif row[7] == "No":
                twotone = False
            else:
                om.MGlobal.displayInfo("Could not parse correct tow tone info. Please check Excel file.")
                continue

            create_rl(rl_name, shader1, shader1, aces_color, clearcoat)
            # create 2 additional renderlayer for dualtone variants
            if twotone is True:
                create_rl(rl_name, shader1, 2, aces_color, clearcoat)
                create_rl(rl_name, shader1, 3, aces_color, clearcoat)


configurator("C:/Users/florianbehr/Documents/_repository/configurator/G70_Individual_Color_List_0423.xlsx")
