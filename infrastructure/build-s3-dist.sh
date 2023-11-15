#!/bin/bash
cd ../front-end
rm -rf build/
rm -rf node_modules/
npm ci
npm run build
