---
name: ims-extractor-converter
description: >-
  Use this skill when unpacking archive containers (.ova, .tar, .zip) and converting virtual disk images
  (VMDK, VHD, VHDX, RAW, VDI, QCOW2) to Huawei Cloud IMS compatible formats (QCOW2, RAW, ZVHD2),
  enforcing the Huawei Cloud single-disk constraint.
---

# IMS Extractor & Converter Skill

Unpacks incoming image containers, identifies virtual disk files, enforces Huawei Cloud's single-disk policy, and converts disks to KVM-optimized formats.

## Huawei Cloud IMS Constraints

> [!IMPORTANT]
> **Single Disk Constraint**: System disk images imported into Huawei Cloud must contain **only ONE virtual disk**. If an OVA or template has multiple VMDK files, split them: convert the primary disk as the System Disk Image, and process subsequent disks as Data Disk Images.

> [!TIP]
> **VHD Format Flag**: When converting `.vhd` images with `qemu-img`, specify `-f vpc` as required by Huawei Cloud specifications.

## Usage

1. **Run Extraction & Conversion**:
   Execute [extract_and_convert.py](../../../scripts/extract_and_convert.py):
   ```bash
   python3 scripts/extract_and_convert.py \
       --input "downloads/<IMAGE_FILE>" \
       --extract-dir "extracted_images" \
       --output-dir "images" \
       --format "qcow2"
   ```

2. **Options**:
   - Enable QCOW2 compression: `--compress`
   - Select disk index from multi-disk templates: `--disk-index <N>`
   - Target Fast Import format: `--format raw` or `--format zvhd2` (requires `qemu-img-hw`)

3. **Output Artifacts**:
   - Converted image: `images/<image_name>.<format>`
   - Technical manifest: `images/<image_name>.<format>.json`

## References
- See the complete matrix in [formats_and_conversions.md](./references/formats_and_conversions.md).
