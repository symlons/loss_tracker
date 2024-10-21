#!/bin/bash


echo "Starting backend..."
npm run --prefix ./server dev &

echo "Starting frontend..."
npm run --prefix ./client dev &

wait
