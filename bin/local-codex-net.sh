#!/usr/bin/env bash
set -e

# CODEX_PATH=
CODEX_DATA_ROOT=${HOME}/codex-data-root
CODEX_BINARY="${CODEX_PATH}/build/codex"
NODES=3

mkdir -p "${CODEX_DATA_ROOT}"

declare -a PIDS

cleanup() {
  for p in "${PIDS[@]}"; do
    echo "Killing ${p}..."
    kill "${p}" 2>/dev/null
  done
}

terminal() {
    local IFS
    local node_id=$1
    
    shift
    printf -v cmd %q ". ~/.bashrc; set -m; $*"
    gnome-terminal --title "Codex Node $node_id" --geometry 250x30 -- bash -c "bash --rcfile <(echo $cmd)"
    term_pid=$!
}

trap 'cleanup' ERR

for i in $(seq 1 ${NODES}); do
  codex_port=$((8080 + i))
  codex_api_port=$((8000 + i))
  data_dir="${CODEX_DATA_ROOT}/node-${i}"
  logs_dir="${CODEX_DATA_ROOT}/logs"

  mkdir -p "${logs_dir}"
  mkdir -p "${data_dir}"

  export CODEX_LOG_LEVEL="TRACE;warn:discv5,providers,manager,cache;warn:libp2p,multistream,switch,transport,tcptransport,semaphore,asyncstreamwrapper,lpstream,mplex,mplexchannel,noise,bufferstream,mplexcoder,secure,chronosstream,connection,connmanager,websock,ws-session,dialer,muxedupgrade,upgrade,identify"
  
  CODEX_CMD="${CODEX_BINARY} --data-dir=${data_dir} --listen-addrs=/ip4/0.0.0.0/tcp/${codex_port} --api-port=${codex_api_port} --disc-port=$((8090 + i)) --block-ttl=99999999 --block-mi=99999999"

  if [ "${i}" -gt 1 ]; then
    CODEX_CMD="${CODEX_CMD} --bootstrap-node=${bootstrap_spr}"
  fi

  terminal $i "${CODEX_CMD} 2>&1 | tee ${logs_dir}/codex-${i}.log"
  PIDS+=($term_pid)

  echo "Node ${i}: "
  echo " upload: http://localhost:${codex_api_port}/api/codex/v1/data"
  echo " download: http://localhost:${codex_api_port}/api/codex/v1/data/{cid}/network"

  if [ "${i}" -eq 1 ]; then
    sleep 5
    bootstrap_spr=$(curl -s localhost:${codex_api_port}/api/codex/v1/debug/info | jq .spr --raw-output)
  fi

  echo $bootstrap_spr

  if [ -z "${bootstrap_spr}" ]; then
    echo "Failed to get bootstrap SPR"
    exit 1
  else
    echo "Bootstrap SPR is ${bootstrap_spr}"
  fi
done

