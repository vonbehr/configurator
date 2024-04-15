import colour
import numpy



COLORSPACE_sRGB = colour.RGB_COLOURSPACES["sRGB"]
COLORSPACE_ACEScg = colour.RGB_COLOURSPACES["ACEScg"]


def main():
    source = numpy.array([0.138, 0.28, 0.164], dtype=numpy.core.float32)
    converted = source.astype(dtype=numpy.core.float32)  # / 255
    converted = colour.RGB_to_RGB(
        converted,
        COLORSPACE_sRGB,
        COLORSPACE_ACEScg,
        chromatic_adaptation_transform="CAT02",
        # remove the sRGB transfer-function
        apply_cctf_decoding=True,
        # ACEScg defined a linear encode so will not do anything anyway
        apply_cctf_encoding=True,
    )
    print(converted)


if __name__ == "__main__":
    main()