import SimpleITK as sitk
import pandas as pd
from pydicom import dcmread, dcmwrite
import numpy as np
import os
import argparse
import glob


def readDicomSeriesFromFolder(dicomFolder: str) -> sitk.Image:
    """Read a dicom image folder to a sitk.Image object

    Args:
        dicomFolder (str): folder containing the dicom series. The folder is
        assumed to contain no other files.

    Returns:
        sitk.Image: imageSeries contained in dicomFolder
    """
    reader = sitk.ImageSeriesReader()
    reader.MetaDataDictionaryArrayUpdateOn()
    reader.LoadPrivateTagsOn()
    reader.SetMetaDataDictionaryArrayUpdate(True)
    fnames = reader.GetGDCMSeriesFileNames(dicomFolder)
    reader.SetFileNames(fnames)
    return reader.Execute()


def replaceValuesInMask(
    image: sitk.Image, mask: sitk.Image, fillValue: float
) -> sitk.Image:
    """Replace the place the values in the image that are specified by the mask
    with the fillValue

    Args:
        image (sitk.Image): image to replace values in
        mask (sitk.Image): boolean mask deciding which values to replace
        fillValue (float): value to paint into the image

    Returns:
        sitk.Image: image with fillValue painted into the masked region
    """

    image_array = sitk.GetArrayFromImage(image)
    mask_array = sitk.GetArrayFromImage(mask)

    image_array_filled = np.copy(image_array)
    image_array_filled = np.where(mask_array, fillValue, image_array_filled)

    image_filled = sitk.GetImageFromArray(image_array_filled)
    image_filled.CopyInformation(image)

    return image_filled


def changePixelData(image: sitk.Image, templateDicomFolder: str, outpuFolder: str) -> None:
    """Creates a copy of the dicom data of the templateDicomFolder, but where 
    the pixel data/image data is changed with the image data contained in the 
    image

    Parameters
    ----------
    image : sitk.Image
        image to paste into the template dicom files
    templateDicomFolder : str
        folder where containing a template dicom series. Must be on the same
        coordinate grid as the image that we want to paste in.
    outpuFolder : str
        Output folder that we want to write the altered dicom data to.
    """
    # Get slice location for the image
    zdim = image.GetSize()[2]
    # Find slice direction
    sliceAx = np.argmax(np.abs(np.array(image.GetDirection())[-3:]))
    imageSliceLocs = [
        image.TransformIndexToPhysicalPoint([0, 0, z])[sliceAx] for z in range(zdim)
    ]

    dcms = glob.glob(templateDicomFolder + "/**")
    sliceLocs = [dcmread(dcm).SliceLocation for dcm in dcms]
    dcmSliceLocs = zip(sliceLocs, dcms)

    if np.all(np.diff(np.array(imageSliceLocs)) >= 0):
        dcmSliceLocs = sorted(dcmSliceLocs)
    else:
        dcmSliceLocs = sorted(dcmSliceLocs, reverse=True)

    # print(list(zip(dcmSliceLocs, imageSliceLocs)))
    assert np.allclose(
        np.array(dcmSliceLocs)[:,0].astype(float), np.array(imageSliceLocs), rtol=1e-3, atol=1e-2
    ), "Slice locations found not to be similar"
    
    sliceLocs, dcms = list(zip(*dcmSliceLocs))
    
    # print(sliceLocs, dcms)
    imageArr = sitk.GetArrayFromImage(image)

    for i in range(len(dcms)):
        dcm = dcmread(dcms[i])
        # imageSlice = sitk.GetArrayFromImage(imageArr[i])
        dcm.PixelData = imageArr[i].tobytes()
        dcmwrite(os.path.join(outpuFolder, os.path.basename(dcms[i])), dcm)



def main(args):
    pass


if __name__ == "__main__":
    pass
    # main()