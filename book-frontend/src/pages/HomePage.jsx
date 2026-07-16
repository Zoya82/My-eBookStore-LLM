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
import OrderConfirmPage from './OrderConfirmPage'
import OrdersPage from './OrdersPage'
import OrderDetailPage from './OrderDetailPage'
import BookshelfPage from './BookshelfPage'
import ReaderPage from './ReaderPage'
import FavoritesPage from './FavoritesPage'
import MyReviewsPage from './MyReviewsPage'
import BrowsingHistoryPage from './BrowsingHistoryPage'
import AddressPage from './AddressPage'
import { getBookCategories, getBooks, getHomeBooks } from '../api/books'
import { addCartItem } from '../api/cart'
import { useAuth } from '../auth/AuthContext'

const tabs = ['首页', '购物车', '大模型对话', '我的']

function HomePage() {
  const [active, setActive] = useState('首页')
  const [book, setBook] = useState(null)
  const [bookReturnPage, setBookReturnPage] = useState('首页')
  const [home, setHome] = useState({ newBooks: [], hotBooks: [] })
  const [categories,setCategories]=useState([]),[selectedCategory,setSelectedCategory]=useState(''),[categoryBooks,setCategoryBooks]=useState([]),[categoryError,setCategoryError]=useState(''),[categoryLoading,setCategoryLoading]=useState(false),[bannerIndex,setBannerIndex]=useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [cartIds, setCartIds] = useState([])
  const [orderId, setOrderId] = useState(null)
  const [reader, setReader] = useState({ id: null, mode: 'preview', fallback: {}, returnPage: '详情' })
  const { isAuthenticated, authLoading } = useAuth()

  useEffect(() => {
    getHomeBooks()
      .then(setHome)
      .catch(requestError => setError(requestError.message))
      .finally(() => setLoading(false))
  }, [])
  useEffect(()=>{getBookCategories().then(setCategories).catch(e=>setCategoryError(e.message))},[])
  useEffect(()=>{let active=true;setCategoryLoading(true);setCategoryError('');getBooks({category:selectedCategory||undefined,page:1,page_size:10}).then(x=>active&&setCategoryBooks(x.items)).catch(e=>active&&setCategoryError(e.message)).finally(()=>active&&setCategoryLoading(false));return()=>{active=false}},[selectedCategory])
  const banners=[...home.newBooks,...home.hotBooks].filter((x,i,a)=>x&&a.findIndex(y=>y.id===x.id)===i).slice(0,5)
  useEffect(()=>{if(banners.length<2||window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;const t=setInterval(()=>setBannerIndex(x=>(x+1)%banners.length),5000);return()=>clearInterval(t)},[banners.length])

  const goMine = () => setActive('我的')
  const openBook = (nextBook, returnPage = active) => {
    setBook(nextBook)
    setBookReturnPage(returnPage)
    setActive('详情')
  }

  const addToCart = async (nextBook, version, openCart) => {
    if (authLoading) return { message: '正在恢复登录状态，请稍候' }
    if (!isAuthenticated) return { requiresLogin: true, message: '请先登录后加入购物车' }
    await addCartItem({ bookId: nextBook.id, versionType: version.version_type, quantity: 1 })
    if (openCart) setActive('购物车')
    return { message: openCart ? '已加入购物车，正在前往购物车' : '已加入购物车' }
  }

  const openPreview = nextBook => {
    if (!isAuthenticated) {
      goMine()
      return
    }
    setReader({ id: nextBook.id, mode: 'preview', fallback: { title: nextBook.title, author: nextBook.author }, returnPage: '详情' })
    setActive('阅读器')
  }

  const renderBookList = list => loading
    ? <div className="status-message">正在加载图书…</div>
    : error
      ? <div className="error-msg">{error}</div>
      : <div className="book-row scroll-list">{list.map(item => <BookCard key={item.id} book={item} onSelect={() => openBook(item, '首页')} />)}</div>

  let content
  if (active === '详情') {
    content = <BookDetailPage key={book?.id ?? 'missing-book'} book={book} onBack={() => setActive(bookReturnPage)} onAddToCart={addToCart} onRequireLogin={goMine} onPreview={openPreview} />
  } else if (active === '收藏') {
    content = <FavoritesPage onBack={goMine} onRequireLogin={goMine} onSelectBook={item => openBook(item, '收藏')} />
  } else if (active === '评价') {
    content = <MyReviewsPage onBack={goMine} onRequireLogin={goMine} onSelectBook={item => openBook(item, '评价')} />
  } else if (active === '历史') {
    content = <BrowsingHistoryPage onBack={goMine} onRequireLogin={goMine} onSelectBook={item => openBook(item, '历史')} />
  } else if (active === '我的') {
    content = <MinePage onOpenFavorites={() => setActive('收藏')} onOpenReviews={() => setActive('评价')} onOpenHistory={() => setActive('历史')} onOpenOrders={() => setActive('订单')} onOpenBookshelf={() => setActive('书架')} onOpenAddresses={() => setActive('收货地址')} />
  } else if (active === '收货地址') {
    content = <AddressPage onBack={goMine} />
  } else if (active === '购物车') {
    content = <CartPage onRequireLogin={goMine} onCheckout={ids => { setCartIds(ids); setActive('确认订单') }} />
  } else if (active === '确认订单') {
    content = <OrderConfirmPage cartItemIds={cartIds} onBack={() => setActive('购物车')} onRequireLogin={goMine} onCreated={order => { setOrderId(order.id); setActive('订单详情') }} />
  } else if (active === '订单') {
    content = <OrdersPage onBack={goMine} onDetail={id => { setOrderId(id); setActive('订单详情') }} onRequireLogin={goMine} />
  } else if (active === '订单详情') {
    content = <OrderDetailPage orderId={orderId} onBack={() => setActive('订单')} />
  } else if (active === '书架') {
    content = <BookshelfPage onBack={goMine} onRequireLogin={goMine} onRead={(id, fallback) => { setReader({ id, mode: 'full', fallback, returnPage: '书架' }); setActive('阅读器') }} />
  } else if (active === '阅读器') {
    content = <ReaderPage bookId={reader.id} mode={reader.mode} fallbackBook={reader.fallback} onBack={() => setActive(reader.returnPage)} onRequireLogin={goMine} />
  } else if (active === '搜索') {
    content = <SearchPage onBack={() => setActive('首页')} onSelectBook={item => openBook(item, '搜索')} />
  } else if (active === '大模型对话') {
    content = <AiRecommendPage />
  } else {
    content = (
      <>
        <section className="banner">{banners.length?<div className="home-banner"><button aria-label="上一张" onClick={()=>setBannerIndex(x=>(x-1+banners.length)%banners.length)}>‹</button><div className="home-banner-slide" onClick={()=>openBook(banners[bannerIndex],'首页')}><img src={banners[bannerIndex].coverImage} alt=""/><div><strong>{banners[bannerIndex].title}</strong><p>{banners[bannerIndex].author} · {banners[bannerIndex].categoryName||'值得一读'}</p><button>查看详情</button></div></div><button aria-label="下一张" onClick={()=>setBannerIndex(x=>(x+1)%banners.length)}>›</button><div className="home-banner-dots">{banners.map((x,i)=><button key={x.id} aria-current={i===bannerIndex} onClick={()=>setBannerIndex(i)} />)}</div></div>:<div className="banner-card active" style={{ backgroundImage: `url(${heroImg})` }}><div className="banner-text">新季热销，暖心阅读</div></div>}</section>
        <section className="section category-showcase"><h3>分类选书</h3><div className="category-tabs"><button className={!selectedCategory?'active':''} onClick={()=>setSelectedCategory('')}>全部</button>{categories.map(x=><button key={x.id} className={String(selectedCategory)===String(x.id)?'active':''} onClick={()=>setSelectedCategory(x.id)}>{x.name} {x.bookCount}</button>)}</div>{categoryLoading?<p>正在加载分类图书…</p>:categoryError?<p className="error-msg">{categoryError}</p>:!categoryBooks.length?<p>该分类暂无在售图书</p>:<div className="book-row scroll-list">{categoryBooks.map(x=><BookCard key={x.id} book={x} onSelect={()=>openBook(x,'首页')}/>)}</div>}</section>
        <section className="section"><h3>新书上架</h3>{renderBookList(home.newBooks)}</section>
        <section className="section"><h3>热门推荐</h3>{renderBookList(home.hotBooks)}</section>
      </>
    )
  }

  const mySubPage = ['收藏', '评价', '历史', '订单', '订单详情', '书架', '收货地址'].includes(active) || (active === '阅读器' && reader.returnPage === '书架')
  const detailFromMy = active === '详情' && ['收藏', '评价', '历史'].includes(bookReturnPage)
  const navActive = tabs.includes(active) ? active : mySubPage || detailFromMy ? '我的' : '首页'
  const title = active === '首页' || active === '详情' ? '智能掌上书店' : active

  return <div className="app-root"><div className="device"><TopBar title={title} showSearch={active === '首页'} onSearchClick={() => setActive('搜索')} /><main className="main">{content}</main><BottomNav activeTab={navActive} onTabChange={setActive} /></div></div>
}

export default HomePage
