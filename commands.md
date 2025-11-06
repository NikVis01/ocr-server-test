### Shit that made shit work
1. Make sure u don't have fuckass dumbass nvidia list files in a certain dir that are freaking your ahh:

```bash
sudo rm -f /etc/apt/sources.list.d/nvidia-container-toolkit.list
```

2. Install it properly
```bash
distribution=ubuntu22.04
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

```

```bash
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

