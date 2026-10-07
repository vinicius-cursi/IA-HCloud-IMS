---
name: ims-local-validator
description: >-
  Use this skill when validating converted disk images against Huawei Cloud IMS requirements
  (single disk, size constraints, MBR/GPT boot modes, Cloud-Init, VirtIO drivers, fstab UUIDs)
  and running local headless QEMU VirtIO boot smoke tests before cloud upload.
---

# IMS Local Validator Skill

Performs automated pre-flight quality assurance and compatibility testing on converted disk images prior to cloud transfer.

## 1. Static Compliance Checks

Run the validator script [validate_image.py](../../../scripts/validate_image.py):
```bash
python3 scripts/validate_image.py \
    --image "images/<IMAGE_FILE>.qcow2" \
    --os-type linux \
    --boot-mode bios
```

Checked criteria:
- **Single Disk**: Verifies disk count and structure.
- **Disk Boundaries**: Linux between 10 GB and 1024 GB; Windows between 20 GB and 1024 GB.
- **Format Integrity**: Validates magic signatures (`QFI\xfb` for QCOW2).
- **Boot Mode**: Ensures partition table scheme (MBR vs GPT) matches requested firmware type.
- **Guest OS Requirements**: VirtIO modules, Cloud-Init, UUIDs in fstab, and dynamic DHCP networking.

## 2. Dynamic Local Smoke Boot (Huawei ECS Simulation)

Run the non-destructive headless boot smoke test using [test_local_boot.py](../../../scripts/test_local_boot.py):
```bash
python3 scripts/test_local_boot.py \
    --image "images/<IMAGE_FILE>.qcow2" \
    --timeout 30 \
    --memory 2048
```

> [!TIP]
> The test runs QEMU with **`snapshot=on`**, ensuring the master image is left untouched while verifying that the kernel initializes VirtIO block/network controllers without panicking.

## References
- See the complete guest configuration checklist in [os_requirements_checklist.md](./references/os_requirements_checklist.md).
