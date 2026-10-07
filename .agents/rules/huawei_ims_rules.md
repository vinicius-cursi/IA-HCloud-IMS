# Cloud Engineering Rules - Huawei Cloud IMS

1. **Single Disk Constraint**:
   - System disk images imported into Huawei Cloud IMS must contain exactly one virtual disk. Packages with multiple VMDK/VHD files must be split: import the first disk as the System Disk Image, and import secondary disks separately as Data Disk Images.

2. **VirtIO Kernel Drivers**:
   - Huawei Cloud ECS runs on KVM hypervisors. Guest operating systems must have `virtio_blk`, `virtio_net`, `virtio_pci`, and `virtio_ring` modules embedded in the kernel or initramfs/dracut to prevent fatal boot panics.

3. **Filesystem Mounts in `/etc/fstab`**:
   - All filesystem mount definitions must use `UUID=` or `LABEL=`. Static paths like `/dev/sda1` or `/dev/vda1` will cause emergency mode drops during ECS boot.

4. **Cloud-Init Metadata Injection**:
   - Linux images must have `cloud-init` active on boot to handle dynamic root password assignment, SSH public key injection, and initial networking setup. Windows images must have `Cloudbase-Init` installed.

5. **Security & Storage Governance (OBS & IAM)**:
   - Secret keys (`HWC_AK`, `HWC_SK`, `HUAWEI_AK`, `HUAWEI_SK`) must never be written to tracked files. They must be injected through session environment variables.
   - The destination OBS bucket must be Standard storage class and must reside in the exact same region as the target IMS service.
