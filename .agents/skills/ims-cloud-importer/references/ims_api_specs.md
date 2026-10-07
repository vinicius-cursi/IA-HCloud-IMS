# Huawei Cloud IMS API Reference

## Create Image Endpoint & Parameters

- **Method**: `POST`
- **URI**: `https://ims.{region}.myhuaweicloud.com/v2/cloudimages/action`

### JSON Request Payload
```json
{
  "name": "Ubuntu-22.04-Server-Prod",
  "description": "Custom image imported via Antigravity image pipeline",
  "image_url": "brsp01sharimg01:ubuntu-22.04.qcow2",
  "os_version": "Ubuntu 22.04 server 64bit",
  "min_disk": 40,
  "is_quick_import": false,
  "tags": [
    "environment:production",
    "managed-by:antigravity"
  ]
}
```

### Parameter Constraints
- **`min_disk`**: Required. Linux: 10–1024 GB. Windows: 20–1024 GB. Must be >= virtual disk size.
- **`is_quick_import`**: Set to `true` only for RAW or ZVHD2 images configured for Fast Create.
- **`image_url`**: Formatted as `<bucket_name>:<object_key>`.
