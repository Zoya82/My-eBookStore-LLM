const AI_BASE = import.meta.env.VITE_AI_BASE || 'http://localhost:8001'
const REQUEST_TIMEOUT = 30000 // 30 秒超时

/**
 * 通用请求封装
 */
async function fetchAi(endpoint, payload, timeout = REQUEST_TIMEOUT) {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(`${AI_BASE}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload),
      signal: controller.signal
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()

    if (data.success === false) {
      throw new Error(data.message || '服务异常')
    }

    return data
  } catch (error) {
    clearTimeout(timeoutId)

    if (error.name === 'AbortError') {
      throw new Error('请求超时，请检查网络或稍后重试', { cause: error })
    }

    throw new Error(error.message || '网络连接失败，请检查 AI 服务是否已启动', { cause: error })
  }
}

/**
 * 获取智能推荐
 * @param {string} query - 用户的推荐需求描述
 * @returns {Promise} { items: [...], reply: '...' }
 */
export async function getRecommendations(query) {
  return fetchAi('/api/ai/recommend', { query })
}

/**
 * 多轮问答
 * @param {string} message - 用户消息
 * @param {string} sessionId - 会话 ID（可选）
 * @returns {Promise} { reply: '...', session_id: '...' }
 */
export async function chatWithAi(message, sessionId = '') {
  const payload = { message }
  if (sessionId) {
    payload.session_id = sessionId
  }
  return fetchAi('/api/ai/chat', payload)
}

/**
 * 智能摘要（基于全书内容的约 200 字安利体推荐语；无全文时服务端自动降级为简介摘要）
 * @param {number} bookId - 图书 ID
 * @returns {Promise} { summary: '...', source: 'rag'|'full'|'cached'|'intro' }
 */
export async function summarizeBook(bookId) {
  return fetchAi('/api/ai/summary', { book_id: bookId })
}
