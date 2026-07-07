import { useState } from 'react'

function MinePage() {
  const [hint, setHint] = useState('')
  const actions = [
    '我的订单',
    '我的收藏',
    '浏览历史',
    '个人信息设置',
    '收货地址管理',
  ]

  const handleAction = (label) => {
    setHint(`已进入「${label}」占位页面，可根据需求继续扩展。 `)
  }

  return (
    <div className="mine-page">
      <div className="mine-header">
        <div className="avatar">书</div>
        <div className="user-info">
          <div className="nickname">秋日书友</div>
          <div className="member-tag">已注册用户 · 金牌会员</div>
        </div>
      </div>

      <div className="mine-actions">
        {actions.map((action) => (
          <button key={action} type="button" className="mine-action" onClick={() => handleAction(action)}>
            {action}
          </button>
        ))}
      </div>

      {hint && <div className="mine-hint">{hint}</div>}

      <button className="logout-btn" type="button" onClick={() => setHint('已退出登录，占位提示。')}>
        退出登录
      </button>
    </div>
  )
}

export default MinePage
