cd "$(dirname "$0")/dashboard"
pnpm i
VITE_BASE_API=/ pnpm run build --if-present -- --outDir build --assetsDir statics
cp ./build/index.html ./build/404.html
