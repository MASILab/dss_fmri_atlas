# DSS fMRI Atlas
Diffusion-informed spatial smoothing (DSS) atlas for functional magnetic resonance imaging (fMRI).

There are three options for using the DSS atlas:
1. [Containerized code with singularity (recommended)](#option-1-singularity-container)
2. [Python code](#option-2-python-code)
3. [Pregenerated filter windows](#option-3-pregenerated-filter-windows)

## Option 1: Singularity container
We provide the Python code in a singularity container to apply the filter without setting up the environment.

### Download and installation
**Download the Singularity image `dss_fmri_atlas.sif` from [https://vanderbilt.box.com/s/spyatb6a0yhcxodxkva0ovjz2ktqa1lj](https://vanderbilt.box.com/s/spyatb6a0yhcxodxkva0ovjz2ktqa1lj).**

We used [SingularityCE](https://github.com/sylabs/singularity) version 3.8.1. To use the container, download the image. There are two scripts provided. First, we register the fMRI data to the HCP-YA template. Second, we apply the DSS filter. We provide the scripts separately so that you can apply any preprocessing (regressing out CSF and motion parameters, applying filters to the time series, etc.) in HCP-YA space in between the two steps.

To use a Singularity container, you must bind a directory with your input data to `/INPUTS/` and bind an output directory to `/OUTPUTS/` with the `-B` flag. This allows the Singularity container to interact with your filesystem.

To register the fMRI data to the HCP-YA template (see `singularity exec /path/to/dss_fmri_atlas.sif register_to_template.sh --help`):
```bash
singularity exec -ec \
    -B /path/to/inputs:/INPUTS \
    -B /path/to/outputs:/OUTPUTS \
    /path/to/dss_fmri_atlas.sif register_to_template.sh \
    --input_fmri /INPUTS/fmri.nii.gz \
    --output_fmri /OUTPUTS/fmri_reg_to_template.nii.gz \
    --input_t1w /INPUTS/t1w.nii.gz
```

To apply the DSS filter (see `singularity exec /path/to/dss_fmri?atlas.sif apply_dss_filter.sh --help`):
```bash
singularity exec -ec \
    -B /path/to/inputs:/INPUTS \
    -B /path/to/outputs:/OUTPUTS \
    /path/to/dss_fmri_atlas.sif apply_dss_filter.sh \
    --input_fmri /OUTPUTS/fmri_reg_to_template.nii.gz \
    --output_fmri /OUTPUTS/filtered_fmri.nii.gz \
    --n 5 \
    --alpha 0.9 \
    --beta 50 \
    --n_jobs 15
```

## Option 2: Python code
We provide Python code to efficiently apply the filter in the graph spectral domain.

### Installation
Clone this repo and navigate to the downloaded directory. Use [conda](https://docs.conda.io/en/latest/) to create a Python environment with the specified requirements:

```bash
conda env create --name dss_atlas -f environment.yml
```

Install the dss_atlas package locally using pip:

```bash
pip install .
```

### Download the DSS Atlas files
Saving the individual filter windows is very large and applying the filter directly is computationally expensive. Instead, we provide the files and code to efficiently apply the DSS filter.

**Download the ODFs represented as spherical harmonics `odf_sh.nii.gz`, T1-weighted image `t1w.nii.gz`, and white matter mask `wm_mask.nii.gz` from [https://vanderbilt.box.com/s/spyatb6a0yhcxodxkva0ovjz2ktqa1lj](https://vanderbilt.box.com/s/spyatb6a0yhcxodxkva0ovjz2ktqa1lj).**

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

### Usage
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

## Option 3: Pregenerated filter windows
You can apply the filter windows directly instead of in the graph spectral domain, though this option is very computationally expensive.

**Download the pregenerated filter windows `filt_windows.nii.gz` from [https://vanderbilt.box.com/s/spyatb6a0yhcxodxkva0ovjz2ktqa1lj](https://vanderbilt.box.com/s/spyatb6a0yhcxodxkva0ovjz2ktqa1lj).**

The filter windows were generated using ODFs generated from the [HCP-1065 Young Adult Fiber Template](https://brain.labsolver.org/hcp_template.html) labeled "1.25 mm with ODF". We used $n=5$, $\alpha=0.9$, and $\beta=50$. The filter windows are stored as a 125×151×108×1131 NIFTI file, where 1131 is the flattened filter window. You can reshape the final dimension into an 11×11×11 window centered at each voxel before using the filter. Note that the windows are unnormalized.

The corresponding T1-weighted image is from [http://www.bic.mni.mcgill.ca/~vfonov/icbm/2009](http://www.bic.mni.mcgill.ca/~vfonov/icbm/2009).

The white matter mask was generated using [UNesT](https://github.com/MASILab/UNesT) with labels 40-45.

## Citation
The code is released under the MIT License and the atlas is released under the [WU-Minn HCP Consortium Open Access Data Use Terms](https://www.humanconnectome.org/study/hcp-young-adult/document/wu-minn-hcp-consortium-open-access-data-use-terms). You must acknowledge the following statement:


> Data were provided [in part] by the Human Connectome Project, WU-Minn Consortium (Principal Investigators: David Van Essen and Kamil Ugurbil; 1U54MH091657) funded by the 16 NIH Institutes and Centers that support the NIH Blueprint for Neuroscience Research; and by the McDonnell Center for Systems Neuroscience at Washington University.

If you use the atlas in your research, please cite the following:

DSS Atlas:
> Adam M. Saunders, Gaurav Rudravaram, Nancy R. Newlin, Michael E. Kim, Rose Herdejurgen, Bennett Landman, Yurui Gao. A 4D atlas of diffusion-informed spatial smoothing windows for BOLD signal in white matter. SPIE Medical Imaging 2024 [in preparation].

HCP-1065 Young Adult Template:
> F.C. Yeh. Population-based tract-to-region connectome of the human brain and its hierarchical topology. Nature Communications, 2022. https://doi.org/10.1038/s41467-022-32595-4

