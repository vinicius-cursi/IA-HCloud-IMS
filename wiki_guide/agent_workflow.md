# Agent Execution Flow & Workspace Lifecycle

How the Antigravity agent navigates and operates inside this workspace.

---

## 1. Skill Discovery & Progressive Disclosure

Antigravity uses progressive disclosure to keep the context clean:
- The agent reads top-level skill descriptions from `SKILL.md` frontmatter in `.agents/skills/`.
- When an objective requires a specific task (such as inspecting an OVA or converting to QCOW2), the agent activates the relevant skill and references the detailed documentation under `references/`.

---

## 2. Data Flow Pipeline

```text
[External Image / URL]
       │
       ▼ (ims-downloader)
  downloads/                  <-- Raw archive + integrity JSON manifest
       │
       ▼ (ims-extractor-converter)
  extracted_images/            <-- Unpacked components; enforces single-disk rule
       │
       ▼ (qemu-img / qemu-img-hw)
  images/                     <-- Clean converted image (.qcow2, .raw, .zvhd2)
       │
       ├─► (ims-local-validator) --> validate_image.py (Static compliance checks)
       │
       ├─► (ims-local-validator) --> test_local_boot.py (Headless QEMU VirtIO smoke boot)
       │
       ▼ (ims-cloud-uploader)
  [Huawei Cloud OBS Bucket]   <-- Multipart upload with obsutil
       │
       ▼ (ims-cloud-importer)
  [Huawei Cloud IMS Service]  <-- Private image registration
```

---

## 3. Decision Matrix

When handling an incoming image, the agent executes the following logic:

1. **Source Location**:
   - Remote URL: Invokes `ims-downloader`. Awaits complete transfer and checksum validation.
   - Local path: Confirms file presence in `downloads/`.

2. **Package Format**:
   - If `.ova`, `.tar`, or `.zip`:
     - Unpacks files into `extracted_images/`.
     - Inspects disk count.
     - **If more than 1 disk is detected**: Warns the user and isolates the primary system disk (index 0).
   - If standalone disk (`.vmdk`, `.vhd`, `.vhdx`, `.raw`, `.qcow2`): Proceeds directly to conversion.

3. **Target Format Selection**:
   - Virtual disk < 128 GB: Converts to `qcow2`.
   - Fast Import target (up to 1 TiB): Converts to `raw` or `zvhd2`.

4. **Pre-Flight Validation**:
   - Runs `validate_image.py`.
   - On failure: Halts execution immediately and reports actionable fixes (missing VirtIO drivers, hardcoded fstab device names).
   - On pass: Runs non-destructive local boot test via `test_local_boot.py`.

5. **Upload & Registration**:
   - Confirms `HWC_AK`/`HUAWEI_AK`, `HWC_SK`/`HUAWEI_SK`, and `HWC_OBS_BUCKET` are set.
   - Executes multipart upload to OBS.
   - Generates registration metadata for automated API submission or manual console creation.
