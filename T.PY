import rawpy
import PIL
import matplotlib.pyplot as plt
import cv2
import imageio

raw_filename = 'default.nef'

# with rawpy.imread(raw_filename) as raw:
#     # raw type (flat or stack, e.g., Foveon sensor)
#     print(f'raw type:                     {raw.raw_type}')
#     # number of different color components, e.g., 3 for common RGB Bayer sensors with two green identical green sensors
#     print(f'number of colors:             {raw.num_colors}')
#     # describes the various color components
#     print(f'color description:            {raw.color_desc}')
#     # decribes the pattern of the Bayer sensor
#     print(f'raw pattern:                  {raw.raw_pattern.tolist()}')
#     # black level correction
#     print(f'black levels:                 {raw.black_level_per_channel}')
#     # camera white level
#     print(f'white level:                  {raw.white_level}')
#     # camera specific color matrix, usually obtained from a list in rawpy (not from the raw file)
#     print(f'color matrix:                 {raw.color_matrix.tolist()}')
#     # camera specific XYZ to camara RGB conversion matrix
#     print(f'XYZ to RGB conversion matrix: {raw.rgb_xyz_matrix.tolist()}')
#     # the picture's white balance as determined by the camera
#     print(f'camera white balance:         {raw.camera_whitebalance}')
#     # the camera's daylight white balance
#     print(f'daylight white balance:       {raw.daylight_whitebalance}')

im = rawpy.imread(raw_filename)
rgb = im.postprocess(no_auto_bright=True,
                    use_auto_wb=True, use_camera_wb=True)
im.close()

imageio.imsave('linear.png', rgb)

    # rgb = raw.postprocess()
    # print(rgb.dtype)
    # width, height, channels = rgb.shape
    # print(width, height, channels)
    # plt.imshow(rgb)
    # imageio.imsave('linear.png', rgb)
    
    # cvuint8 = cv2.convertScaleAbs(rgb)
    # print(cvuint8.dtype)
    # plt.imsave('a.png', cvuint8)