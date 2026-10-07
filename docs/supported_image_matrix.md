# Supported Image Formats & Huawei IMS Recommendations

Reference matrix of all virtual disk and image formats supported by this repository.

---

## Conversion & Compatibility Matrix

| Source Format | File Extension | Pipeline Action | Recommended Output Format | Fast Create Supported? |
| :--- | :--- | :--- | :--- | :--- |
| **VMware OVA** | `.ova` | Extract TAR, isolate system disk, discard extra | `qcow2` | Yes (if converted to RAW/ZVHD2) |
| **VMware VMDK** | `.vmdk` | Convert via `qemu-img` | `qcow2` | No (Standard import <= 128 GB) |
| **QEMU QCOW2** | `.qcow2` | Validate directly / compress | `qcow2` | No (Standard import <= 128 GB) |
| **Raw Disk** | `.raw`, `.img` | Direct validation / convert | `raw` or `qcow2` | **Yes** (RAW up to 1 TiB) |
| **Hyper-V VHD** | `.vhd` | Convert via `qemu-img -f vpc` | `qcow2` | No (Standard import <= 128 GB) |
| **Hyper-V VHDX** | `.vhdx` | Convert via `qemu-img -f vhdx` | `qcow2` | No (Standard import <= 128 GB) |
| **Huawei ZVHD2**| `.zvhd2`| Optimized via `qemu-img-hw` | `zvhd2` | **Yes** (ZVHD2 up to 1 TiB) |
| **VirtualBox VDI**| `.vdi` | Convert via `qemu-img -f vdi` | `qcow2` | No (Standard import <= 128 GB) |
| **QED / QCOW** | `.qed`, `.qcow` | Legacy convert | `qcow2` | No (Standard import <= 128 GB) |

---

## Senior Engineering Recommendations
1. **For images under 128 GB virtual size**:
   - Target **QCOW2** (`--format qcow2`).
   - Sparse allocation (thin provisioning) keeps upload payloads small. Huawei Cloud handles background driver injection automatically.
2. **For images over 128 GB (up to 1 TiB)**:
   - Target **RAW** or **ZVHD2** with Fast Create (`--format raw` or `--format zvhd2`).
   - The guest OS MUST have VirtIO drivers pre-installed since Fast Create skips cloud-side driver injection.
