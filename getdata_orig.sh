#!/bin/bash

git submodule update --init --recursive

for data in 'contributions' 'votes'; do
    pushd "./data/$data"
    ./getdata.sh
    popd
done
