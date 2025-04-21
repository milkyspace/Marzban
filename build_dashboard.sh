cd "$(dirname "$0")/dashboard"
VITE_BASE_API=/ pnpm run build -- --outDir build --assetsDir statics
cp ./build/index.html ./build/404.html
 