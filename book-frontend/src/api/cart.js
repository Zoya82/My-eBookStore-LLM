import { request } from './client'
import { normalizeBook } from './normalizers'
const money = value => { const n = Number(value); return Number.isFinite(n) ? n : null }
const normalizeItem = (item = {}) => ({ id: item.id, bookId: item.book, book: normalizeBook(item.book_detail || {}), versionType: item.version_type, versionLabel: item.version_label || item.version_type, quantity: item.quantity, selected: Boolean(item.is_selected), unitPrice: money(item.unit_price), subtotal: money(item.subtotal), stock: Number(item.stock) || 0, isValid: item.is_valid !== false, invalidReason: item.invalid_reason || '', createdAt: item.created_at })
export async function getCart() { const data = await request('/cart/'); return { items: (data?.items || []).map(normalizeItem), invalidItems: (data?.invalid_items || []).map(normalizeItem), selectedTotal: money(data?.selected_total) ?? 0, invalidCount: Number(data?.invalid_count) || 0 } }
export async function addCartItem({ bookId, versionType, quantity = 1 }) { const r = await request('/cart/', { method: 'POST', body: { book_id: bookId, version_type: versionType, quantity } }); return normalizeItem(r.data) }
export async function updateCartItemQuantity(itemId, quantity) { const r = await request(`/cart/${itemId}/`, { method: 'PUT', body: { quantity } }); return normalizeItem(r.data) }
export async function deleteCartItem(itemId) { return request(`/cart/${itemId}/`, { method: 'DELETE' }) }
export async function setCartItemsSelected(itemIds, isSelected) { return request('/cart/batch/', { method: 'POST', body: { item_ids: itemIds, is_selected: isSelected } }) }
export async function deleteCartItems(itemIds) { return request('/cart/batch/', { method: 'DELETE', body: { item_ids: itemIds } }) }
export async function clearInvalidCartItems() { return request('/cart/clear-invalid/', { method: 'DELETE' }) }
