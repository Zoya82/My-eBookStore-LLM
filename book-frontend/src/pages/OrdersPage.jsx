import { useEffect, useState } from 'react'
import { getOrders } from '../api/orders'
import { useAuth } from '../auth/AuthContext'

const filters = [['', '全部'], [1, '待付款'], [2, '已提交'], [3, '待收货'], [4, '已完成'], [5, '已取消']]

function BookCover({ src, title }) {
  const [failed, setFailed] = useState(false)
  return (
    <div className="order-list-cover" aria-label={`${title || '图书'}封面`}>
      <span>{title?.slice(0, 1) || '书'}</span>
      {src && !failed && <img src={src} alt={`${title || '图书'}封面`} onError={() => setFailed(true)} />}
    </div>
  )
}
const logistics = order => { const physical = order.items.some(item => item.versionType === 'physical'); if (!physical) return '电子订单，无需物流'; if (order.status === 5) return '订单已取消'; if (order.status === 1) return '订单尚未支付'; if (order.status === 2) return '等待商家发货'; return order.expressCompany && order.expressNo ? `${order.expressCompany} · ${order.expressNo}` : '已发货，物流信息暂缺' }

function OrdersPage({ onBack, onDetail, onRequireLogin }) {
  const { isAuthenticated, authLoading, user } = useAuth()
  const [filter, setFilter] = useState('')
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!isAuthenticated || authLoading) return
    let active = true
    const timer = setTimeout(() => {
      setLoading(true)
      setError('')
      getOrders(filter)
        .then(data => { if (active) setOrders(data) })
        .catch(requestError => { if (active) setError(requestError.message) })
        .finally(() => { if (active) setLoading(false) })
    }, 0)
    return () => { active = false; clearTimeout(timer) }
  }, [filter, isAuthenticated, authLoading, user?.id])

  if (authLoading) return <div className="page-card">正在恢复登录状态…</div>
  if (!isAuthenticated) return <div className="page-card">登录后查看订单<button className="primary-btn" onClick={onRequireLogin}>去登录</button></div>

  return (
    <div className="orders-page">
      <div className="order-page-heading">
        <button className="back-btn" onClick={onBack}>← 返回我的</button>
        <div>
          <p className="order-eyebrow">MY ORDERS</p>
          <h2>我的订单</h2>
          <p>查看订单状态与商品明细</p>
        </div>
      </div>

      <div className="order-filters" aria-label="订单状态筛选">
        {filters.map(([value, label]) => (
          <button key={label} type="button" className={String(filter) === String(value) ? 'active' : ''} onClick={() => setFilter(value)}>{label}</button>
        ))}
      </div>

      {loading && <div className="status-message">正在加载订单…</div>}
      {error && <div className="error-msg order-list-error"><span>{error}</span><button className="secondary-btn" onClick={() => setFilter(filter)}>重试</button></div>}
      {!loading && !error && !orders.length && <div className="page-card order-empty">暂无此状态的订单</div>}

      <div className="order-list">
        {orders.map(order => (
          <article className="order-card" key={order.id}>
            <header className="order-card-header">
              <div>
                <span className="order-card-label">订单号</span>
                <strong>{order.orderNo}</strong>
              </div>
              <span className={`order-status order-status-${order.status}`}>{order.statusText}</span>
            </header>
            <div className="order-card-items">
              {order.items.map(item => (
                <div className="order-card-item" key={item.id}>
                  <BookCover src={item.coverImage} title={item.title} />
                  <div className="order-list-copy">
                    <strong>{item.title}</strong>
                    <span>{item.versionLabel} · 数量 {item.quantity}</span>
                  </div>
                  <strong className="order-line-price">¥{item.subtotal?.toFixed(2) || '暂无报价'}</strong>
                </div>
              ))}
            </div>
            <footer className="order-card-footer">
              <div className="order-card-total"><span>共 {order.itemCount} 件</span><strong>合计 ¥{order.totalAmount?.toFixed(2) || '暂无报价'}</strong><span className="order-list-logistics">{logistics(order)}</span></div>
              <button className="secondary-btn" onClick={() => onDetail(order.id)}>查看详情</button>
            </footer>
          </article>
        ))}
      </div>
    </div>
  )
}

export default OrdersPage
