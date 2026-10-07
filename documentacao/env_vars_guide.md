# Environment Variables & IAM Permissions Guide

In accordance with 12-factor cloud engineering best practices, no sensitive credentials are ever committed to source control. This project reads configuration directly from environment variables.

---

## 1. Environment Variables Reference

| Variable | Description | Example | Required |
| :--- | :--- | :--- | :--- |
| `HWC_AK` / `HUAWEI_AK` | IAM Access Key ID | `MOS7J38XND9EXAMPLE` | **Yes** (for uploads & API) |
| `HWC_SK` / `HUAWEI_SK` | IAM Secret Access Key | `W1z2x3Y4z5A6B7c8D9EXAMPLE` | **Yes** (for uploads & API) |
| `HWC_REGION` / `HUAWEI_REGION` | Target Huawei Cloud Region | `sa-brazil-1` | Optional (default: `sa-brazil-1`) |
| `HWC_PROJECT_ID` / `HUAWEI_PROJECT_ID` | Regional IAM Project ID | `0c4f83b129840a1b...` | For direct API calls only |
| `HWC_OBS_BUCKET` / `OBS_BUCKET` | Standard OBS Bucket Name | `my-ims-bucket` | **Yes** (for OBS upload) |
| `HWC_OBS_ENDPOINT` / `OBS_ENDPOINT` | Regional OBS Endpoint URL | `https://obs.sa-brazil-1.myhuaweicloud.com` | Optional (auto-derived) |
| `IMS_IMAGE_NAME` | Default image name in IMS | `Ubuntu-22.04-Automated` | Optional |
| `IMS_MIN_DISK` | Minimum disk size in GB | `40` | Optional (default: 40) |

---

## 2. Session Configuration

Copy the template to create your local environment file:
```bash
cp scripts/huawei_env.sh.example scripts/huawei_env.sh
chmod 600 scripts/huawei_env.sh
nano scripts/huawei_env.sh
```

Load the variables into your current shell session:
```bash
source scripts/huawei_env.sh
```

Verify that variables are active:
```bash
echo "Region: $HWC_REGION"
echo "Bucket: $HWC_OBS_BUCKET"
```

---

## 3. How to Generate AK/SK in Huawei Cloud

1. Log in to the Huawei Cloud Console.
2. In the upper-right corner, hover over your username and select **My Credentials**.
3. In the left navigation menu, click **Access Keys**.
4. Click **Create Access Key**.
5. Complete the SMS/email verification challenge.
6. Download the `credentials.csv` file immediately (the secret key is only displayed once).

---

## 4. Minimum IAM Permissions

The IAM user or user group associated with `HWC_AK` requires:
- **OBS Administrator** (or custom policy with `obs:object:PutObject`, `obs:bucket:ListBucket`).
- **IMS Administrator** (for `ims:images:create`, `ims:jobs:get`).
- **Server Administrator** (if automating subsequent ECS provisioning).
