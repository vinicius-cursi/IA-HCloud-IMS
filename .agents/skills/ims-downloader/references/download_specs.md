# Download Specifications for Huawei Cloud IMS Images

## Network & Integrity Requirements

1. **Supported Protocols**: HTTP and HTTPS.
2. **Byte-Range Resume**: Downloads support HTTP byte-range headers (`Range: bytes=X-`) to resume failed transfers for large images (typically 1 GB to 50 GB).
3. **Integrity Hashing**:
   - `SHA-256`: Recommended standard hash.
   - `MD5`: Supported for legacy mirrors.
4. **Storage Rules**:
   - Raw incoming archives reside in `downloads/`.
   - Temporary chunks are tracked during active downloads and finalized upon successful completion.
