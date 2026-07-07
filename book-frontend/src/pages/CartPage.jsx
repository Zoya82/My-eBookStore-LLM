import { useMemo, useState } from 'react'

function CartPage({ items, onUpdateQuantity, onToggleSelect, onRemove }) {
  const [checkoutNotice, setCheckoutNotice] = useState('')
  const [showInvalid, setShowInvalid] = useState(true)

  const invalidItems = useMemo(
    () => [
      {
        id: 'invalid-1',
        title: '经典已下架',
        price: 39.0,
        color: '#D8C6A5',
        reason: '已下架',
      },
    ],
    []
  )

  const checkedItems = items.filter((item) => item.selected)
  const total = checkedItems.reduce((sum, item) => sum + item.price * item.quantity, 0)
  const allSelected = items.length > 0 && checkedItems.length === items.length

  const handleSelectAll = () => {
    items.forEach((item) => {
      if (item.selected !== !allSelected) {
        onToggleSelect(item.id)
      }
    })
  }

  const handleCheckout = () => {
    if (checkedItems.length === 0) {
      setCheckoutNotice('请选择至少一本商品后再结算。')
      return
    }
    setCheckoutNotice(`已选 ${checkedItems.length} 件商品，准备前往订单确认。`)
  }

  const handleClearInvalid = () => {
    setShowInvalid(false)
  }

  return (
    <div className="cart-page">
      <h2>购物车</h2>
      {items.length === 0 ? (
        <div className="page-card">
          <p>购物车为空，快去挑选喜欢的书吧。</p>
        </div>
      ) : (
        <>
          <div className="cart-bar">
            <label className="select-all">
              <input type="checkbox" checked={allSelected} onChange={handleSelectAll} /> 全选
            </label>
            <div className="cart-bar-info">已选 {checkedItems.length} 本</div>
          </div>

          {items.map((item) => (
            <div className="cart-item" key={item.id}>
              <div className="cart-item-left">
                <input
                  type="checkbox"
                  checked={item.selected}
                  onChange={() => onToggleSelect(item.id)}
                />
                <div className="cart-cover" style={{ background: item.color }}>
                  {item.title[0]}
                </div>
                <div className="cart-info">
                  <div className="cart-title">{item.title}</div>
                  <div className="cart-price">单价 ¥{item.price.toFixed(2)}</div>
                </div>
              </div>
              <div className="cart-item-right">
                <div className="cart-qty">
                  <button
                    type="button"
                    onClick={() => onUpdateQuantity(item.id, Math.max(1, item.quantity - 1))}
                  >
                    -
                  </button>
                  <span>{item.quantity}</span>
                  <button type="button" onClick={() => onUpdateQuantity(item.id, item.quantity + 1)}>
                    +
                  </button>
                </div>
                <div className="cart-subtotal">小计 ¥{(item.price * item.quantity).toFixed(2)}</div>
                <button className="remove-btn" type="button" onClick={() => onRemove(item.id)}>
                  删除
                </button>
              </div>
            </div>
          ))}

          {showInvalid && (
            <div className="invalid-section">
              <div className="invalid-header">
                <span>失效商品</span>
                <button type="button" className="clear-invalid" onClick={handleClearInvalid}>
                  清空
                </button>
              </div>
              {invalidItems.map((invalid) => (
                <div className="invalid-item" key={invalid.id}>
                  <div className="cart-cover" style={{ background: invalid.color }}>
                    {invalid.title[0]}
                  </div>
                  <div className="invalid-info">
                    <div className="cart-title">{invalid.title}</div>
                    <div className="cart-price">¥{invalid.price.toFixed(2)}</div>
                  </div>
                  <span className="invalid-label">{invalid.reason}</span>
                </div>
              ))}
            </div>
          )}

          <div className="cart-footer">
            <label className="select-all">
              <input type="checkbox" checked={allSelected} onChange={handleSelectAll} /> 全选
            </label>
            <div className="checkout-info">
              <div>已选商品总价</div>
              <div className="checkout-price">¥{total.toFixed(2)}</div>
            </div>
            <button className="checkout-btn" type="button" onClick={handleCheckout}>
              去结算 ({checkedItems.length} 件)
            </button>
          </div>
          {checkoutNotice && <div className="checkout-notice">{checkoutNotice}</div>}
        </>
      )}
    </div>
  )
}

export default CartPage
