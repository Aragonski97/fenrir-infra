sudo tailscale login

export TSC_IP=$(tailscale ip | awk 'FNR == 1 {print}')
export TSC_IP_BASE=$(tailscale ip | awk 'NR==1' | grep -oP '^\d+\.\d+')
export FENRIR_DOCKER_NETWORK=$(hostname)-network
export FENRIR_ROOT_DIR=$(dirname $(pwd))
