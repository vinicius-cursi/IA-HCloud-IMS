# OBS Upload Specifications for Huawei Cloud IMS

## Storage Class & Regional Governance

1. **Storage Class**: The OBS bucket must use the **Standard** tier. Warm or Cold/Archive tiers cannot be imported by IMS.
2. **Region Matching**: The bucket must reside in the exact same region where the private image is registered. Cross-region image creation via OBS pointers is not supported.
3. **Pointers Syntax (`image_url`)**:
   - The required format for IMS API calls and console input is:
     `<bucket_name>:<object_key>` (separated by a colon).
   - Example: `brsp01sharimg01:ubuntu-22.04.qcow2`.
4. **Performance with `obsutil`**:
   - `obsutil` splits images into 50–100 MB parts and uploads concurrently (`-j=5`), reducing transfer time and enabling resumable recovery on flaky networks.
