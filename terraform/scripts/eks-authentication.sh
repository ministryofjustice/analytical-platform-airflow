#!/usr/bin/env bash

EKS_CLUSTER_NAME="${1}"

aws eks get-token --cluster-name "${EKS_CLUSTER_NAME}"
