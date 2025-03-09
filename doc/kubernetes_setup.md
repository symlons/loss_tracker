# Kubernetes Installation Guide

## Prerequisites Setup

### 1. System Updates and Required Packages
```bash
# Update system packages
apt-get update && apt-get upgrade

# Install required packages
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common
```

### 2. Kernel Configuration
```bash
# Load required kernel modules
modprobe overlay
modprobe br_netfilter

# Configure sysctl parameters
cat <<EOF | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf
net.bridge.bridge-nf-call-iptables  = 1
net.ipv4.ip_forward                 = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF

# Apply sysctl parameters
sysctl --system
```

## Installation Options

### Option A: Traditional Kubernetes Setup

#### 1. Install containerd
```bash
# Install containerd
apt-get update
apt-get install -y containerd.io

# Configure containerd
mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
systemctl restart containerd
```

#### 2. Install kubectl
```bash
# Add Kubernetes repository
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-archive-keyring.gpg

echo "deb [signed-by=/etc/apt/keyrings/kubernetes-archive-keyring.gpg] \
    https://apt.kubernetes.io/ kubernetes-xenial main" | \
    sudo tee /etc/apt/sources.list.d/kubernetes.list

# Install kubectl
apt-get update
apt-get install -y kubectl
```

### Option B: Lightweight K3s Setup

#### Install K3s
```bash
# Install K3s
curl -sfL https://get.k3s.io | sh -

# Verify installation
kubectl get nodes
```
