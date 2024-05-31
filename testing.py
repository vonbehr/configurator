import psapi
import numpy as np
import cv2
import numpy as np

filepath = "C:/Users/florianbehr/Desktop/configurator/Colorchart.psd"

ps_document = psapi.LayeredFile.read(filepath)

# image = cv2.imread("C:/Users/florianbehr/Desktop/configurator/r.jpg", cv2.IMREAD_UNCHANGED)
# print(type(image))

# image_array = dict(enumerate(image.flatten(), 1))
# print(image_array)

# print(ps_document.width)
# print(ps_document.height)

for layer in ps_document.layers:
    # print(type(layer))

    if isinstance(layer, psapi.GroupLayer_8bit):
        print("Group Layer")
        # for sub_layer in layer.layers:
        #     name = sub_layer.name

        #     transformed_image = np.zeros((sub_layer.shape[0], sub_layer.shape[1], sub_layer.shape[2]), np.uint8)
        #     transformed_image[2] = image[:, :, 0]   # Use numpy slicing to get the third channel of bgr
        #     transformed_image[1] = image[:, :, 1]
        #     transformed_image[0] = image[:, :, 2]
        #     # transformed_image[3] = image[:, :, 3]


        #     cv2.imwrite("C:/Users/florianbehr/Desktop/configurator/" + name + ".jpg", transformed_image)

    elif isinstance(layer, psapi.ImageLayer_8bit):
        name = layer.name
        # print(layer.image_data)
        # for key, value in layer.image_data.items():
        #     print(key)
        #     print(value)


        R = layer.image_data[0]
        G = layer.image_data[1]
        B = layer.image_data[2]
        A = layer.image_data[-1]

        packed_array = np.dstack((B, G, R, A))

        cv2.imwrite("C:/Users/florianbehr/Desktop/configurator/" + name + ".png", packed_array)
