# Step-by-Step Guide: Creating Private Images via Huawei Cloud Console

This guide walks through registering an external image file in the **Huawei Cloud Management Console** after it has been converted, validated, and uploaded to Object Storage Service (OBS).

---

## Console Prerequisites
1. The converted disk image (`.qcow2`, `.raw`, or `.zvhd2`) must already be uploaded to an OBS bucket in your target region (via `scripts/upload_to_obs.py` or the OBS web console).
2. The destination OBS bucket must belong to the **Standard** storage tier.
3. Your IAM user account requires **IMS Administrator** or **Tenant Administrator** permissions.

---

## Step-by-Step Procedure

### 1. Access the IMS Console
1. Log in to the Huawei Cloud Console: [https://console.huaweicloud.com/](https://console.huaweicloud.com/).
2. In the top navigation bar, select the region where your OBS bucket resides (e.g., **SA-Sao Paulo1** / `sa-brazil-1`).
3. Under the service navigation menu, go to **Compute** > **Image Management Service (IMS)**.

---

### 2. Initiate Image Creation
1. In the top-right corner of the IMS page, click **Create Image**.
2. Configure the creation parameters:
   - **Type**: Choose `System disk image` (for OS boot disks) or `Data disk image` (for extra volumes).
   - **Source**: Select **Image File** (external disk file uploaded to OBS).

---

### 3. Select the File in OBS
1. In the **Image File** field:
   - Click **Browse**.
   - Navigate your buckets and select the bucket containing your uploaded image.
   - Choose the target disk image file (e.g., `ubuntu-22.04-prod.qcow2`).
   - The console formats the pointer as `<bucket_name>:<object_key>`.

---

### 4. Configure Operating System Properties
1. **OS**: Select the operating system family (e.g., `Linux` or `Windows`).
2. **OS Version**: Select the exact version matching your guest OS (e.g., `Ubuntu 22.04 server 64bit`, `CentOS 7.9 64bit`, or `Other Linux 64bit`).
3. **Boot Mode**:
   - Select **BIOS** for legacy MBR partitioned disks.
   - Select **UEFI** for GPT partitioned disks containing an EFI System Partition (ESP).
4. **System Disk (Min Disk)**:
   - Enter the minimum required system disk capacity in GB.
   - **Rule**: Must be greater than or equal to the virtual disk size of the image file (minimum 10 GB for Linux, 20 GB for Windows).

---

### 5. Select Creation Mode (Standard vs. Fast Create)
1. **Enable Fast Create**:
   - **Unchecked (Default / Standard Import)**: Recommended for `.qcow2`, `.vmdk`, and `.vhd`. Huawei Cloud runs background driver injection and integrity validation.
   - **Checked (Fast Create)**: Supported **only** for `.raw` and `.zvhd2` formats. Skips driver injection and allows importing disks up to 1 TiB (1024 GiB).

---

### 6. Review and Submit
1. **Name**: Provide a unique identifier for the image (e.g., `Ubuntu-22.04-Base-v1`).
2. **Enterprise Project**: Select your target enterprise project (default is `default`).
3. **Description**: Add useful context (source template, build date, maintainer).
4. Click **Create Now**, review your configuration summary, and click **Submit**.

---

### 7. Monitor Status
1. Navigate back to the **Private Images** tab in IMS.
2. The initial status will be `Creating` or `Queued`.
3. Once background processing completes, the status changes to **Normal** (`active`).
4. You can now click **Apply for Server** to launch new ECS instances directly from this image.
