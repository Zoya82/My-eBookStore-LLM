import { useState, useRef, useEffect } from 'react'
import { getRecommendations, chatWithAi } from '../api/ai'

const quickPrompts = {
  recommend: '帮我推荐几本适合晚上阅读的暖心小说',
}

function AiRecommendPage() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [messages, setMessages] = useState([])
  const [sessionId, setSessionId] = useState('')
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState('')
  const messagesEndRef = useRef(null)

  const handleSearch = async (e) => {
    e.preventDefault()

    if (!query.trim()) {
      setError('请输入想看的书或阅读兴趣')
      return
    }

    setError('')
    setLoading(true)
    setResult(null)

    try {
      const data = await getRecommendations(query.trim())
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleQuickPrompt = (type) => {
    const prompt = quickPrompts[type]
    setQuery(prompt)
    setError('')
    if (type === 'recommend') {
      setResult(null)
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()

    if (!chatInput.trim()) {
      return
    }

    const userMsg = chatInput.trim()
    setChatInput('')
    setChatError('')
    setMessages((prev) => [...prev, { role: 'user', text: userMsg }])
    setChatLoading(true)

    try {
      const data = await chatWithAi(userMsg, sessionId)
      setMessages((prev) => [...prev, { role: 'ai', text: data.reply }])
      if (data.session_id) {
        setSessionId(data.session_id)
      }
    } catch (err) {
      setChatError(err.message)
    } finally {
      setChatLoading(false)
    }
  }

  const handleNewChat = () => {
    setMessages([])
    setSessionId('')
    setChatInput('')
    setChatError('')
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="ai-page">
      <div className="ai-topbar">
        <div>
          <h2>大模型对话</h2>
          <p className="ai-desc">你可以和 AI 聊天、获取推荐、生成摘要，体验智能书店助手。</p>
        </div>
        <button className="new-chat-btn" type="button" onClick={handleNewChat}>
          新对话
        </button>
      </div>

      <div className="ai-panel">
        <section className="recommend-panel">
          <div className="recommend-header">
            <h3>快速推荐</h3>
            <div className="recommend-actions">
              <button type="button" className="quick-btn" onClick={() => handleQuickPrompt('recommend')}>
                帮我推荐书
              </button>
            </div>
          </div>

          <form onSubmit={handleSearch} className="recommend-form">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="例如：想找一本温暖治愈的小说"
              disabled={loading}
            />
            <button type="submit" disabled={loading}>
              {loading ? '加载中...' : '获取推荐'}
            </button>
          </form>

          {error && <div className="error-msg">{error}</div>}

          {result && (
            <div className="recommend-result">
              {result.items && result.items.length > 0 ? (
                <div className="rec-items">
                  {result.items.map((item, idx) => (
                    <div className="rec-item" key={idx}>
                      <div className="rec-item-header">
                        <div>
                          <div className="rec-title">{item.title}</div>
                          <div className="rec-author">{item.author || '未知作者'}</div>
                        </div>
                        <button
                          type="button"
                          className="detail-link"
                          onClick={() => window.alert(`查看 ${item.title} 详情。`)}
                        >
                          查看详情
                        </button>
                      </div>
                      <div className="rec-reason">{item.reason || item.description || 'AI 推荐理由。'}</div>
                    </div>
                  ))}
                </div>
              ) : result.reply ? (
                <div className="rec-reply">{result.reply}</div>
              ) : null}
            </div>
          )}
        </section>

        <section className="chat-panel">
          <div className="chat-messages" aria-live="polite">
            {messages.length === 0 ? (
              <div className="chat-empty">这里展示你的聊天记录，AI 会智能回复。</div>
            ) : (
              messages.map((msg, idx) => (
                <div className={`chat-msg ${msg.role}`} key={idx}>
                  <div className="msg-bubble">{msg.text}</div>
                </div>
              ))
            )}
            {chatLoading && (
              <div className="chat-msg ai">
                <div className="msg-bubble loading">AI 正在思考...</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {chatError && <div className="error-msg">{chatError}</div>}

          <form onSubmit={handleSendMessage} className="chat-input-area">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="向 AI 提问..."
              disabled={chatLoading}
            />
            <button type="submit" disabled={chatLoading || !chatInput.trim()}>
              {chatLoading ? '发送中...' : '发送'}
            </button>
          </form>
        </section>
      </div>
    </div>
  )
}

export default AiRecommendPage

