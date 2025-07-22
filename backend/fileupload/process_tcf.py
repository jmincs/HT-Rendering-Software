import h5py
import numpy as np
from PIL import Image
import cv2
from multiprocessing.pool import ThreadPool
import os, glob
import torch
from pycave.bayes import GaussianMixture
from skimage.transform import resize

progress_file_path = 'media/progress.txt'
num_frames = 1

def set_progress(percent_complete):
    with open(progress_file_path, 'w') as f:
        f.write(f"{percent_complete:06.2f}")

def get_progress_data():
    if os.path.exists(progress_file_path):
        with open(progress_file_path, 'r') as f:
            return float(f.read().strip())
        
def set_num_frames(n):
    global num_frames
    num_frames = n

def ReadLDMTCFHT_10(file, timeFrameIndex):
    dataPath = '/Data/3D/{:06d}'.format(timeFrameIndex)
    minValue = file[dataPath].attrs['RIMin']
    tileCount = int(file[dataPath].attrs['NumberOfTiles'])
    tile_name_length = len(list(file[dataPath])[0].split('_')[-1])
    dataSizeX = int(file[dataPath].attrs['DataSizeX'])
    dataSizeY = int(file[dataPath].attrs['DataSizeY'])
    dataSizeZ = int(file[dataPath].attrs['DataSizeZ'])
    z_center = dataSizeZ//2+1
    data = np.zeros((dataSizeX, dataSizeY, 20))

    for tileIndex in range(1, tileCount + 1):
        tileString = "{:0>{length}}".format(tileIndex - 1, length=tile_name_length)
        tilePath = dataPath + '/TILE_' + tileString
        samplingStep = file[tilePath].attrs['SamplingStep']
        if samplingStep != 1:
            continue

        tileData = np.transpose(file[tilePath][:, :, :].astype(np.float32))/1000 + minValue
        offsetX = file[tilePath].attrs['DataIndexOffsetPointX'] - 1
        offsetY = file[tilePath].attrs['DataIndexOffsetPointY'] - 1
        offsetZ = file[tilePath].attrs['DataIndexOffsetPointZ'] - 1
        lastX = file[tilePath].attrs['DataIndexLastPointX']
        lastY = file[tilePath].attrs['DataIndexLastPointY']
        lastZ = file[tilePath].attrs['DataIndexLastPointZ']
        mappingRangeX = np.arange(offsetX, lastX)
        mappingRangeY = np.arange(offsetY, lastY)
        mappingRangeZ = np.arange(0, 20)
        dataRangeX = np.arange(0, mappingRangeX.size)
        dataRangeY = np.arange(0, mappingRangeY.size)
        dataRangeZ = np.arange(z_center-10, z_center+10)
        meshgrid = np.ix_(mappingRangeX, mappingRangeY, mappingRangeZ)
        data[meshgrid] = tileData[dataRangeX[:, np.newaxis, np.newaxis], dataRangeY[np.newaxis, :, np.newaxis], dataRangeZ[np.newaxis, np.newaxis, :]]

        # Calculate and display percentage completed
        percent_complete = ((timeFrameIndex * tileCount + tileIndex) / (tileCount * num_frames)) * 100
        set_progress(percent_complete)

    return data

def sigmoid(x, a=1):
    return 1 / (1 + np.exp(-a * x))

def increase_contrast(image, strength=0.4, midpoint=0.5):
    # Ensure the image is in float format and normalized to [0, 1]
    image_float = image.astype(float) / 255.0
    
    # Apply sigmoid contrast adjustment
    adjusted = sigmoid((image_float - midpoint) * strength * 10) 
    
    # Rescale to [0, 1]
    min_val, max_val = adjusted.min(), adjusted.max()
    adjusted = (adjusted - min_val) / (max_val - min_val)
    
    # Convert back to original range and dtype
    return (adjusted * 255).astype(np.uint8)

def save_image(args):
    array, array2, z, frame_num, output_dir = args
    # Convert to uint8
    image_uint8 = array[:,:,z].astype(np.uint8)
    image2_uint8 = array2[:,:,z].astype(np.uint8)

    image_uint8c = increase_contrast(image_uint8)
    image2_uint8c = increase_contrast(image2_uint8)

    # Generate the output filename in the output directory
    filename = os.path.join(output_dir, f"HT_frame_{frame_num:06d}_{z+1:02d}.tga")
    filename2 = os.path.join(output_dir, f"FL_frame_{frame_num:06d}_{z+1:02d}.tga")

    pilImage = Image.fromarray(image_uint8c, mode='L')
    pilImage2 = Image.fromarray(image2_uint8c, mode='L')
    
    # Save as TGA
    pilImage.save(filename, format='TGA')
    pilImage2.save(filename2, format='TGA')
    
    return f"Saved {filename} and {filename2}"

def generate_images(array, array2, frame_num, output_dir):
    # Create the output directory if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create a ThreadPool
    with ThreadPool() as pool:
        # Prepare arguments for each thread
        args_list = [(array, array2, z, frame_num, output_dir) for z in range(20)]
        
        # Map the save_image function to the arguments
        results = pool.map(save_image, args_list)
    
    # Print the results
    for result in results:
        print(result)

def ReadLDMTCFFL_10(file, timeFrameIndex):
    # Get only middle 10 slices for saving
    dataPath = '/Data/3DFL/CH0/{:06d}'.format(timeFrameIndex)

    minValue = file[dataPath].attrs['MinIntensity']

    tileCount = int(file[dataPath].attrs['NumberOfTiles'])
    tile_name_length = len(list(file[dataPath])[0].split('_')[-1])

    dataSizeX = int(file[dataPath].attrs['DataSizeX'])
    dataSizeY = int(file[dataPath].attrs['DataSizeY'])
    dataSizeZ = int(file[dataPath].attrs['DataSizeZ'])
    z_center = dataSizeZ//2+1

    data = np.zeros((dataSizeX, dataSizeY, 20))    

    for tileIndex in range(1, tileCount + 1):
        tileString = "{:0>{length}}".format(tileIndex - 1, length= tile_name_length)
        tilePath = dataPath + '/TILE_' + tileString
        samplingStep = file[tilePath].attrs['SamplingStep']

        if samplingStep != 1:
            continue

        tileData = np.transpose(file[tilePath][:, :, :].astype(np.float32))/1000 + minValue

        offsetX = file[tilePath].attrs['DataIndexOffsetPointX']-1
        offsetY = file[tilePath].attrs['DataIndexOffsetPointY']-1
        offsetZ = file[tilePath].attrs['DataIndexOffsetPointZ']-1

        lastX = file[tilePath].attrs['DataIndexLastPointX']
        lastY = file[tilePath].attrs['DataIndexLastPointY']
        lastZ = file[tilePath].attrs['DataIndexLastPointZ']

        mappingRangeX = np.arange(offsetX, lastX)
        mappingRangeY = np.arange(offsetY, lastY)
        mappingRangeZ = np.arange(0,20)#np.arange(offsetZ, lastZ)[z_center-5:z_center+5]

        dataRangeX = np.arange(0, mappingRangeX.size)
        dataRangeY = np.arange(0, mappingRangeY.size)
        # dataRangeZ = np.arange(0, mappingRangeZ.size)
        dataRangeZ = np.arange(z_center-10, z_center+10)

        meshgrid = np.ix_(mappingRangeX, mappingRangeY, mappingRangeZ)
        data[meshgrid] = tileData[dataRangeX[:,np.newaxis,np.newaxis],dataRangeY[np.newaxis,:,np.newaxis],dataRangeZ[np.newaxis,np.newaxis,:]]

    return data

def remove_background(voxel_grid):
    voxel_shape = voxel_grid.shape

    voxel_grid = cv2.normalize(voxel_grid, None, 0, 255, cv2.NORM_MINMAX)
    intensities = voxel_grid[voxel_grid > 0].astype(np.float64)
    points = np.argwhere(voxel_grid > 0)

    print("Gaussian Mixture Model...")

    intensities_t = torch.Tensor(intensities).unsqueeze(-1)

    model = GaussianMixture(
        num_components=2,
        covariance_type='full',
        init_strategy='kmeans++',
        batch_size=16000000,
        trainer_params=dict(accelerator='gpu', devices=1)
    )

    model.fit(intensities_t)
    labels = model.predict(intensities_t)
    background_label = np.argmax(np.bincount(labels))

    foreground_indices = np.where(labels != background_label)[0]
    points = points[foreground_indices]
    intensities = intensities[foreground_indices]

    print("Creating Matrix...")
    # Create matrix
    matrix = np.zeros((voxel_shape), dtype=np.uint8)
    int_points = points.astype(int)
    matrix[int_points[:, 0], int_points[:, 1], int_points[:, 2]] = intensities
    return matrix