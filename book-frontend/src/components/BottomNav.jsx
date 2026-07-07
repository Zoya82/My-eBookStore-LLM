const navItems = ['首页', '购物车', '大模型对话', '我的']

function BottomNav({ activeTab, onTabChange }) {
  return (
    <nav className="bottom-nav">
      {navItems.map((item) => (
        <button
          className={`nav-item${activeTab === item ? ' active' : ''}`}
          key={item}
          onClick={() => onTabChange(item)}
        >
          {item}
        </button>
      ))}
    </nav>
  )
}

export default BottomNav
