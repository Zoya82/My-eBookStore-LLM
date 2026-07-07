import { useEffect, useMemo, useRef, useState } from 'react'
import { mockBooks } from '../data/mockData'

const HISTORY_KEY = 'bookweb_search_history'
const hotWords = ['React', '文学', '算法', '治愈', '少儿']
const priceFilters = [
  { label: '¥0-30', min: 0, max: 30 },
  { label: '¥30-50', min: 30, max: 50 },
  { label: '¥50+', min: 50, max: Infinity },
]
const yearFilters = ['2023', '2022', '2021', '2020']
const publisherFilters = ['晓光出版社', '未来图书', '时代文化']
const languageFilters = ['中文', 'English']
const sortOptions = ['综合', '销量', '新品', '价格↑', '价格↓']

function SearchPage({ onSelectBook, onBack }) {
  const [query, setQuery] = useState('')
  const [history, setHistory] = useState([])
  const [error, setError] = useState('')
  const [selectedPrice, setSelectedPrice] = useState(null)
  const [selectedYear, setSelectedYear] = useState(null)
  const [selectedPublisher, setSelectedPublisher] = useState(null)
  const [selectedLanguage, setSelectedLanguage] = useState(null)
  const [sortBy, setSortBy] = useState('综合')
  const [searchTerm, setSearchTerm] = useState('')
  const debounceRef = useRef(null)

  useEffect(() => {
    const stored = window.localStorage.getItem(HISTORY_KEY)
    if (stored) {
      try {
        setHistory(JSON.parse(stored))
      } catch (err) {
        setHistory([])
      }
    }
  }, [])

  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }

    debounceRef.current = setTimeout(() => {
      setSearchTerm(query.trim())
    }, 500)

    return () => clearTimeout(debounceRef.current)
  }, [query])

  useEffect(() => {
    if (!searchTerm) {
      return
    }
    setError('')
    const nextHistory = [searchTerm, ...history.filter((item) => item !== searchTerm)].slice(0, 8)
    setHistory(nextHistory)
    window.localStorage.setItem(HISTORY_KEY, JSON.stringify(nextHistory))
  }, [searchTerm])

  const handleHotWordClick = (word) => {
    setQuery(word)
    setSearchTerm(word)
  }

  const handleClearHistory = () => {
    setHistory([])
    window.localStorage.removeItem(HISTORY_KEY)
  }

  const handleFilter = (current, setter, value) => {
    setter(current === value ? null : value)
  }

  const results = useMemo(() => {
    const normalized = searchTerm.toLowerCase()
    return mockBooks
      .filter((book) => {
        const matchesQuery = !normalized || [book.title, book.author, book.isbn].some((field) =>
          String(field).toLowerCase().includes(normalized)
        )
        const matchesPrice = !selectedPrice || (book.priceNum >= selectedPrice.min && book.priceNum < selectedPrice.max)
        const matchesYear = !selectedYear || String(book.year) === selectedYear
        const matchesPublisher = !selectedPublisher || book.publisher === selectedPublisher
        const matchesLanguage = !selectedLanguage || book.language === selectedLanguage
        return matchesQuery && matchesPrice && matchesYear && matchesPublisher && matchesLanguage
      })
      .sort((a, b) => {
        switch (sortBy) {
          case '销量':
            return b.sales - a.sales
          case '新品':
            return b.year === a.year ? 0 : b.year > a.year ? -1 : 1
          case '价格↑':
            return a.priceNum - b.priceNum
          case '价格↓':
            return b.priceNum - a.priceNum
          default:
            return 0
        }
      })
  }, [searchTerm, selectedPrice, selectedYear, selectedPublisher, selectedLanguage, sortBy])

  return (
    <div className="search-page">
      <div className="search-header">
        <button type="button" className="back-btn" onClick={onBack}>
          ← 返回
        </button>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="请输入书名、作者或ISBN"
        />
      </div>

      <div className="search-block search-history-block">
        <div className="search-row">
          <div className="search-label">搜索历史</div>
          <button type="button" className="small-link" onClick={handleClearHistory}>
            清空
          </button>
        </div>
        <div className="tag-list">
          {history.length > 0 ? (
            history.map((keyword) => (
              <button
                key={keyword}
                type="button"
                className="tag"
                onClick={() => setQuery(keyword)}
              >
                {keyword}
              </button>
            ))
          ) : (
            <span className="empty-note">暂无搜索历史</span>
          )}
        </div>
      </div>

      <div className="search-block">
        <div className="search-row">
          <div className="search-label">热搜推荐</div>
        </div>
        <div className="tag-list">
          {hotWords.map((word) => (
            <button key={word} type="button" className="tag" onClick={() => handleHotWordClick(word)}>
              {word}
            </button>
          ))}
        </div>
      </div>

      <div className="search-block filter-block">
        <div className="search-label">筛选条件</div>
        <div className="filter-group">
          <div className="filter-title">价格区间</div>
          <div className="tag-list">
            {priceFilters.map((item) => (
              <button
                key={item.label}
                type="button"
                className={`tag ${selectedPrice === item ? 'selected' : ''}`}
                onClick={() => handleFilter(selectedPrice, setSelectedPrice, item)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
        <div className="filter-group">
          <div className="filter-title">出版年份</div>
          <div className="tag-list">
            {yearFilters.map((year) => (
              <button
                key={year}
                type="button"
                className={`tag ${selectedYear === year ? 'selected' : ''}`}
                onClick={() => handleFilter(selectedYear, setSelectedYear, year)}
              >
                {year}
              </button>
            ))}
          </div>
        </div>
        <div className="filter-group">
          <div className="filter-title">出版社</div>
          <div className="tag-list">
            {publisherFilters.map((publisher) => (
              <button
                key={publisher}
                type="button"
                className={`tag ${selectedPublisher === publisher ? 'selected' : ''}`}
                onClick={() => handleFilter(selectedPublisher, setSelectedPublisher, publisher)}
              >
                {publisher}
              </button>
            ))}
          </div>
        </div>
        <div className="filter-group">
          <div className="filter-title">语种</div>
          <div className="tag-list">
            {languageFilters.map((language) => (
              <button
                key={language}
                type="button"
                className={`tag ${selectedLanguage === language ? 'selected' : ''}`}
                onClick={() => handleFilter(selectedLanguage, setSelectedLanguage, language)}
              >
                {language}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="search-block sort-block">
        <div className="search-label">排序方式</div>
        <div className="tag-list">
          {sortOptions.map((option) => (
            <button
              key={option}
              type="button"
              className={`tag ${sortBy === option ? 'selected' : ''}`}
              onClick={() => setSortBy(option)}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      <div className="search-block result-block">
        <div className="result-info">
          <span>搜索结果 {results.length} 条</span>
          <span>{searchTerm ? `当前搜索：“${searchTerm}”` : '请输入关键词开始搜索'}</span>
        </div>
        <div className="result-list">
          {results.map((book) => (
            <div className="result-item" key={book.id} onClick={() => onSelectBook(book)}>
              <div className="result-cover" style={{ background: book.color }}>
                {book.title[0]}
              </div>
              <div className="result-meta">
                <div className="result-title">{book.title}</div>
                <div className="result-author">作者：{book.author}</div>
                <div className="result-extra">
                  <span>¥{book.priceNum.toFixed(2)}</span>
                  <span>评分 {book.rating.toFixed(1)}</span>
                </div>
              </div>
            </div>
          ))}
          {results.length === 0 && (
            <div className="empty-note">暂无匹配结果，换个关键词试试。</div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SearchPage
