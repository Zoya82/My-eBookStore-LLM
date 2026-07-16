import { useEffect, useState } from 'react'
import { getCart } from '../api/cart'
import { createOrder } from '../api/orders'
import { useAuth } from '../auth/AuthContext'
import { createAddress, getAddresses } from '../api/addresses'

const addressFields = ['receiver', 'phone', 'province', 'city', 'district', 'detail']

function cleanAddress(address) {
  return Object.fromEntries(addressFields.map(field => [field, String(address?.[field] || '').trim()]))
}

function isSameAddress(left, right) {
  const cleanLeft = cleanAddress(left)
  const cleanRight = cleanAddress(right)
  return addressFields.every(field => cleanLeft[field] === cleanRight[field])
}

function orderAddress(address) {
  return [address.province, address.city, address.district, address.detail].filter(Boolean).join(' ')
}

function BookCover({ src, title, className }) {
  const [failed, setFailed] = useState(false)
  return (
    <div className={className} aria-label={`${title || '图书'}封面`}>
      <span>{title?.slice(0, 1) || '书'}</span>
      {src && !failed && <img src={src} alt={`${title || '图书'}封面`} onError={() => setFailed(true)} />}
    </div>
  )
}

function OrderConfirmPage({ cartItemIds, onBack, onCreated, onRequireLogin }) {
  const { user, isAuthenticated, authLoading } = useAuth()
  const [items, setItems] = useState(null)
  const [form, setForm] = useState({ receiver: user?.username || '', phone: user?.phone || '', province: '', city: '', district: '', detail: '', remark: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [addresses, setAddresses] = useState([])
  const [addressError, setAddressError] = useState('')
  const [saveToAddressBook, setSaveToAddressBook] = useState(true)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) onRequireLogin?.()
    if (isAuthenticated) {
      getAddresses().then(list => { setAddresses(list); const selected = list.find(item => item.is_default) || list[0]; if (selected) setForm(current => ({ ...current, ...cleanAddress(selected) })) }).catch(e => setAddressError(e.message))
      getCart()
        .then(cart => {
          const found = cart.items.filter(item => cartItemIds.includes(item.id) && item.isValid && item.selected)
          if (found.length !== cartItemIds.length) setError('购物车状态已变化，请返回购物车重新确认')
          else setItems(found)
        })
        .catch(requestError => setError(requestError.message))
    }
  }, [authLoading, isAuthenticated, cartItemIds, onRequireLogin])

  const submit = async event => {
    event.preventDefault()
    const shippingAddress = cleanAddress(form)
    const address = orderAddress(shippingAddress)
    if (!shippingAddress.receiver || shippingAddress.receiver.length > 50 || !/^\d{11}$/.test(shippingAddress.phone) || !shippingAddress.province || !shippingAddress.city || !shippingAddress.district || !shippingAddress.detail || address.length > 200) {
      return setError('请填写有效的收货人、11位手机号和完整收货地址')
    }
    setBusy(true)
    setError('')
    try {
      const alreadySaved = addresses.some(saved => isSameAddress(saved, shippingAddress))
      if (saveToAddressBook && !alreadySaved) {
        const saved = await createAddress({ ...shippingAddress, is_default: addresses.length === 0 })
        setAddresses(current => [saved, ...current])
      }
      const order = await createOrder({ address, receiver: shippingAddress.receiver, phone: shippingAddress.phone, remark: form.remark, cartItemIds })
      onCreated(order)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  if (authLoading) return <div className="page-card">正在恢复登录状态…</div>
  if (!isAuthenticated) return <div className="page-card">请先登录<button className="primary-btn" onClick={onRequireLogin}>去登录</button></div>
  if (error && !items) return <div className="order-page page-card"><p>{error}</p><button className="secondary-btn" onClick={onBack}>返回购物车</button></div>
  if (!items) return <div className="page-card">正在确认购物车…</div>

  const total = items.reduce((sum, item) => sum + (item.subtotal || 0), 0)
  const isSavedAddress = addresses.some(address => isSameAddress(address, form))

  return (
    <div className="order-page order-confirm-page">
      <div className="order-page-heading">
        <button className="back-btn" onClick={onBack}>← 返回购物车</button>
        <div>
          <p className="order-eyebrow">CHECKOUT</p>
          <h2>确认订单</h2>
          <p>核对商品信息并填写收货资料</p>
        </div>
      </div>

      <div className="order-confirm-layout">
        <section className="order-panel order-summary-panel">
          <div className="order-panel-title">
            <h3>商品清单</h3>
            <span>{items.length} 件商品</span>
          </div>
          <div className="order-items">
            {items.map(item => (
              <div className="order-confirm-item" key={item.id}>
                <BookCover className="order-confirm-cover" src={item.book.coverImage} title={item.book.title} />
                <div className="order-confirm-copy">
                  <strong>{item.book.title}</strong>
                  <span>{item.versionLabel}</span>
                </div>
                <div className="order-confirm-price">
                  <strong>¥{item.subtotal?.toFixed(2) || '暂无报价'}</strong>
                  <span>¥{item.unitPrice?.toFixed(2) || '暂无报价'} × {item.quantity}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="order-total-row">
            <span>订单合计</span>
            <strong>¥{total.toFixed(2)}</strong>
          </div>
        </section>

        <section className="order-panel order-form-panel">
          <div className="address-select-area"><h3>选择收货地址</h3>{addressError&&<div className="error-msg">{addressError}</div>}{addresses.map(address => <button type="button" className={`address-option${isSameAddress(address, form) ? ' selected' : ''}`} key={address.id} onClick={() => setForm(current => ({ ...current, ...cleanAddress(address) }))}><strong>{address.receiver} {address.phone}</strong><span>{address.province} {address.city} {address.district} {address.detail}</span>{address.is_default&&<em>默认地址</em>}</button>)}</div>
          <div className="order-panel-title">
            <h3>收货信息</h3>
            <span>请确认填写无误</span>
          </div>
          <form className="order-form" onSubmit={submit} noValidate>
            <div className="order-form-row">
              <label>收货人<input value={form.receiver} onChange={event => setForm({ ...form, receiver: event.target.value })} maxLength="50" required /></label>
              <label>手机号<input value={form.phone} onChange={event => setForm({ ...form, phone: event.target.value })} inputMode="numeric" maxLength="11" required /></label>
            </div>
            <div className="order-form-row">
              <label>省<input value={form.province} onChange={event => setForm({ ...form, province: event.target.value })} maxLength="50" required /></label>
              <label>市<input value={form.city} onChange={event => setForm({ ...form, city: event.target.value })} maxLength="50" required /></label>
            </div>
            <div className="order-form-row">
              <label>区 / 县<input value={form.district} onChange={event => setForm({ ...form, district: event.target.value })} maxLength="50" required /></label>
              <label>详细地址<input value={form.detail} onChange={event => setForm({ ...form, detail: event.target.value })} maxLength="200" required /></label>
            </div>
            {isSavedAddress
              ? <div className="success-msg">该地址已在您的地址库中</div>
              : <label className="address-default"><input type="checkbox" checked={saveToAddressBook} onChange={event => setSaveToAddressBook(event.target.checked)} />将此新地址保存到我的收货地址</label>}
            <label>备注（选填）<textarea value={form.remark} onChange={event => setForm({ ...form, remark: event.target.value })} rows="3" placeholder="可填写配送说明等信息" /></label>
            {error && <div className="error-msg">{error}</div>}
            <button className="primary-btn order-submit-btn" disabled={busy}>{busy ? '创建中…' : `提交订单 · ¥${total.toFixed(2)}`}</button>
          </form>
        </section>
      </div>
    </div>
  )
}

export default OrderConfirmPage
