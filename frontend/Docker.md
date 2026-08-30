## Docker has specific installation instructions for each operating system.
## Please refer to the official documentation at https://docker.com/get-started/

## Create a Node.js container and start a Shell session:
docker run -it --rm --entrypoint sh -p 5173:5173 -v "${PWD}/:/app" node:24-alpine

## Do this when you first run it
export NODE_EXTRA_CA_CERTS="CAINLROOT_B64.crt"

## Verify the Node.js version:
node -v # Should print
## Verify npm version:
npm -v # Should print 
## Change Directory to app
cd app/
## Run Dev
npm run dev -- --host