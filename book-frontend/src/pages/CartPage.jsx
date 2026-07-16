import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { deleteCartItem, getCart, setCartItemsSelected, updateCartItemQuantity, clearInvalidCartItems } from '../api/cart'

function CartCover({ book }) {
  const [failed, setFailed] = useState(false)
  return (
    <div className="cart-cover" aria-label={`${book.title || '图书'}封面`}>
      <span>{book.title?.slice(0, 1) || '书'}</span>
      {book.coverImage && !failed && (
        <img src={book.coverImage} alt={`${book.title || '图书'}封面`} onError={() => setFailed(true)} />
      )}
    </div>
  )
}

function CartPage({ onRequireLogin, onCheckout }) {
  const { user, isAuthenticated, authLoading } = useAuth()
  const [cart, setCart] = useState(null); const [error, setError] = useState(''); const [busy, setBusy] = useState(null)
  const load = async () => { if (!isAuthenticated) { setCart(null); return }; try { setCart(await getCart()) } catch (e) { setError(e.message) } }
  // Synchronize the server cart after authentication changes.
  // eslint-disable-next-line react-hooks/set-state-in-effect, react-hooks/exhaustive-deps
  useEffect(() => { if (!authLoading) load() }, [user?.id, isAuthenticated, authLoading])
  const operate = async (id, fn) => { setBusy(id); setError(''); try { await fn(); await load() } catch (e) { setError(e.message) } finally { setBusy(null) } }
  if (authLoading) return <div className="page-card">正在恢复登录状态…</div>
  if (!isAuthenticated) return <div className="page-card">登录后可查看和同步购物车<button className="primary-btn" onClick={onRequireLogin}>去登录</button></div>
  if (error && !cart) return <div className="page-card error-msg">{error}<button className="secondary-btn" onClick={load}>重试</button></div>
  if (!cart) return <div className="page-card">正在加载购物车…</div>
  const valid = cart.items.filter(item => item.isValid); const invalid = cart.invalidItems; const selected = valid.filter(item => item.selected); const allSelected = valid.length > 0 && selected.length === valid.length
  return <div className="cart-page"><h2>购物车</h2>{error && <div className="error-msg">{error}</div>}{!cart.items.length && !invalid.length ? <div className="page-card">购物车为空</div> : <><div className="cart-bar"><label className="select-all"><input type="checkbox" checked={allSelected} disabled={!valid.length} onChange={() => operate('all', () => setCartItemsSelected(valid.map(item => item.id), !allSelected))} />全选</label><span>已选 {selected.length} 件</span></div>{cart.items.map(item => <div className="cart-item" key={item.id}><div className="cart-item-left">{item.isValid && <input type="checkbox" checked={item.selected} disabled={busy === item.id} onChange={() => operate(item.id, () => setCartItemsSelected([item.id], !item.selected))} />}<CartCover book={item.book} /><div className="cart-info"><div className="cart-title">{item.book.title}</div><div>{item.book.author}</div><div className="version-label">{item.versionLabel}</div><div>¥{item.unitPrice?.toFixed(2) || '暂无报价'} · 数量 {item.quantity}</div>{!item.isValid && <span className="invalid-label">{item.invalidReason}</span>}</div></div>{item.isValid && <div className="cart-item-right"><div className="cart-qty"><button disabled={busy === item.id || item.quantity <= 1} onClick={() => operate(item.id, () => updateCartItemQuantity(item.id, item.quantity - 1))}>-</button><span>{item.quantity}</span><button disabled={busy === item.id || (item.versionType === 'physical' && item.quantity >= item.stock)} onClick={() => operate(item.id, () => updateCartItemQuantity(item.id, item.quantity + 1))}>+</button></div><div>小计 ¥{item.subtotal?.toFixed(2) || '暂无报价'}</div><button className="remove-btn" disabled={busy === item.id} onClick={() => operate(item.id, () => deleteCartItem(item.id))}>删除</button></div>}</div>)}{invalid.length > 0 && <div className="invalid-section"><span>失效商品 ({cart.invalidCount})</span><button className="clear-invalid" onClick={() => operate('clear', clearInvalidCartItems)}>清理失效商品</button></div>}<div className="cart-footer"><div>已选商品总价 ¥{(cart.selectedTotal || 0).toFixed(2)}</div><button className="checkout-btn" disabled={!selected.length} onClick={() => onCheckout?.(selected.map(item => item.id))}>去结算</button></div></>}</div>
}
export default CartPage
