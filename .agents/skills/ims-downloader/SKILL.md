---
name: ims-downloader
description: >-
  Use this skill when downloading operating system image files (.ova, .qcow2, .vmdk, .raw, .tar.gz)
  from remote URLs into the workspace downloads/ directory with resumable transfers, progress tracking,
  and SHA256/MD5 checksum verification.
---

# IMS Downloader Skill

Downloads OS image files from remote HTTP/HTTPS endpoints with automatic resume support, transfer speed monitoring, and cryptographic checksum validation.

## Workflow

1. **Parameters & Target Path**:
   - Source URL.
   - Optional expected checksum (SHA-256 or MD5).
   - Target folder: `downloads/`.

2. **Execute Download**:
   Run [download_image.py](../../../scripts/download_image.py):
   ```bash
   python3 scripts/download_image.py \
       --url "<IMAGE_URL>" \
       --output-dir "downloads" \
       --algo sha256 \
       --checksum "<OPTIONAL_HASH>"
   ```

3. **Validation & Output**:
   - The file is saved in `downloads/`.
   - A companion JSON manifest (`<filename>.json`) is generated with total bytes, hash value, and completion timestamp.
   - If interrupted, re-running the command resumes transfer from the last byte.

4. **Next Step**:
   - Once verified, invoke `ims-extractor-converter` pointing to the downloaded image.

## References
- See technical details in [download_specs.md](./references/download_specs.md).
