import fs from 'node:fs/promises'
import path from 'node:path'

const frontendRoot = path.resolve(import.meta.dirname, '..')
const publicDir = path.join(frontendRoot, 'public')
const defaultSiteUrl = 'https://www.sakurakugu.top'
const defaultApiBaseUrl = 'https://api.sakurakugu.top/v1'

const staticRoutes = [
  '/',
  '/blog',
  '/archive',
  '/announcements',
  '/friends',
  '/about',
  '/guestbook',
  '/sponsor',
  '/media',
  '/gallery',
  '/rss',
]

function normalizeBaseUrl(url, fallback) {
  const normalized = url?.trim() || fallback
  return normalized.endsWith('/') ? normalized : `${normalized}/`
}

function xmlEscape(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;')
}

function createSitemapUrl(pathname, siteUrl) {
  return new URL(pathname === '/' ? '/' : pathname.replace(/\/+$/, ''), siteUrl).href
}

async function loadArticleEntries(apiBaseUrl, siteUrl) {
  const requestUrl = new URL('articles/all-meta', apiBaseUrl).href

  try {
    const response = await fetch(requestUrl)
    if (!response.ok) {
      throw new Error(`接口返回 ${response.status}`)
    }

    const articles = await response.json()
    if (!Array.isArray(articles)) {
      throw new Error('返回值不是数组')
    }

    return articles
      .filter((item) => typeof item?.slug === 'string' && item.slug.trim().length > 0)
      .map((item) => ({
        loc: createSitemapUrl(`/blog/${item.slug.trim()}`, siteUrl),
        lastmod: typeof item?.published_at === 'string' && item.published_at.trim().length > 0
          ? new Date(item.published_at).toISOString()
          : null,
      }))
  } catch (error) {
    console.warn(`[generate:seo] 文章 sitemap 获取失败，将仅输出静态路由：${error instanceof Error ? error.message : String(error)}`)
    return []
  }
}

async function writeSitemap(siteUrl, apiBaseUrl) {
  const staticEntries = staticRoutes.map((pathname) => ({
    loc: createSitemapUrl(pathname, siteUrl),
    lastmod: null,
  }))
  const articleEntries = await loadArticleEntries(apiBaseUrl, siteUrl)
  const uniqueEntries = [...staticEntries, ...articleEntries].filter((entry, index, entries) => (
    entries.findIndex((candidate) => candidate.loc === entry.loc) === index
  ))

  const xml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...uniqueEntries.map((entry) => {
      const lines = ['  <url>', `    <loc>${xmlEscape(entry.loc)}</loc>`]
      if (entry.lastmod) {
        lines.push(`    <lastmod>${entry.lastmod}</lastmod>`)
      }
      lines.push('  </url>')
      return lines.join('\n')
    }),
    '</urlset>',
    '',
  ].join('\n')

  await fs.writeFile(path.join(publicDir, 'sitemap.xml'), xml, 'utf8')
}

async function writeRobots(siteUrl) {
  const robotsTxt = [
    '# 个人博客站点：允许搜索引擎抓取公开内容',
    'User-agent: *',
    'Allow: /',
    '',
    '# 后台管理页不需要被收录',
    'Disallow: /dashboard',
    'Disallow: /dashboard/',
    '',
    '# 常见无意义或敏感入口',
    'Disallow: /404',
    '',
    '# 站点地图',
    `Sitemap: ${new URL('sitemap.xml', siteUrl).href}`,
    '',
  ].join('\n')

  await fs.writeFile(path.join(publicDir, 'robots.txt'), robotsTxt, 'utf8')
}

async function main() {
  const siteUrl = normalizeBaseUrl(process.env.SITE_URL || process.env.VITE_SITE_URL, defaultSiteUrl)
  const apiBaseUrl = normalizeBaseUrl(process.env.SITEMAP_API_BASE_URL || process.env.VITE_API_BASE, defaultApiBaseUrl)

  await fs.mkdir(publicDir, { recursive: true })
  await writeSitemap(siteUrl, apiBaseUrl)
  await writeRobots(siteUrl)
  console.log(`[generate:seo] 已生成 sitemap.xml 与 robots.txt，站点地址：${siteUrl}`)
}

await main()
