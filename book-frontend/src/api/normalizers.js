import { API_BASE } from './client.js'

const MEDIA_BASE = API_BASE.replace(/\/api\/?$/, '')

export function resolveMediaUrl(url) {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  return `${MEDIA_BASE}${url.startsWith('/') ? url : `/${url}`}`
}

export function normalizeBook(book = {}) {
  const versions = Array.isArray(book.versions) ? book.versions : []
  const salePrice = book.sale_price
  const parsedPrice = Number(salePrice)
  const priceNum = salePrice === null || salePrice === undefined || salePrice === '' || !Number.isFinite(parsedPrice) ? null : parsedPrice
  const category = book.category || null
  const publishDate = book.publish_date || null
  const hasDigital = book.has_digital ?? versions.some(version => version.version_type === 'digital' && version.is_on_sale !== false)
  const hasPhysical = book.has_physical ?? versions.some(version => version.version_type === 'physical' && version.is_on_sale !== false)

  return {
    id: book.id ?? null,
    title: book.title ?? '',
    author: book.author ?? '',
    isbn: book.isbn ?? null,
    publisher: book.publisher ?? null,
    publishDate,
    year: publishDate ? String(publishDate).slice(0, 4) : null,
    description: book.description ?? null,
    catalog: book.catalog ?? null,
    coverImage: resolveMediaUrl(book.cover_image),
    price: priceNum === null ? '暂无报价' : `¥${priceNum.toFixed(2)}`,
    priceNum,
    rating: book.rating ?? null,
    sales: book.sales_count ?? null,
    stock: book.stock ?? null,
    category,
    categoryName: book.category_name ?? category?.name ?? null,
    versions,
    hasPreview: Boolean(book.has_preview ?? book.content_file_path),
    hasDigital: Boolean(hasDigital),
    hasPhysical: Boolean(hasPhysical),
    isOnSale: typeof book.is_on_sale === 'boolean' ? book.is_on_sale : null,
    color: '#E8C9A6',
    raw: book,
  }
}
