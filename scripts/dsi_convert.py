# Conversion tool from DSI .fib file to NIFTI format
# Based on https://github.com/mattcieslak/dmri_convert
import argparse
import numpy as np
import os
import os.path as op
import nibabel as nb
from dipy.core.geometry import cart2sphere
from dipy.core.sphere import HemiSphere
from dipy.direction import peak_directions
import subprocess
from scipy.io.matlab import loadmat, savemat
from tqdm import tqdm
import re
from adam_utils.nifti import reorient_to_ras

def popen_run(arg_list):
    cmd = subprocess.Popen(arg_list, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    out, err = cmd.communicate()
    print(out)
    print(err)


def dsistudio_to_mrtrix(fib_file, fa_file, odf_file, odf_type, dir_file=None, lps=False, odf_verts=None, odf_faces=None):
    """Convert a DSI Studio fib file to NIFTI.

    Parameters:
    ============

    fib_file : str
        Path to a (decompressed) fib file
    fa_file : str
        Path to output nifti file that contains the FA values
    odf_file : str
        File name for the output ODF file that will be created.
    odf_type : str
        How to represent ODF along last dimension. Either 'amp' for amplitudes
        or 'sh' for spherical harmonics
    dir_file : str
        File name for the output text file that contains the directions of the
        ODFs. If None, no file will be created.
    lps : bool
        If True, the output ODF file will be in LPS space. Otherwise, it will be RAS. 
        (only works for --odf_type amp)
    odf_verts : str
        Output ODF vertices (.npy)
    odf_faces : str
        Output ODF faces (.npy)
    """
    if dir_file is None:
        dir_file = "directions.txt"
    
    fibmat = loadmat(fib_file)
    print(fibmat.keys())
    dims = tuple(fibmat['dimension'].squeeze())
    directions = fibmat['odf_vertices'].T
    faces = fibmat['odf_faces'].T

    if odf_faces is not None:
        np.save(odf_faces, faces)
    if odf_verts is not None:
        np.save(odf_verts, directions)

    # Create NIFTI with correct spatial mapping (FA in LPS orientation)
    # Reshape the FA to the original image size 
    image_size = tuple(fibmat['dimension'][0])
    fa_data = np.reshape(fibmat['dti_fa'], image_size, order='F')

    # Find affine and save in LPS space
    try:
        affine = fibmat['trans']
    except KeyError:
        affine = np.eye(4)
    fa = nb.Nifti1Image(fa_data, affine) 

    # Save FA file in RAS space
    fa_ras = reorient_to_ras(fa)
    if lps:
        fa.to_filename(fa_file)
    else:
        fa_ras.to_filename(fa_file)

    odf_vars = [k for k in fibmat.keys() if re.match("odf\\d+", k)]

    valid_odfs = []
    print(fibmat['dti_fa'].shape)
    flat_mask = (fibmat["dti_fa"].squeeze() > 0).flatten(order='F')
    n_voxels = np.prod(dims)
    for n in range(len(odf_vars)):
        varname = "odf%d" % n
        odfs = fibmat[varname]
        odf_sum = odfs.sum(0)
        odf_sum_mask = odf_sum > 0
        valid_odfs.append(odfs[:, odf_sum_mask].T)
    odf_array = np.row_stack(valid_odfs)
    odf_array = odf_array - odf_array.min(0)
    print('ODF array shape: ', odf_array.shape, n_voxels, flat_mask.shape)

    # Convert each column to a 3d file, then concatenate them
    odfs_3d = []
    for odf_vals in odf_array.T:
        new_data = np.zeros(n_voxels, dtype=np.float64)
        new_data[flat_mask] = odf_vals
        odfs_3d.append(new_data.reshape(dims, order="F"))

    # real_img = nb.load(source_nifti_file)
    real_img = fa
    odf4d = np.stack(odfs_3d, -1)

    # Find distances
    num_dirs, _ = directions.shape
    hemisphere = num_dirs // 2
    x, y, z = directions[:hemisphere].T
    _, theta, phi = cart2sphere(-x, -y, z)

    # Subtract min distance along each ODF from ODFs
    odf4d = odf4d - odf4d.min(-1, keepdims=True)    

    odf4d_img = nb.Nifti1Image(odf4d, real_img.affine)

    # if not lps:
    #     odf4d_img = reorient_to_ras(odf4d_img)

    if odf_type == "amp":
        if not lps:
            odf4d_img = reorient_to_ras(odf4d_img)
        odf4d_img.to_filename(odf_file)
        return

    odf4d_img = reorient_to_ras(odf4d_img)
    odf4d_img.to_filename("odf_values.nii")

    np.savetxt(dir_file, np.column_stack([phi, theta]))

    popen_run(["amp2sh", "-force", "-directions", dir_file, "odf_values.nii", odf_file, "-nthreads", "19"])

    if lps:
        _, theta, phi = cart2sphere(x, y, z)
        np.savetxt(dir_file, np.column_stack([phi, theta]))

    if dir_file == "directions.txt":
        os.remove("directions.txt")
    os.remove("odf_values.nii")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=(
            'Convert DSI .fib file to NIFTI format.'
            'Code modified from https://github.com/mattcieslak/dmri_convert'
        )
    )

    parser.add_argument('input', help='Input .fib file', type=str)
    parser.add_argument('fa_file', help='Output FA .nii.gz file', type=str)
    parser.add_argument('odf_file', help='Output ODF file (NIFTI only for amp, any mrtrix compatible file for sh)', type=str)
    parser.add_argument('--dir_file', help='Output directions .txt file', type=str)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--amp', help='Output ODFs as amplitude', action='store_true')
    group.add_argument('--sh', help='Output ODFs as spherical harmonics', action='store_true')
    parser.add_argument('--lps', help='Output ODFs in LPS space', action='store_true')
    parser.add_argument('--odf_verts', help='Output ODF vertices (.npy)', type=str)
    parser.add_argument('--odf_faces', help='Output ODF faces (.npy)', type=str)

    args = parser.parse_args()

    # Run conversion
    dsistudio_to_mrtrix(args.input, args.fa_file, args.odf_file, 'amp' if args.amp else 'sh',
        args.dir_file, args.lps, args.odf_verts, args.odf_faces)
