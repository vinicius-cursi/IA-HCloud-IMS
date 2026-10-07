---
name: ims-cloud-uploader
description: >-
  Use this skill when uploading validated disk images to Huawei Cloud Object Storage Service (OBS)
  standard buckets using internal environment variables and obsutil CLI or Python SDK.
---

# IMS Cloud Uploader Skill

Uploads validated disk images to Huawei Cloud Object Storage Service (OBS) with multipart concurrency, checksum verification, and resume capability.

## Environment Variables

Load environment variables before triggering the upload:
```bash
source scripts/huawei_env.sh
```

Supported variables:
- `HWC_AK` or `HUAWEI_AK`: IAM Access Key ID
- `HWC_SK` or `HUAWEI_SK`: IAM Secret Access Key
- `HWC_REGION` or `HUAWEI_REGION`: Target region (e.g., `sa-brazil-1`)
- `HWC_OBS_BUCKET` or `OBS_BUCKET`: Target Standard storage bucket
- `HWC_OBS_ENDPOINT` or `OBS_ENDPOINT`: Regional OBS endpoint

## Usage

Execute [upload_to_obs.py](../../../scripts/upload_to_obs.py):
```bash
python3 scripts/upload_to_obs.py \
    --image "imagem/<IMAGE_FILE>.qcow2"
```

To test variables and connectivity without transferring data:
```bash
python3 scripts/upload_to_obs.py \
    --image "imagem/<IMAGE_FILE>.qcow2" \
    --dry-run
```

## Generated Manifest
- Saves `<image_file>.obs_upload.json` containing the exact `ims_image_url` string required by IMS: `<bucket_name>:<object_name>`.

## References
- See technical details in [obs_upload_specs.md](./references/obs_upload_specs.md).
