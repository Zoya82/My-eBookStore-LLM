function BookCard({ book, compact = false, onSelect }) {
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
        style={{ background: book.color }}
      >
        <div className="cover-initial">{book.title[0]}</div>
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
