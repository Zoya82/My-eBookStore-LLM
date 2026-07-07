import { useEffect, useState } from 'react'
import heroImg from '../assets/hero.png'
import TopBar from '../components/TopBar'
import BookCard from '../components/BookCard'
import BottomNav from '../components/BottomNav'
import CartPage from './CartPage'
import AiRecommendPage from './AiRecommendPage'
import MinePage from './MinePage'
import BookDetailPage from './BookDetailPage'
import SearchPage from './SearchPage'
import { mockBooks } from '../data/mockData'

const bannerSlides = [
  { type: 'image', src: heroImg, title: '新季热销，暖心阅享' },
  { type: 'color', color: '#f2d7b0', title: '限时精选书单' },
  { type: 'color', color: '#e8c5b0', title: '畅销小说推荐' },
  { type: 'color', color: '#d9b899', title: '儿童启蒙好书' }
]

const quickCategories = ['文学', '科技', '教育', '少儿', '经管', '漫画']

function HomePage() {
  const [activeTab, setActiveTab] = useState('首页')
  const [selectedBook, setSelectedBook] = useState(null)
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [bannerIndex, setBannerIndex] = useState(0)
  const [cartItems, setCartItems] = useState([])

  useEffect(() => {
    const interval = setInterval(() => {
      setBannerIndex((prev) => (prev + 1) % bannerSlides.length)
    }, 4500)
    return () => clearInterval(interval)
  }, [])

  const handleSelectBook = (book) => {
    setSelectedBook(book)
    setActiveTab('详情')
  }

  const handleAddToCart = (book) => {
    setCartItems((prev) => {
      const existing = prev.find((item) => item.id === book.id)
      if (existing) {
        return prev.map((item) =>
          item.id === book.id ? { ...item, quantity: item.quantity + 1 } : item
        )
      }
      return [...prev, { ...book, quantity: 1, selected: true, price: Number(book.price.replace('¥', '')) }]
    })
    setActiveTab('购物车')
  }

  const handleOpenSearch = () => {
    setActiveTab('搜索')
    setSelectedCategory(null)
  }

  const handleCategoryClick = (category) => {
    setSelectedCategory(category)
  }

  const handleUpdateQuantity = (id, quantity) => {
    setCartItems((prev) =>
      prev
        .map((item) => (item.id === id ? { ...item, quantity: Math.max(1, quantity) } : item))
        .filter((item) => item.quantity > 0)
    )
  }

  const handleToggleSelect = (id) => {
    setCartItems((prev) => prev.map((item) => (item.id === id ? { ...item, selected: !item.selected } : item)))
  }

  const handleRemove = (id) => {
    setCartItems((prev) => prev.filter((item) => item.id !== id))
  }

  const categoryBooks = selectedCategory ? mockBooks.slice(0, 4) : []

  const renderContent = () => {
    if (activeTab === '详情') {
      return <BookDetailPage book={selectedBook} onBack={() => setActiveTab('首页')} onAddToCart={handleAddToCart} />
    }

    switch (activeTab) {
      case '购物车':
        return <CartPage items={cartItems} onUpdateQuantity={handleUpdateQuantity} onToggleSelect={handleToggleSelect} onRemove={handleRemove} />
      case '大模型对话':
        return <AiRecommendPage />
      case '我的':
        return <MinePage />
      case '搜索':
        return <SearchPage onSelectBook={handleSelectBook} onBack={() => setActiveTab('首页')} />
      case '首页':
      default:
        return (
          <>
            <section className="banner">
              <div className="banner-carousel">
                {bannerSlides.map((slide, index) => (
                  <div
                    key={slide.title}
                    className={`banner-card${index === bannerIndex ? ' active' : ''}`}
                    style={
                      slide.type === 'image'
                        ? { backgroundImage: `url(${slide.src})` }
                        : { background: slide.color }
                    }
                  >
                    <div className="banner-text">{slide.title}</div>
                  </div>
                ))}
              </div>
              <div className="banner-dots">
                {bannerSlides.map((_, index) => (
                  <button
                    key={index}
                    type="button"
                    className={index === bannerIndex ? 'dot active' : 'dot'}
                    onClick={() => setBannerIndex(index)}
                  />
                ))}
              </div>
            </section>

            <section className="section categories-grid">
              <h3>快捷分类</h3>
              <div className="category-grid">
                {quickCategories.map((category) => (
                  <button className="category-card" key={category} onClick={() => handleCategoryClick(category)}>
                    <div className="category-icon">📚</div>
                    <div>{category}</div>
                  </button>
                ))}
              </div>
            </section>

            {selectedCategory && (
              <section className="section category-results">
                <div className="section-header">
                  <h3>{selectedCategory} 好书推荐</h3>
                  <button className="see-more" type="button" onClick={() => setSelectedCategory(null)}>
                    关闭
                  </button>
                </div>
                <div className="book-row scroll-list">
                  {categoryBooks.map((book) => (
                    <BookCard key={book.id} book={book} compact onSelect={handleSelectBook} />
                  ))}
                </div>
              </section>
            )}

            <section className="section">
              <div className="section-header">
                <h3>新书上架</h3>
                <span>查看更多</span>
              </div>
              <div className="book-row scroll-list">
                {mockBooks.slice(0, 6).map((book) => (
                  <BookCard key={book.id} book={book} onSelect={handleSelectBook} />
                ))}
              </div>
            </section>

            <section className="section">
              <div className="section-header">
                <h3>热门推荐</h3>
                <span>热销精选</span>
              </div>
              <div className="book-row scroll-list">
                {mockBooks.slice(2, 8).map((book) => (
                  <BookCard key={book.id} book={book} compact onSelect={handleSelectBook} />
                ))}
              </div>
            </section>
          </>
        )
    }
  }

  return (
    <div className="app-root">
      <div className="device">
        <TopBar
          title={activeTab === '首页' || activeTab === '详情' ? '智能掌上书店' : activeTab}
          showSearch={activeTab === '首页'}
          onSearchClick={handleOpenSearch}
        />

        <main className="main">{renderContent()}</main>

        <BottomNav activeTab={activeTab === '详情' ? '首页' : activeTab} onTabChange={setActiveTab} />
      </div>
    </div>
  )
}

export default HomePage
