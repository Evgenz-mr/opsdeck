#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 <source-context> <opsdeck-context> <output-kubeconfig>" >&2
  exit 2
fi

OPSDECK_SOURCE_CONTEXT=$1
OPSDECK_TARGET_CONTEXT=$2
OPSDECK_OUTPUT_KUBECONFIG=$3
OPSDECK_TOKEN_DURATION=${OPSDECK_TOKEN_DURATION:-24h}
OPSDECK_TEMP_DIR=$(mktemp -d)
trap 'rm -rf -- "$OPSDECK_TEMP_DIR"' EXIT

OPSDECK_API_SERVER=$(kubectl \
  --context "$OPSDECK_SOURCE_CONTEXT" \
  config view \
  --raw \
  --minify \
  -o jsonpath='{.clusters[0].cluster.server}')

OPSDECK_CA_DATA=$(kubectl \
  --context "$OPSDECK_SOURCE_CONTEXT" \
  config view \
  --raw \
  --minify \
  -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')

if [[ -z "$OPSDECK_API_SERVER" || -z "$OPSDECK_CA_DATA" ]]; then
  echo "The source context must contain an API server and embedded CA data." >&2
  exit 1
fi

OPSDECK_TOKEN=$(kubectl \
  --context "$OPSDECK_SOURCE_CONTEXT" \
  -n opsdeck \
  create token opsdeck \
  --duration "$OPSDECK_TOKEN_DURATION")

mkdir -p "$(dirname "$OPSDECK_OUTPUT_KUBECONFIG")"
printf '%s' "$OPSDECK_CA_DATA" | base64 --decode > "$OPSDECK_TEMP_DIR/ca.crt"

kubectl config set-cluster "$OPSDECK_TARGET_CONTEXT" \
  --server "$OPSDECK_API_SERVER" \
  --certificate-authority "$OPSDECK_TEMP_DIR/ca.crt" \
  --embed-certs=true \
  --kubeconfig "$OPSDECK_OUTPUT_KUBECONFIG"

kubectl config set-credentials "opsdeck-$OPSDECK_TARGET_CONTEXT" \
  --token "$OPSDECK_TOKEN" \
  --kubeconfig "$OPSDECK_OUTPUT_KUBECONFIG"

kubectl config set-context "$OPSDECK_TARGET_CONTEXT" \
  --cluster "$OPSDECK_TARGET_CONTEXT" \
  --user "opsdeck-$OPSDECK_TARGET_CONTEXT" \
  --kubeconfig "$OPSDECK_OUTPUT_KUBECONFIG"

chmod 0400 "$OPSDECK_OUTPUT_KUBECONFIG"
echo "Added read-only context '$OPSDECK_TARGET_CONTEXT' to $OPSDECK_OUTPUT_KUBECONFIG"
echo "Token requested for $OPSDECK_TOKEN_DURATION; actual lifetime may be capped by cluster policy."
