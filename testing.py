import re

filename = "24028_BMWi7Config01_renderRenderBlack_FrozenBlackMetallic_v002.exr"

group_name = (re.findall(r"[0-9a-zA-z]*renderRender[a-zA-Z]*_([0-9a-zA-z]*)_[a-zA-Z0-9.]*", filename))[0]

print(group_name)