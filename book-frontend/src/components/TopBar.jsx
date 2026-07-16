function TopBar({ title = '智能掌上书店', showSearch = true, onSearchClick }) {
  return (
    <header className="topbar">
      <div className="brand">{title}</div>
      {showSearch && (
        <button className="search-btn" type="button" onClick={onSearchClick}>
          🔍 搜索
        </button>
      )}
    </header>
  )
}

export default TopBar
