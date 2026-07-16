import { useEffect, useRef, useState } from 'react'
import { getBookDetail } from '../api/books'
import { summarizeBook } from '../api/ai'
import {
  createBookReview,
  getBookReviews,
  getFavorites,
  recordBrowsingHistory,
  toggleFavorite,
} from '../api/interactions'
import { useAuth } from '../auth/AuthContext'

function BookDetailPage({ book, onBack, onAddToCart, onRequireLogin, onPreview }) {
  const { user, isAuthenticated, authLoading } = useAuth()
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(Boolean(book?.id))
  const [error, setError] = useState('')
  const [selectedVersion, setSelectedVersion] = useState(null)
  const [notice, setNotice] = useState('')
  const [cartBusy, setCartBusy] = useState(false)
  const [coverFailed, setCoverFailed] = useState(false)

  const [summary, setSummary] = useState('')
  const [summaryBusy, setSummaryBusy] = useState(false)
  const [summaryError, setSummaryError] = useState('')

  const [reviews, setReviews] = useState([])
  const [reviewsLoading, setReviewsLoading] = useState(false)
  const [reviewsError, setReviewsError] = useState('')
  const [favorite, setFavorite] = useState(false)
  const [favoriteLoading, setFavoriteLoading] = useState(false)
  const [favoriteBusy, setFavoriteBusy] = useState(false)
  const [rating, setRating] = useState(5)
  const [comment, setComment] = useState('')
  const [reviewBusy, setReviewBusy] = useState(false)
  const [reviewFeedback, setReviewFeedback] = useState(null)
  const historyBookRef = useRef(null)

  useEffect(() => {
    if (!book?.id) return undefined
    let active = true
    getBookDetail(book.id)
      .then(data => { if (active) setDetail(data) })
      .catch(requestError => { if (active) setError(requestError.message) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [book?.id])

  useEffect(() => {
    if (!detail?.id || authLoading) return undefined
    let active = true
    const timer = setTimeout(() => {
      if (!isAuthenticated) {
        setFavorite(false)
        setReviews([])
        setReviewsError('')
        return
      }

      setFavoriteLoading(true)
      setReviewsLoading(true)
      getFavorites(detail.id)
        .then(items => { if (active) setFavorite(items.length > 0) })
        .catch(requestError => { if (active) setNotice(requestError.message) })
        .finally(() => { if (active) setFavoriteLoading(false) })
      getBookReviews(detail.id)
        .then(items => { if (active) setReviews(items) })
        .catch(requestError => { if (active) setReviewsError(requestError.message) })
        .finally(() => { if (active) setReviewsLoading(false) })

      if (historyBookRef.current !== detail.id) {
        historyBookRef.current = detail.id
        recordBrowsingHistory(detail.id).catch(requestError => {
          if (active && requestError.status !== 401) setNotice('浏览记录保存失败')
        })
      }
    }, 0)
    return () => { active = false; clearTimeout(timer) }
  }, [detail?.id, isAuthenticated, authLoading, user?.id])

  if (loading) return <div className="page-card">正在加载图书详情…</div>
  if (error || !detail) return <div className="page-card error-msg">{error || '无法加载图书详情'}<button className="back-btn" onClick={onBack}>返回</button></div>

  const saleVersions = detail.versions?.filter(version => version.is_on_sale !== false) || []
  const currentVersion = selectedVersion && saleVersions.find(version => version.id === selectedVersion.id)
    ? selectedVersion
    : saleVersions.find(version => version.version_type === 'physical') || saleVersions[0] || null
  const canBuy = Boolean(currentVersion) && (currentVersion.version_type === 'digital' || Number(currentVersion.stock) > 0)
  const myReview = reviews.find(review => review.isMine)

  const addSelectedVersion = async openCart => {
    if (!canBuy || cartBusy) return
    setCartBusy(true)
    setNotice('')
    try {
      const result = await onAddToCart(detail, currentVersion, openCart)
      setNotice(result?.message || (openCart ? '已加入购物车' : '加入购物车成功'))
      if (result?.requiresLogin) onRequireLogin?.()
    } catch (requestError) {
      setNotice(requestError.message)
    } finally {
      setCartBusy(false)
    }
  }

  const openPreview = () => {
    if (!detail.hasPreview) {
      setNotice('暂无试读内容')
      return
    }
    if (authLoading) {
      setNotice('正在恢复登录状态，请稍候')
      return
    }
    if (!isAuthenticated) {
      setNotice('请先登录后试读')
      onRequireLogin?.()
      return
    }
    onPreview?.(detail)
  }

  const handleFavorite = async () => {
    if (authLoading || favoriteBusy) return
    if (!isAuthenticated) {
      setNotice('请先登录后收藏')
      onRequireLogin?.()
      return
    }
    setFavoriteBusy(true)
    setNotice('')
    try {
      const result = await toggleFavorite(detail.id)
      setFavorite(result.isFavorite)
      setNotice(result.isFavorite ? '已收藏' : '已取消收藏')
    } catch (requestError) {
      setNotice(requestError.message)
    } finally {
      setFavoriteBusy(false)
    }
  }

  const generateSummary = async () => {
    if (!detail.id || summaryBusy || !(detail.hasPreview || detail.description)) return
    setSummaryBusy(true)
    setSummaryError('')
    try {
      const result = await summarizeBook(detail.id)
      setSummary(result.summary || '')
    } catch (requestError) {
      setSummaryError(requestError.message)
    } finally {
      setSummaryBusy(false)
    }
  }

  const reloadReviews = async () => {
    setReviewsLoading(true)
    setReviewsError('')
    try {
      setReviews(await getBookReviews(detail.id))
    } catch (requestError) {
      setReviewsError(requestError.message)
    } finally {
      setReviewsLoading(false)
    }
  }

  const submitReview = async event => {
    event.preventDefault()
    if (!isAuthenticated) {
      setReviewFeedback({ type: 'error', message: '请先登录后再发表评价' })
      onRequireLogin?.()
      return
    }
    if (rating < 1 || rating > 5 || comment.trim().length > 1000) {
      setReviewFeedback({ type: 'error', message: '评分或评论内容不合法' })
      return
    }
    setReviewBusy(true)
    setReviewFeedback(null)
    try {
      await createBookReview({ bookId: detail.id, rating, comment })
      setComment('')
      setRating(5)
      await reloadReviews()
      setReviewFeedback({ type: 'success', message: '评价提交成功' })
    } catch (requestError) {
      setReviewFeedback({
        type: 'error',
        message: requestError.message || '评价提交失败，请稍后重试',
      })
    } finally {
      setReviewBusy(false)
    }
  }

  return (
    <div className="detail-page">
      <button className="back-btn" onClick={onBack}>返回</button>
      <div className="detail-card detail-grid">
        <div className="detail-cover detail-cover-large" style={{ background: detail.color }}>
          {detail.coverImage && !coverFailed
            ? <img src={detail.coverImage} alt={`${detail.title}封面`} onError={() => setCoverFailed(true)} />
            : <span>{detail.title?.slice(0, 1) || '书'}</span>}
        </div>
        <div className="detail-main">
          <h2>{detail.title}</h2>
          <p className="detail-author">作者：{detail.author || '暂无'}</p>
          <p className="detail-publisher">出版社：{detail.publisher || '暂无'}</p>

          <div className="version-picker">
            <h4>选择版本</h4>
            {saleVersions.length ? saleVersions.map(version => {
              const disabled = version.version_type === 'physical' && Number(version.stock) <= 0
              return (
                <button
                  type="button"
                  key={version.id}
                  disabled={disabled}
                  onClick={() => setSelectedVersion(version)}
                  className={`version-option${currentVersion?.id === version.id ? ' selected' : ''}`}
                >
                  <span>{version.type_label || version.version_type}</span>
                  <span>¥{version.sale_price ?? '暂无'}</span>
                  <span>库存：{version.stock ?? '暂无'}</span>
                </button>
              )
            }) : <p>暂无可购买版本</p>}
          </div>

          <div className="detail-actions-grid">
            <button className="primary-btn" disabled={!canBuy || cartBusy} onClick={() => addSelectedVersion(false)}>{cartBusy ? '处理中…' : '加入购物车'}</button>
            <button className="secondary-btn" disabled={!canBuy || cartBusy} onClick={() => addSelectedVersion(true)}>立即购买</button>
            <button className="secondary-btn" disabled={authLoading || !detail.hasPreview} onClick={openPreview}>{detail.hasPreview ? '试读' : '暂无试读'}</button>
            <button className={`secondary-btn favorite-btn${favorite ? ' collected' : ''}`} disabled={favoriteLoading || favoriteBusy} onClick={handleFavorite}>{favoriteLoading ? '收藏状态加载中…' : favorite ? '★ 已收藏' : '☆ 收藏'}</button>
          </div>
          {notice && <div className="buy-notice">{notice}</div>}
        </div>
      </div>

      <section className="tab-section">
        <h3>图书简介</h3>
        <p>{detail.description || '暂无图书简介'}</p>
      </section>

      <section className="tab-section ai-summary-section">
        <h3>AI 简介</h3>
        <p className="hint-text">基于全书内容生成 AI 推荐语</p>
        <button className="secondary-btn" disabled={summaryBusy || !(detail.hasPreview || detail.description)} onClick={generateSummary}>{summaryBusy ? '正在生成…' : '生成 AI 摘要'}</button>
        {!(detail.hasPreview || detail.description) && <p className="hint-text">该书暂无可供摘要的内容</p>}
        {summaryError && <div className="error-msg">{summaryError}</div>}
        {summary && <div className="summary-content">{summary}</div>}
      </section>

      <section className="tab-section review-section">
        <h3>读者评价</h3>
        {!isAuthenticated && !authLoading ? (
          <div className="page-card"><p>登录后查看和发表评价</p><button className="secondary-btn" onClick={onRequireLogin}>去登录</button></div>
        ) : reviewsLoading ? (
          <p>正在加载评价…</p>
        ) : reviewsError ? (
          <div className="error-msg"><p>{reviewsError}</p><button className="secondary-btn" onClick={reloadReviews}>重试</button></div>
        ) : reviews.length ? reviews.map(review => (
          <article className="review-card" key={review.id}>
            <b>{review.username} {review.isMine && '· 我的评价'}</b>
            <div>{'★'.repeat(review.rating)}{'☆'.repeat(5 - review.rating)}</div>
            <p>{review.comment || '该用户未填写文字评论'}</p>
            <small>{review.createdAt || ''}</small>
          </article>
        )) : <p>暂无评价</p>}

        {isAuthenticated && !reviewsLoading && !myReview && (
          <form className="review-form" onSubmit={submitReview}>
            <h4>发表评价</h4>
            <select value={rating} onChange={event => setRating(Number(event.target.value))}>
              {[1, 2, 3, 4, 5].map(value => <option key={value} value={value}>{value} 星</option>)}
            </select>
            <textarea maxLength={1000} value={comment} onChange={event => setComment(event.target.value)} placeholder="分享你的阅读感受" />
            <small>{comment.length} / 1000</small>
            <button className="primary-btn" disabled={reviewBusy}>{reviewBusy ? '提交中…' : '提交评价'}</button>
          </form>
        )}
        {reviewFeedback && (
          <div
            className={`review-feedback ${reviewFeedback.type}`}
            role={reviewFeedback.type === 'error' ? 'alert' : 'status'}
            aria-live="polite"
          >
            {reviewFeedback.message}
          </div>
        )}
        {myReview && <p className="hint-text">你已评价过这本书。</p>}
      </section>
    </div>
  )
}

export default BookDetailPage
