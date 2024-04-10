import pandas as pd
import math
import maya.app.renderSetup.model.renderSetup as renderSetup

'''
   Two carpaint shaders assigned to the correct geo:
   carpaint01, carpaint02
'''


def read_excel_rows(file_path):
    # Load the Excel file
    df = pd.read_excel(file_path)

    # Convert each row to a list and collect them in a list
    rows_as_lists = df.values.tolist()

    # return the list
    return rows_as_lists


def create_rl(rl_name, c1r, c1g, c1b, metallic01, clearcoat01, c2r, c2g, c2b, metallic02, clearcoat02):

    rs = renderSetup.instance()

    rs.switchToLayerUsingLegacyName("defaultRenderLayer")

    # Create and append the render layer for the paint variant
    renderlayer = rs.createRenderLayer(rl_name)

    # Create collections for everything.
    mainCol = renderlayer.createCollection("mainCol01")
    # Set up collection 1 to contain the whole scene, and the other collections the sahders
    mainCol.getSelector().setPattern('*')

    # And one collection for the first shader override
    shader01Col = renderlayer.createCollection("shaderCol01")
    # set filter to shaders
    shader01Col.getSelector().setFilterType(3)
    # add 1st carpaint shader to collection
    shader01Col.getSelector().staticSelection.set(["carpaint01"])

    # create overrides for shader
    shader01ColOverride = shader01Col.createAbsoluteOverride("carpaint01", "base_color")
    shader01MetallicOverride = shader01Col.createAbsoluteOverride("carpaint01", "flake_density")
    shader01ClearcoatOverride = shader01Col.createAbsoluteOverride("carpaint01", "coat_glossiness")

    #  set values of overrides
    shader01ColOverride.setAttrValue([c1r, c1g, c1b])
    shader01MetallicOverride.setAttrValue(metallic01)
    shader01ClearcoatOverride.setAttrValue(clearcoat01)

    # and again for the second shader
    shader02Col = renderlayer.createCollection("shaderCol02")
    # set filter to shaders
    shader02Col.getSelector().setFilterType(3)
    # add 1st carpaint shader to collection
    shader02Col.getSelector().staticSelection.set(["carpaint02"])
    # create overrides for shader

    shader02ColOverride = shader02Col.createAbsoluteOverride("carpaint02", "base_color")
    shader02MetallicOverride = shader02Col.createAbsoluteOverride("carpaint02", "flake_density")
    shader02ClearcoatOverride = shader02Col.createAbsoluteOverride("carpaint02", "coat_glossiness")

    # set override values for second shader
    shader02ColOverride.setAttrValue([c2r, c2g, c2b])
    shader02MetallicOverride.setAttrValue(metallic02)
    shader02ClearcoatOverride.setAttrValue(clearcoat02)


# Full path to the Excel file with the config data
file_path = "C:/Users/florianbehr/Documents/_repository/configurator/testconfig.xlsx"
rows = read_excel_rows(file_path)

# iterate over rows, extract data and call function to create render layer.
for row in rows:
    print(row)
    if math.isnan(row[4]) is True:
        print("NaN")

    rl_name = row[0]

    c1r = row[1]
    c1g = row[2]
    c1b = row[3]

    if math.isnan(row[4]) is True:
        c2r = c1r
        c2g = c1g
        c2b = c1b
    else:
        c2r = row[4]
        c2g = row[5]
        c2b = row[6]

    metallic01 = row[7]

    if math.isnan(row[8]) is True:
        metallic02 = metallic01
    else:
        metallic02 = row[8]

    if row[9] == 1:
        clearcoat01 = 1.0
    else:
        clearcoat01 = 0.5

    if math.isnan(row[10]) is True:
        clearcoat02 = clearcoat01
    else:
        if row[10] == 0:
            clearcoat02 = 0.5
        else:
            clearcoat02 = 1.0

    create_rl(rl_name, c1r, c1g, c1b, metallic01, clearcoat01, c2r, c2g, c2b, metallic02, clearcoat02)
