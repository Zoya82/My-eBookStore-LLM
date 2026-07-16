import { request } from './client.js'
import { normalizeBook } from './normalizers.js'

const BOOK_LIST_PARAMS = ['page', 'page_size', 'search', 'category', 'publisher', 'is_new', 'price_min', 'price_max', 'ordering']

export async function getBooks(params = {}) {
  const query = Object.fromEntries(BOOK_LIST_PARAMS.filter(key => params[key] !== undefined && params[key] !== null && params[key] !== '').map(key => [key, params[key]]))
  const response = await request('/books/', { params: query })
  return {
    count: response?.count ?? 0,
    next: response?.next ?? null,
    previous: response?.previous ?? null,
    items: Array.isArray(response?.results) ? response.results.map(normalizeBook) : [],
  }
}

export async function getHomeBooks() {
  const response = await request('/books/home/')
  const data = response?.data || {}
  return {
    banners: data.banners ?? [],
    newBooks: Array.isArray(data.new_books) ? data.new_books.map(normalizeBook) : [],
    hotBooks: Array.isArray(data.hot_books) ? data.hot_books.map(normalizeBook) : [],
  }
}
export async function getBookCategories() { const response = await request('/books/categories/'); return Array.isArray(response?.data) ? response.data.map(value => ({ id:Number.isSafeInteger(Number(value?.id)) ? Number(value.id) : null, name:typeof value?.name === 'string' ? value.name : '', parentId:Number.isSafeInteger(Number(value?.parent)) ? Number(value.parent) : null, parentName:typeof value?.parent_name === 'string' ? value.parent_name : '', bookCount:Number.isSafeInteger(Number(value?.book_count)) && Number(value.book_count) >= 0 ? Number(value.book_count) : 0 })) : [] }

export async function getBookDetail(id) {
  if (id === undefined || id === null || id === '') throw new Error('获取图书详情需要提供图书 ID')
  const response = await request(`/books/${encodeURIComponent(id)}/`)
  return normalizeBook(response?.data ?? response)
}

const nonNegativeInt = value => { const n = Number(value); return Number.isFinite(n) && n >= 0 ? Math.floor(n) : 0 }
export async function getBookPreview(bookId) {
  if (bookId === undefined || bookId === null || bookId === '') throw new Error('试读需要提供图书 ID')
  const data = (await request(`/books/${encodeURIComponent(bookId)}/preview/`)).data
  return { bookId: data.book_id, title: data.book_title || '', content: typeof data.content === 'string' ? data.content : '', totalLength: nonNegativeInt(data.total_length), previewLength: nonNegativeInt(data.preview_length), isComplete: Boolean(data.is_complete) }
}
export async function getBookContent(bookId) {
  if (bookId === undefined || bookId === null || bookId === '') throw new Error('阅读全文需要提供图书 ID')
  const data = (await request(`/books/${encodeURIComponent(bookId)}/read/`)).data
  return { bookId: data.book_id, title: data.title || '', author: data.author || '', content: typeof data.content === 'string' ? data.content : '', totalLength: nonNegativeInt(data.total_length) }
}
