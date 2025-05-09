from PIL import ImageOps, Image
import os


def padding(img):
    files = os.listdir(path)
    for file in files:
        file_path = os.path.join(path, file)
        img = Image.open(file_path)
        x = img.size[0]
        y = img.size[1]
        type = '0'
        pad_right = int((375-x)*(375*3.2-x)/375)
        pad_left = int(375*3.2+(375*3.2-x)-(375-x)*(375*3.2-x)/375)
        pad_up = int((375-y)*(375*1.2-y)/375)
        pad_down = int(375*3.6+(375*1.2-y)-(375-y)*(375*1.2-y)/375)
        expanded_img = ImageOps.expand(img, border=(pad_left, pad_up, pad_right, pad_down), fill=(0, 255, 255))
        expanded_img.save(file)
        x_position = (pad_left+(x/2))/(pad_left+pad_right+x)
        y_position = (pad_up+(y/2))/(pad_up+pad_down+y)
        width = x/(pad_left+pad_right+x)
        height = y/(pad_up+pad_down+y)
        file_name = file[0:(len(file)-5)] + '.txt'
        with open(file_name, 'w') as f:
            f.write(f'{type} {x_position} {y_position} {width} {height}')