import { request } from './client.js'
import { normalizeBook } from './normalizers.js'

function idOf(value) {
  if (value === undefined || value === null || value === '') throw new Error('bookId is required')
  const id = Number(value)
  if (!Number.isInteger(id) || id <= 0) throw new Error('bookId must be a positive integer')
  return id
}
function dataOf(response) { return response?.data ?? response }
function reviewOf(item = {}) {
  return { id: item.id ?? null, userId: item.user ?? null, username: item.username ?? '', bookId: item.book ?? null, bookTitle: item.book_title ?? '', book: normalizeBook(item.book_detail || {}), rating: Number.isInteger(Number(item.rating)) ? Number(item.rating) : 0, comment: item.comment ?? '', createdAt: item.created_at ?? null, updatedAt: item.updated_at ?? null, isMine: Boolean(item.is_mine) }
}
function recordOf(item = {}) { return { id: item.id ?? null, bookId: item.book ?? null, book: normalizeBook(item.book_detail || {}), bookIsOnSale: item.book_is_on_sale ?? null, createdAt: item.created_at ?? null } }
export async function getBookReviews(bookId) { const id = idOf(bookId); const response = await request('/interactions/reviews/', { params: { book_id: id } }); return (dataOf(response) || []).map(reviewOf) }
export async function createBookReview({ bookId, rating, comment }) { const id = idOf(bookId); const response = await request('/interactions/reviews/', { method: 'POST', body: { book_id: id, rating, comment: String(comment ?? '').trim() } }); return reviewOf(dataOf(response)) }
export async function getMyReviews() { const response = await request('/interactions/reviews/me/'); return (dataOf(response) || []).map(reviewOf) }
export async function getFavorites(bookId) { const params = bookId === undefined || bookId === null || bookId === '' ? {} : { book_id: idOf(bookId) }; const response = await request('/interactions/favorites/', { params }); return (dataOf(response) || []).map(recordOf) }
export async function toggleFavorite(bookId) { const id = idOf(bookId); const response = await request('/interactions/favorites/toggle/', { method: 'POST', body: { book_id: id } }); const data = dataOf(response); return { action: data.action, bookId: data.book_id ?? id, isFavorite: Boolean(data.is_favorite) } }
export async function getBrowsingHistory() { const response = await request('/interactions/histories/'); return (dataOf(response) || []).map(recordOf) }
export async function recordBrowsingHistory(bookId) { const id = idOf(bookId); const response = await request('/interactions/histories/', { method: 'POST', body: { book_id: id } }); return recordOf(dataOf(response)) }
export async function clearBrowsingHistory() { const response = await request('/interactions/histories/', { method: 'DELETE' }); return { deletedCount: Number(dataOf(response)?.deleted_count ?? 0) } }
