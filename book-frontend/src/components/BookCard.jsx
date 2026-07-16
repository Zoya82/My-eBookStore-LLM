import { useState } from 'react'

function BookCard({ book, compact = false, onSelect }) {
  const [imageFailed, setImageFailed] = useState(false)
  const showImage = Boolean(book.coverImage) && !imageFailed
  return (
    <article
      className={compact ? 'book-card small' : 'book-card'}
      onClick={() => onSelect(book)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onSelect(book)
        }
      }}
    >
      <div
        className={`cover${compact ? ' small-cover' : ''}`}
        style={{ background: book.color || '#E8C9A6' }}
      >
        {showImage && <img src={book.coverImage} alt={`${book.title}封面`} onError={() => setImageFailed(true)} />}
        {!showImage && <div className="cover-initial">{book.title?.[0] || '书'}</div>}
      </div>
      <div className={`meta${compact ? ' small-meta' : ''}`}>
        <div className="title">{book.title}</div>
        {!compact && <div className="author">{book.author}</div>}
        <div className="price">{book.price}</div>
      </div>
    </article>
  )
}

export default BookCard
