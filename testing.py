from colormath.color_objects import sRGBColor
import colormath

hex = "#cb563b"

rgb = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
print(rgb)

srgb = colormath.color_objects.sRGBColor.new_from_rgb_hex(hex)
print(srgb)
print(type(colormath.color_objects.sRGBColor.get_value_tuple(srgb)))