# Huawei Cloud Image Conversion Matrix

## Formats and Commands

| Source Format | Target Format | Official Huawei Conversion Command (`qemu-img`) |
| :--- | :--- | :--- |
| **VMware OVA** | TAR Extract | `tar -xvf image.ova -C extracao_imagem/` |
| **VMware VMDK** | QCOW2 | `qemu-img convert -p -f vmdk -O qcow2 image.vmdk imagem/image.qcow2` |
| **Hyper-V VHD** | QCOW2 | `qemu-img convert -p -f vpc -O qcow2 image.vhd imagem/image.qcow2` |
| **Hyper-V VHDX** | QCOW2 | `qemu-img convert -p -f vhdx -O qcow2 image.vhdx imagem/image.qcow2` |
| **RAW** | QCOW2 | `qemu-img convert -p -f raw -O qcow2 image.raw imagem/image.qcow2` |
| **VirtualBox VDI** | QCOW2 | `qemu-img convert -p -f vdi -O qcow2 image.vdi imagem/image.qcow2` |
| **Any Supported** | ZVHD2 (Huawei) | `./qemu-img-hw convert -p -O zvhd2 image.ext imagem/image.zvhd2` |

## Notes on ZVHD and ZVHD2
- **ZVHD2** is Huawei Cloud's proprietary format optimized for fast I/O and compression.
- It enables **Fast Create (Fast Import)** for disk images up to 1 TiB (1024 GiB).
- Generating ZVHD2 images requires the `qemu-img-hw` binary provided by Huawei Cloud.
