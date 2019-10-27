#/bin/bash
cd html
yarn install
yarn build
cd ../server
python3 server.py
