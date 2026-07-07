import { useState } from 'react'
import { summarizeBook } from '../api/ai'

function BookDetailPage({ book, onBack, onAddToCart }) {
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [summaryError, setSummaryError] = useState('')
  const [summary, setSummary] = useState('')
  const [activeTab, setActiveTab] = useState('简介')
  const [collected, setCollected] = useState(false)
  const [buyNotice, setBuyNotice] = useState('')

  if (!book) {
    return null
  }

  const descText =
    book.description ||
    '这本书由作者用细腻的笔触讲述生活中的温度与思考，适合在闲暇时阅读，带来轻松又有收获的阅读体验。'

  const bookPublisher = book.publisher || '晓光出版社'
  const originalPrice = book.originalPrice || '¥88.00'
  const stock = book.stock || '有货'

  const handleGetSummary = async () => {
    setSummaryError('')
    setSummary('')
    setSummaryLoading(true)

    try {
      const data = await summarizeBook(descText, 60)
      setSummary(data.summary)
    } catch (err) {
      setSummaryError(err.message)
    } finally {
      setSummaryLoading(false)
    }
  }

  const handleBuyNow = () => {
    onAddToCart(book)
    setBuyNotice('已添加购物车，可在购物车页继续结算')
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case '目录':
        return (
          <div className="tab-section">
            <ol>
              <li>第一章 破晓</li>
              <li>第二章 阅读之旅</li>
              <li>第三章 心灵篇章</li>
              <li>第四章 深入思考</li>
              <li>第五章 温暖结语</li>
            </ol>
          </div>
        )
      case '评价':
        return (
          <div className="tab-section">
            <p>“语言优美，令人沉浸。每一章都像一次心灵漫步。”</p>
            <p>“书中故事温暖且富有哲理，适合静心阅读。”</p>
          </div>
        )
      case '详情参数':
        return (
          <div className="tab-section detail-params">
            <div>页数：320 页</div>
            <div>语言：中文</div>
            <div>装帧：平装</div>
            <div>ISBN：978-7-12345-678-9</div>
          </div>
        )
      case '简介':
      default:
        return (
          <>
            <div className="tab-section">
              <h4>图书简介</h4>
              <p>{descText}</p>
            </div>
            <div className="tab-section">
              <h4>AI 摘要</h4>
              <button
                className="secondary-btn"
                onClick={handleGetSummary}
                disabled={summaryLoading}
              >
                {summaryLoading ? '正在生成...' : '生成 AI 摘要'}
              </button>
              {summaryError && <div className="error-msg">{summaryError}</div>}
              {summary ? (
                <div className="summary-content">{summary}</div>
              ) : (
                <p className="hint-text">点击 AI 摘要，快速得到书籍亮点与阅读推荐。</p>
              )}
            </div>
          </>
        )
    }
  }

  return (
    <div className="detail-page">
      <button className="back-btn" onClick={onBack}>
        ← 返回
      </button>

      <div className="detail-card detail-grid">
        <div className="detail-cover detail-cover-large" style={{ background: book.color }}>
          <span>{book.title[0]}</span>
        </div>

        <div className="detail-info detail-main">
          <h2>{book.title}</h2>
          <p className="detail-author">作者：{book.author}</p>
          <p className="detail-publisher">出版社：{bookPublisher}</p>

          <div className="detail-meta-row">
            <span className="meta-item">定价：<del>{originalPrice}</del></span>
            <span className="meta-item sale">售价：{book.price}</span>
            <span className={`stock-tag stock-${stock === '有货' ? 'in' : stock === '库存紧张' ? 'low' : 'out'}`}>
              {stock}
            </span>
          </div>

          <div className="detail-actions detail-actions-grid">
            <button className="primary-btn" onClick={() => onAddToCart(book)}>
              加入购物车
            </button>
            <button className="secondary-btn" type="button" onClick={handleBuyNow}>
              立即购买
            </button>
            <button
              className={`icon-btn favorite-btn ${collected ? 'collected' : ''}`}
              type="button"
              onClick={() => setCollected((prev) => !prev)}
            >
              {collected ? '★ 已收藏' : '☆ 收藏'}
            </button>
          </div>

          {buyNotice && <div className="buy-notice">{buyNotice}</div>}
        </div>
      </div>

      <div className="detail-tabs">
        <div className="tab-list">
          {['简介', '目录', '评价', '详情参数'].map((tab) => (
            <button
              key={tab}
              type="button"
              className={`tab ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>
        <div className="tab-panel">{renderTabContent()}</div>
      </div>
    </div>
  )
}

export default BookDetailPage

