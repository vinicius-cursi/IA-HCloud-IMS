# Local Testing & KVM Simulation Guide

Why and how we smoke-test images locally before committing network bandwidth and cloud resources.

---

## 1. Why Test Locally?
- Uploading 5 GB to 50 GB images takes network time and consumes object storage capacity.
- Registering an image with missing VirtIO modules or a bad `/etc/fstab` causes instantiated ECS servers to fail at boot (Kernel Panic, Emergency Mode, or missing network interfaces).
- Local testing emulates the exact virtual hardware topology that Huawei Cloud ECS exposes to virtual machines.

---

## 2. Emulation Mechanics

`scripts/test_local_boot.py` launches a headless **QEMU** instance configured as follows:

```bash
qemu-system-x86_64 \
    -m 2048 \
    -smp 2 \
    -machine q35,accel=kvm \
    -drive file=imagem/server.qcow2,if=virtio,format=qcow2,snapshot=on \
    -net nic,model=virtio \
    -net user \
    -nographic \
    -serial file:imagem/server.qcow2.boot_test.log \
    -no-reboot
```

### Key Parameters:
1. **`if=virtio`**: Attaches the disk as a VirtIO block device (identical to `/dev/vda` in Huawei Cloud). If the guest kernel lacks `virtio_blk`, it panics immediately.
2. **`model=virtio`**: Attaches the network interface using VirtIO Net drivers.
3. **`snapshot=on`**: All runtime writes are redirected to a temporary copy-on-write overlay and **discarded upon shutdown**. The master converted image remains 100% clean.
4. **Serial Console Logging (`-serial file:...`)**: Captures kernel messages and systemd status lines for automated parsing.

---

## 3. Interpreting Test Output

- **Success Markers**:
  - `login:` or OS release banner
  - `Reached target Multi-User System`
  - `Started OpenSSH Server`
  - `Cloud-init`
- **Failure Markers**:
  - `Kernel panic - not syncing: VFS: Unable to mount root fs` -> Missing VirtIO modules in initramfs!
  - `Entering emergency mode` -> `/etc/fstab` specifies non-existent `/dev/sda` paths!
  - `Failed to mount /sysroot` -> Dracut initqueue failure!
