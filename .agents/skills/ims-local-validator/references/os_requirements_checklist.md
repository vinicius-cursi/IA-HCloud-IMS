# Guest OS Preparation Checklist for Huawei Cloud IMS

## Critical Linux Requirements

1. **VirtIO KVM Drivers**:
   - Required kernel modules: `virtio_blk`, `virtio_net`, `virtio_pci`, `virtio_ring`.
   - RHEL/CentOS verification:
     `lsinitrd /boot/initramfs-$(uname -r).img | grep virtio`
   - Debian/Ubuntu verification:
     `lsinitramfs /boot/initrd.img-$(uname -r) | grep virtio`
   - If missing, add modules to `/etc/dracut.conf` or `/etc/initramfs-tools/modules` and rebuild initramfs.

2. **Cloud-Init Configuration**:
   - Install and enable:
     `systemctl enable cloud-init cloud-init-local cloud-config cloud-final`
   - Handles password setting, SSH key injection, and initial networking on ECS instantiation.

3. **Storage Identifiers (`/etc/fstab`)**:
   - **MANDATORY**: Mount all filesystems by **UUID** or **LABEL**.
   - **DO NOT USE**: Device paths like `/dev/sda1`. Storage controllers change to `/dev/vda1` on KVM.

4. **Network Settings**:
   - Configure all network interfaces for DHCP.
   - Remove persistent udev MAC rules:
     `rm -f /etc/udev/rules.d/70-persistent-net.rules`
     `sed -i '/HWADDR/d' /etc/sysconfig/network-scripts/ifcfg-eth*`
