---
name: ims-pipeline-orchestrator
description: >-
  Use this skill when coordinating and executing the end-to-end pipeline of preparing, converting,
  validating, testing, uploading, and importing an OS image into Huawei Cloud IMS in an automated sequence.
---

# IMS Pipeline Orchestrator Skill

Coordinates the complete end-to-end lifecycle of custom OS images for Huawei Cloud IMS across all preparation and cloud onboarding stages.

## Pipeline Architecture

The orchestrator executes the following stages in order:
1. **Fetch**: `ims-downloader` ([download_image.py](../../../scripts/download_image.py))
2. **Convert**: `ims-extractor-converter` ([extract_and_convert.py](../../../scripts/extract_and_convert.py))
3. **Validate**: `ims-local-validator` ([validate_image.py](../../../scripts/validate_image.py))
4. **Smoke Boot**: `ims-local-validator` ([test_local_boot.py](../../../scripts/test_local_boot.py))
5. **Upload**: `ims-cloud-uploader` ([upload_to_obs.py](../../../scripts/upload_to_obs.py))
6. **Register**: `ims-cloud-importer` ([import_ims_image.py](../../../scripts/import_ims_image.py))

## CLI Usage

### 1. From a Remote Image URL
```bash
python3 scripts/pipeline.py \
    --url "https://cloud-images.ubuntu.com/releases/22.04/release/ubuntu-22.04-server-cloudimg-amd64.img" \
    --format qcow2 \
    --os-type linux
```

### 2. From a Local Image or OVA Template
```bash
python3 scripts/pipeline.py \
    --input "downloads/appliance.ova" \
    --format qcow2 \
    --os-type linux
```

### 3. Dry-Run (Offline Simulation)
```bash
python3 scripts/pipeline.py \
    --input "downloads/appliance.ova" \
    --format qcow2 \
    --dry-run
```

## References
- See the complete workflow flow in [workflow_guide.md](./references/workflow_guide.md).
