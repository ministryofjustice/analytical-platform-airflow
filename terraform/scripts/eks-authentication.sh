#!/usr/bin/env bash

aws eks get-token --cluster-name "${EKS_CLUSTER_NAME}"
