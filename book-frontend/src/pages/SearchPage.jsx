import { useEffect, useRef, useState } from 'react'
import { getBooks } from '../api/books'

const HISTORY_KEY = 'bookweb_search_history'
const hotWords = ['三体', '活着', '余华', '刘慈欣', '百年孤独']
const priceFilters = [
  { label: '¥0-30', min: 0, max: 30 },
  { label: '¥30-50', min: 30, max: 50 },
  { label: '¥50+', min: 50 },
]
const sortOptions = [
  { label: '综合', ordering: undefined },
  { label: '销量', ordering: '-sales_count' },
  { label: '新品', ordering: '-publish_date' },
  { label: '价格↑', ordering: 'sale_price' },
  { label: '价格↓', ordering: '-sale_price' },
]

function ResultCover({ book }) {
  const [failed, setFailed] = useState(false)
  if (!book.coverImage || failed) return <div className="result-cover" style={{ background: book.color }}>{book.title?.[0] || '书'}</div>
  return <div className="result-cover" style={{ background: book.color }}><img src={book.coverImage} alt={`${book.title}封面`} onError={() => setFailed(true)} /></div>
}

function SearchPage({ onSelectBook, onBack }) {
  const [query, setQuery] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [items, setItems] = useState([])
  const [count, setCount] = useState(0)
  const [next, setNext] = useState(null)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedPrice, setSelectedPrice] = useState(null)
  const [sortBy, setSortBy] = useState('综合')
  const [history, setHistory] = useState(() => {
    try {
      const saved = localStorage.getItem(HISTORY_KEY)
      return Array.isArray(JSON.parse(saved)) ? JSON.parse(saved) : []
    } catch { return [] }
  })
  const [reloadKey, setReloadKey] = useState(0)
  const mountedRef = useRef(false)
  const requestSequenceRef = useRef(0)

  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setSearchTerm(query.trim())
      setPage(1)
    }, 500)
    return () => window.clearTimeout(timeoutId)
  }, [query])

  useEffect(() => {
    if (!searchTerm) return
    const timeoutId = window.setTimeout(() => {
      setHistory(previous => {
        const nextHistory = [searchTerm, ...previous.filter(item => item !== searchTerm)].slice(0, 8)
        localStorage.setItem(HISTORY_KEY, JSON.stringify(nextHistory))
        return nextHistory
      })
    }, 0)
    return () => window.clearTimeout(timeoutId)
  }, [searchTerm])

  useEffect(() => {
    const sequence = ++requestSequenceRef.current
    const selectedSort = sortOptions.find(option => option.label === sortBy)
    const timeoutId = window.setTimeout(() => {
      setLoading(true)
      setError('')
      getBooks({
        page,
        page_size: 10,
        search: searchTerm,
        price_min: selectedPrice?.min,
        price_max: selectedPrice?.max,
        ordering: selectedSort?.ordering,
      })
        .then(data => {
          if (!mountedRef.current || sequence !== requestSequenceRef.current) return
          setItems(data.items)
          setCount(data.count)
          setNext(data.next)
        })
        .catch(requestError => {
          if (!mountedRef.current || sequence !== requestSequenceRef.current) return
          setError(requestError.message || '搜索失败')
          setItems([])
          setCount(0)
          setNext(null)
        })
        .finally(() => {
          if (mountedRef.current && sequence === requestSequenceRef.current) setLoading(false)
        })
    }, 0)
    return () => window.clearTimeout(timeoutId)
  }, [page, reloadKey, searchTerm, selectedPrice, sortBy])

  const choosePrice = (price) => {
    setSelectedPrice(current => current?.label === price?.label ? null : price)
    setPage(1)
  }

  const chooseSort = (label) => {
    setSortBy(label)
    setPage(1)
  }

  const chooseKeyword = (word) => setQuery(word)
  const clearHistory = () => {
    setHistory([])
    localStorage.removeItem(HISTORY_KEY)
  }

  return <div className="search-page">
    <div className="search-header"><button type="button" className="back-btn" onClick={onBack}>← 返回</button><input type="text" value={query} onChange={event => setQuery(event.target.value)} placeholder="请输入书名、作者或 ISBN" /></div>
    <div className="search-block search-history-block"><div className="search-row"><div className="search-label">搜索历史</div><button type="button" className="small-link" onClick={clearHistory}>清空</button></div><div className="tag-list">{history.length ? history.map(word => <button key={word} type="button" className="tag" onClick={() => chooseKeyword(word)}>{word}</button>) : <span className="empty-note">暂无搜索历史</span>}</div></div>
    <div className="search-block"><div className="search-label">热搜推荐</div><div className="tag-list">{hotWords.map(word => <button key={word} type="button" className="tag" onClick={() => chooseKeyword(word)}>{word}</button>)}</div></div>
    <div className="search-block filter-block"><div className="search-label">筛选条件</div><div className="filter-group"><div className="filter-title">价格区间</div><div className="tag-list">{priceFilters.map(price => <button key={price.label} type="button" className={`tag ${selectedPrice?.label === price.label ? 'selected' : ''}`} onClick={() => choosePrice(price)}>{price.label}</button>)}</div></div>{/* 后端提供筛选元数据接口后，再恢复出版社、语种和年份筛选。 */}</div>
    <div className="search-block sort-block"><div className="search-label">排序方式</div><div className="tag-list">{sortOptions.map(option => <button key={option.label} type="button" className={`tag ${sortBy === option.label ? 'selected' : ''}`} onClick={() => chooseSort(option.label)}>{option.label}</button>)}</div></div>
    <div className="search-block result-block"><div className="result-info"><span>搜索结果 {count} 条</span><span>{searchTerm ? `当前搜索：“${searchTerm}”` : '当前显示全部图书'}</span></div>
      {loading ? <div className="empty-note">正在搜索…</div> : error ? <div className="search-error"><p>{error}</p><button type="button" className="secondary-btn" onClick={() => setReloadKey(value => value + 1)}>重新加载</button></div> : <>
        <div className="result-list">{items.map(book => <button type="button" className="result-item" key={book.id} onClick={() => onSelectBook(book)}><ResultCover book={book} /><div className="result-meta"><div className="result-title">{book.title}</div><div className="result-author">作者：{book.author || '暂无'}</div><div className="result-extra"><span>{book.price}</span><span>评分 {book.rating ?? '暂无'}</span></div></div></button>)}</div>
        {!items.length && <div className="empty-note">暂无匹配结果</div>}
        <div className="pagination"><button type="button" disabled={page === 1} onClick={() => setPage(current => current - 1)}>上一页</button><span>第 {page} 页</span><button type="button" disabled={!next} onClick={() => setPage(current => current + 1)}>下一页</button></div>
      </>}
    </div>
  </div>
}

export default SearchPage
