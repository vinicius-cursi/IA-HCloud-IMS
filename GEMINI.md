# Project Guidelines - Huawei Cloud IMS Image Factory

See [AGENTS.md](file:///home/viniciuscursi/Documents/Projetos/IMS_Huawei_Image/AGENTS.md) for full architecture context and cloud engineering standards.

## Execution Directives
- Fetch remote images with [download_image.py](file:///home/viniciuscursi/Documents/Projetos/IMS_Huawei_Image/scripts/download_image.py).
- Unpack and convert images using [extract_and_convert.py](file:///home/viniciuscursi/Documents/Projetos/IMS_Huawei_Image/scripts/extract_and_convert.py), strictly enforcing the single-disk policy.
- Run pre-upload compliance checks with [validate_image.py](file:///home/viniciuscursi/Documents/Projetos/IMS_Huawei_Image/scripts/validate_image.py) and local smoke boot validation with [test_local_boot.py](file:///home/viniciuscursi/Documents/Projetos/IMS_Huawei_Image/scripts/test_local_boot.py).
- Upload to OBS using [upload_to_obs.py](file:///home/viniciuscursi/Documents/Projetos/IMS_Huawei_Image/scripts/upload_to_obs.py) backed by `HWC_*` or `HUAWEI_*` environment variables.
- Register private images in IMS using [import_ims_image.py](file:///home/viniciuscursi/Documents/Projetos/IMS_Huawei_Image/scripts/import_ims_image.py) or follow the manual console guide.
- Orchestrate the complete end-to-end pipeline through [pipeline.py](file:///home/viniciuscursi/Documents/Projetos/IMS_Huawei_Image/scripts/pipeline.py).
