---
name: ims-cloud-importer
description: >-
  Use this skill when registering and importing a private image into Huawei Cloud Image Management Service (IMS)
  from an uploaded OBS image file, specifying min_disk, OS version, and tracking the asynchronous creation job.
---

# IMS Cloud Importer Skill

Registers private images in Huawei Cloud Image Management Service (IMS) from OBS objects and tracks the background creation job to completion.

## Usage

Execute [import_ims_image.py](../../../scripts/import_ims_image.py):
```bash
python3 scripts/import_ims_image.py \
    --manifest "imagem/<IMAGE_FILE>.qcow2.obs_upload.json" \
    --name "Ubuntu-22.04-IMS-Custom" \
    --min-disk 40 \
    --os-version "Ubuntu 22.04 server 64bit"
```

To validate request parameters without calling the remote API:
```bash
python3 scripts/import_ims_image.py \
    --manifest "imagem/<IMAGE_FILE>.qcow2.obs_upload.json" \
    --dry-run
```

## Asynchronous Job Tracking
- The IMS API responds with an asynchronous `job_id`.
- The job transitions through `RUNNING` until reaching `SUCCESS`.
- Once finished, the image status becomes `Normal` (`active`) in IMS and is ready for ECS provisioning.

## Manual Portal Registration
- For teams that prefer registering images via the Huawei Cloud Console web UI, follow [manual_portal_creation.md](../../../documentacao/manual_portal_creation.md).

## References
- See API details in [ims_api_specs.md](./references/ims_api_specs.md).
