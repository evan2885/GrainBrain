import matplotlib.pyplot as plt
import os
import hashlib
import struct
import numpy as np
from PIL import Image


# Ändra var du vill ha bilderna här
destination_folder = "C:/Users/eveli/Documents/Universitetskurser/Tillämpad bioinformatik/all_masks/"
root_folder_path = "croptailor/oat_images/Additional data with labels/"

# Kommentera bort den här raden om du redan har skapat en mapp för bilderna
os.makedirs(destination_folder)


def read_seed(start_byte,out_hex):
    """
    This function reads the coordinates and some attributes of __one__  seed in an image from a .tbin file generated by
    SmartGrain.

    Inputs:
        start_byte: The first byte to start reading for the current seed
        out_hex: The full raw hexadecimal file, containing all seeds.
    Output:
        seed: a dictionary containing the fields
        ["Centroid", "IS (intersection?)", "Length", "width", "Area", "PL", "Circularity", "Contour"]
        , where Contour contains the coordinates of the pixels at the contour of the seed.
        new_start: The byte to start reading the next seed.
    """
    vals = []
    line = out_hex[start_byte:start_byte+48]
    for i in range(len(line) // 4):
        hexval = "".join(line[i * 4:i * 4 + 4][::-1])
        decimal_val = struct.unpack("!l", bytes.fromhex(hexval))[0]
        vals.append(decimal_val)

    vals2 = np.reshape(vals, [6, 2])
    # Bytes 48 through  52 are zeroes.

    # Next are a bunch of properties of the seed as computed by SmartGrain, described below, and stored in attrib.
    # Attributes = ["Centroid", "IS (intersection?)", "Length", "width", "Area", "PL", "Circularity"]
    line = out_hex[start_byte+52:start_byte+52+100]
    attrib = []
    for i in range(len(line) // 8):
        hexval = "".join(line[i * 8:i * 8 + 8][::-1])
        decimal_val = struct.unpack("!d", bytes.fromhex(hexval))[0]
        attrib.append(decimal_val)

    # Read the number of points defining the outline of the seed.
    line = out_hex[start_byte+304:start_byte+308]
    for i in range(len(line) // 4):
        hexval = "".join(line[i * 4:i * 4 + 4][::-1])
        decimal_val = struct.unpack("!l", bytes.fromhex(hexval))[0]
        n_points = decimal_val

    # Read the coordinate of the seeds.
    line = out_hex[start_byte+308:start_byte+308 + ((n_points ) * 3 * 4)]
    coords = []
    for i in range((n_points) * 3):
        hexval = "".join(line[i * 4:i * 4 + 4][::-1])
        decimal_val = struct.unpack("!l", bytes.fromhex(hexval))[0]
        coords.append(decimal_val)

    coords2 = np.reshape(coords, [n_points, 3])

    # Compute at which byte to start reading the next seed in the image.
    new_start = start_byte+308 + ((n_points ) * 3 * 4)

    # Store the seed attributes as a dictionary.
    seed = {}
    seed["Centroid"] = np.array([attrib[0], attrib[1]])
    seed["Intersection"] = np.array([attrib[2], attrib[3]])
    seed["Length"] = np.array([attrib[4]])
    seed["Width"] = np.array([attrib[5]])
    seed["Area"] = np.array([attrib[6]])
    seed["PL"] = np.array([attrib[7]])
    seed["Circularity"] = np.array([attrib[8]])
    seed["Contour"] = coords2

    return  seed, new_start

# Given a filename, start reading the data for all the seeds.
# This is probably an ugly solution programming-wise, but it works. It keeps reading seeds from the tbin file, until the
# new starting byte has reached end-of-file, without knowing how large the file is.

def process_file(file, file_number): 
    
    plt.close("all")

    seeds = []
    start_byte = 120
    i = 0
    try:

        # Read the entire hex-file.
        with open(file, "rb") as f:
            buff = f.read()
        out_hex = ['{:02X}'.format(b) for b in buff]

        #Keep reading the data for each seed in the image, until we reach the end.
        # Store them as a list of dictionaries, one for each seed.
        while True: # (don't do this hehe... can probably do something more elegant/smarter)
            seed, start_byte = read_seed(start_byte = start_byte, out_hex = out_hex)
            seeds.append(seed)
            i +=1
            print(f"Read seed no. {i}")
    except:
        pass


    areas = []
    Circularities = []
    areas = [] #EN TILL? MISSTAG?

    for seed in seeds:
        areas.append(seed["Area"])
        Circularities.append(seed["Circularity"])


    areas = np.array(areas)

    # Without being careful, SmartGrain can also segment other stuff, e.g., parts of the ruler, or tiny specks
    # which shouldn't be considered seeds. The below line removes unreasonably large, and small values.
    #  Real seeds seems to, __in this particular camera setup__, have reasonable seed areas vary between around 2000 - 5000
    seed_inds = np.where(np.all(np.hstack([np.array(areas) < 100000,  np.array(areas) > 200]), axis = 1))[0]

    # Knasig men användbar funktion
    def cool_file_function(output_file):
        fig, ax = plt.subplots()

        for seed in np.take(seeds, seed_inds):
            plt.plot(seed["Contour"][:,0],seed["Contour"][:,1])

        ax.invert_yaxis()

        fig.savefig(output_file)
        plt.close(fig)

    cool_file_function(destination_folder + file_number + '.png')

def process_files_in_folder(folder_path):
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.tbin'):
            file_path = os.path.join(folder_path, file_name)
            process_file(file_path, file_name)

def process_files_in_all_folders(root_folder):
    for folder_name in os.listdir(root_folder):
        folder_path = os.path.join(root_folder, folder_name)
        if os.path.isdir(folder_path):
            process_files_in_folder(folder_path)

process_files_in_all_folders(root_folder_path)