# Troubleshooting Guide - Huawei Cloud IMS

Common issues encountered when preparing and importing images, and how to fix them.

---

## 1. `qemu-img: command not found`
- **Root Cause**: `qemu-utils` package is not installed on the host.
- **Resolution**: Run the workspace dependency bootstrap:
  ```bash
  ./scripts/setup_prerequisites.sh
  ```
  Or install via apt:
  ```bash
  sudo apt-get update && sudo apt-get install -y qemu-utils
  ```

---

## 2. ECS Instance Boots into `Kernel Panic`
- **Root Cause**: The Linux kernel is missing `virtio_blk` or `virtio_net` drivers in its initramfs.
- **Resolution**:
  - Boot the template VM and rebuild the ramdisk:
    - Debian/Ubuntu: `echo virtio_blk >> /etc/initramfs-tools/modules && update-initramfs -u`
    - RHEL/CentOS: `dracut -f -v --add-drivers "virtio_blk virtio_net"`
  - Verify with `scripts/test_local_boot.py` before re-uploading.

---

## 3. `Failed to mount /sysroot` or `Emergency Mode` on Boot
- **Root Cause**: `/etc/fstab` contains hardcoded device node paths (such as `/dev/sda1`). In KVM, the controller assigns `/dev/vda1`.
- **Resolution**:
  - Run `blkid` inside the VM.
  - Update all mount points in `/etc/fstab` to use `UUID=...` or `LABEL=...`.

---

## 4. `Image file must contain only one disk`
- **Root Cause**: The OVA package contains multiple VMDK disks, or a data volume was included in the export.
- **Resolution**:
  - `scripts/extract_and_convert.py` automatically flags multi-disk templates.
  - Pass `--disk-index 0` to isolate the system disk, and import secondary disks separately as Data Disk Images.

---

## 5. `Fast Create is only supported for RAW and ZVHD2`
- **Root Cause**: Fast Create was enabled for a `.qcow2` or `.vmdk` image.
- **Resolution**:
  - Uncheck `Enable Fast Create` in the console to use Standard import (up to 128 GiB).
  - Alternatively, convert to `.raw` via `scripts/extract_and_convert.py --format raw` to support Fast Create up to 1 TiB.

---

## 6. `The OBS bucket region does not match the IMS region`
- **Root Cause**: The OBS bucket and the target IMS service reside in different regions (e.g., bucket in `sa-brazil-1` while IMS is opened in `la-south-2`).
- **Resolution**:
  - Ensure your OBS bucket is in the exact same region as IMS, and set `export HWC_REGION="<your-region>"`.
