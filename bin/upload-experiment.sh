#!/usr/bin/env bash

peer1=$((8000 + $1))
peer2=$((8000 + $2))

echo "Upload to Node $1 ($peer1)"

cleanup() {
  rm -rf upload.bin download.bin
}

trap 'cleanup' EXIT

echo "Generate file"
dd if=/dev/urandom of=./upload.bin bs=80M count=1

$SECONDS=0
echo "Upload to Node $1"
cid=$(curl -s --data-binary @upload.bin http://localhost:${peer1}/api/codex/v1/data)

echo "Download from Node $2 ($peer2)"
curl -s -o download.bin http://localhost:${peer2}/api/codex/v1/data/${cid}/network

echo "Took $SECONDS seconds"
echo "Upload md5: $(md5sum upload.bin)"
echo "Download md5: $(md5sum download.bin)"
