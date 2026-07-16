import { useEffect, useState } from 'react'
import { getBookshelf } from '../api/orders'
import { useAuth } from '../auth/AuthContext'

function ShelfCover({ book }) {
  const [failed, setFailed] = useState(false)
  return (
    <div className="shelf-cover" aria-label={`${book.title || '图书'}封面`}>
      <span>{book.title?.slice(0, 1) || '书'}</span>
      {book.coverImage && !failed && <img src={book.coverImage} alt={`${book.title || '图书'}封面`} onError={() => setFailed(true)} />}
    </div>
  )
}

function BookshelfPage({ onBack, onRead, onRequireLogin }) { const { isAuthenticated, authLoading, user } = useAuth(); const [books,setBooks]=useState(null); const [error,setError]=useState('')
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(()=>{if(!isAuthenticated||authLoading){setBooks(null);return}let active=true;getBookshelf().then(x=>active&&setBooks(x)).catch(e=>active&&setError(e.message));return()=>{active=false}},[isAuthenticated,authLoading,user?.id])
  if(authLoading)return <div className="page-card">正在恢复登录状态</div>; if(!isAuthenticated)return <div className="page-card">登录后查看我的电子书<button className="primary-btn" onClick={onRequireLogin}>去登录</button></div>; if(error)return <div className="page-card error-msg">{error}<button className="secondary-btn" onClick={()=>setBooks(null)}>重试</button></div>; if(!books)return <div className="page-card">正在加载书架…</div>
  return <div className="bookshelf-page"><button className="back-btn" onClick={onBack}>返回我的</button><h2>我的电子书架</h2>{!books.length?<div className="page-card">书架暂无电子书，购买并支付电子版后会出现在这里。</div>:<div className="bookshelf-grid">{books.map(book=><div className="bookshelf-card" key={book.bookId}><ShelfCover book={book} /><h3>{book.title}</h3><p>{book.author}</p><p>{book.isOnSale?'在售':'已下架 · 已购仍可阅读'}</p><p>{book.purchasedAt ? new Date(book.purchasedAt).toLocaleString() : ''}</p>{book.canRead?<button className="primary-btn" onClick={()=>onRead(book.bookId,{title:book.title,author:book.author})}>阅读全文</button>:<button disabled className="secondary-btn">阅读内容暂不可用</button>}</div>)}</div>}</div>
}
export default BookshelfPage
