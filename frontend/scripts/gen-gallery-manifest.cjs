const fs = require('fs')
const path = require('path')

const galleryDir = path.resolve(__dirname, '../public/gallery')
const outFile = path.resolve(__dirname, '../src/features/gallery/manifest.ts')

const manifest = {}
if (fs.existsSync(galleryDir)) {
  const albums = fs.readdirSync(galleryDir, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name)
  for (const album of albums) {
    const albumDir = path.join(galleryDir, album)
    const files = fs.readdirSync(albumDir)
      .filter(f => /\.(jpe?g|png|webp|avif|gif)$/i.test(f))
      .sort((a, b) => {
        const aIsCover = /^cover\./i.test(a)
        const bIsCover = /^cover\./i.test(b)
        if (aIsCover && !bIsCover) return -1
        if (!aIsCover && bIsCover) return 1
        return a.localeCompare(b)
      })
    manifest[album] = files.map(f => `/gallery/${album}/${f}`)
  }
}

fs.mkdirSync(path.dirname(outFile), { recursive: true })
const content = `// 自动生成，由 scripts/gen-gallery-manifest.js 维护
export const galleryManifest: Record<string, string[]> = ${JSON.stringify(manifest, null, 2)}
`
fs.writeFileSync(outFile, content)
console.log('Generated gallery manifest:', outFile)
