# DSS fMRI Atlas
Diffusion-informed spatial smoothing (DSS) atlas for functional magnetic resonance imaging (fMRI).

## Installation
Clone this repo and navigate to the downloaded directory. Use [conda](https://docs.conda.io/en/latest/) to create a Python environment with the specified requirements:

```bash
conda env create --name dss_atlas -f environment.yml
```

Install the dss_atlas package locally using pip:

```bash
pip install .
```

## Download the DSS Atlas Files
Saving the individual filter windows is very large and applying the filter directly is computationally expensive. Instead, we provide the files and code to efficiently apply the DSS filter.

**Download the ODFs represented as spherical harmonics, T1-weighted image, and white matter mask from [https://vanderbilt.box.com/s/spyatb6a0yhcxodxkva0ovjz2ktqa1lj](https://vanderbilt.box.com/s/spyatb6a0yhcxodxkva0ovjz2ktqa1lj).**

The ODFs were generated from the [HCP-1065 Young Adult Fiber Template](https://brain.labsolver.org/hcp_template.html) labeled "1.25 mm with ODF". The file is provided as a DSI Studio .fib file, which can be converted using the ```scripts/dsi_convert.py``` (based on [https://github.com/mattcieslak/dmri_convert](https://github.com/mattcieslak/dmri_convert)):

```bash
input_dsi="/path/to/HCP1065.1.25mm.odf.fib"
output_folder="/path/to/output"
odf_nii="$output_folder/odf_sh.nii.gz"
fa_nii="$output_folder/fa.nii.gz"

python dsi_convert.py $input_dsi $fa_nii $odf_nii --sh
```

The corresponding T1-weighted image is from [http://www.bic.mni.mcgill.ca/~vfonov/icbm/2009](http://www.bic.mni.mcgill.ca/~vfonov/icbm/2009).

The white matter mask was generated using [UNesT](https://github.com/MASILab/UNesT) with labels 40-45.

## Usage
To use the filter, see the provided ```apply_dss_filter.py```. Note that the fMRI data should be deformably registered to the T1-weighted template for the HCP atlas.

```bash
data_dir="/path/to/data/dir"
odf_sh="$data_dir/odf_sh.nii.gz"
wm_mask="$data_dir/wm_mask.nii.gz"
input_fmri="$data_dir/fmri_reg_to_hcp.nii.gz"
output_fmri="$data_dir/fmri_filtered.nii.gz"
adj_matrix="$data_dir/adj_matrix_5x5x5_0.9.npz"

# Apply filter
python apply_dss_filter.py \
    --odf_sh $odf_sh \
    --wm_mask $wm_mask \
    --adj_matrix $adj_matrix \
    --fmri_data $input_fmri \
    --output $output_fmri \
    --sh_format tournier \
    --n 5 \
    --alpha 0.9 \
    --beta 50 \
    --n_jobs 15
```

## Citation
The code is released under the MIT License and the atlas is released under the [WU-Minn HCP Consortium Open Access Data Use Terms](https://www.humanconnectome.org/study/hcp-young-adult/document/wu-minn-hcp-consortium-open-access-data-use-terms). You must acknowledge the following statement:


> Data were provided [in part] by the Human Connectome Project, WU-Minn Consortium (Principal Investigators: David Van Essen and Kamil Ugurbil; 1U54MH091657) funded by the 16 NIH Institutes and Centers that support the NIH Blueprint for Neuroscience Research; and by the McDonnell Center for Systems Neuroscience at Washington University.

If you use the atlas in your research, please cite the following:

DSS Atlas:
> Adam M. Saunders, Gaurav Rudravaram, Nancy R. Newlin, Michael E. Kim, Rose Herdejurgen, Bennett Landman, Yurui Gao. A 4D atlas of diffusion-informed spatial smoothing windows for BOLD signal in white matter. SPIE Medical Imaging 2024 [in preparation].

HCP-1065 Young Adult Template:
> F.C. Yeh. Population-based tract-to-region connectome of the human brain and its hierarchical topology. Nature Communications, 2022. https://doi.org/10.1038/s41467-022-32595-4

