import { useCallback, useEffect, useState } from 'react'
import { getAdminOrderDetail, getAdminOrders, shipAdminOrder } from '../api/admin'
import { getAdminUserDetail, getAdminUsers, toggleAdminUser } from '../api/admin'
import { createAdminBook, getAdminBookDetail, getAdminBooks, getAdminCategories, setAdminBookSale, updateAdminBook } from '../api/admin'
import { getAdminDashboardSummary } from '../api/admin'
import { useAuth } from '../auth/AuthContext'
import CategoryManagement from './CategoryManagement'

const statusOptions = [['', '全部'], [1, '待付款'], [2, '待发货'], [3, '已发货'], [4, '已完成'], [5, '已取消']]
const hasPhysical = order => order.items.some(item => item.versionType === 'physical')
const price = value => value === null ? '暂无报价' : `¥${value.toFixed(2)}`
const date = value => { if (!value) return '—'; const parsed = new Date(value); return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleString('zh-CN', { hour12: false }) }
const readableError = error => {
  const value = error?.data?.errors ?? error?.data?.msg ?? error?.message ?? '请求失败'
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.map(item => typeof item === 'string' ? item : JSON.stringify(item)).join('；')
  if (value && typeof value === 'object') return Object.entries(value).map(([key, item]) => `${key}：${Array.isArray(item) ? item.join('、') : String(item)}`).join('；')
  return '请求失败'
}

function Cover({ item }) {
  const [failed, setFailed] = useState(false)
  return <div className="admin-cover">{item?.coverImage && !failed ? <img src={item.coverImage} alt={item.title} onError={() => setFailed(true)} /> : <span>{item?.title?.slice(0, 1) || '书'}</span>}</div>
}

function UserAvatar({ user }) { const [failed, setFailed] = useState(false); return <div className="admin-user-avatar">{user.avatar && !failed ? <img src={user.avatar} alt={user.username || '用户头像'} onError={() => setFailed(true)} /> : <span>{(user.username || '用').slice(0, 1)}</span>}</div> }
const userRole = user => user.isSuperuser ? '超级管理员' : user.isStaff ? '管理员' : '普通用户'
const emptyBookForm = () => ({ title:'', author:'', isbn:'', publisher:'', publishDate:'', coverImage:'', description:'', catalog:'', contentFilePath:'', categoryId:'', isOnSale:true, onShelfDate:'', versions:{ digital:{ enabled:true, price:'', salePrice:'', stock:'99999', isOnSale:true }, physical:{ enabled:false, price:'', salePrice:'', stock:'0', isOnSale:true } } })
const bookFormFrom = book => ({ title:book.title, author:book.author, isbn:book.isbn, publisher:book.publisher, publishDate:book.publishDate, coverImage:book.coverImage || '', description:book.description, catalog:book.catalog, contentFilePath:book.contentFilePath, categoryId:book.categoryId || '', isOnSale:book.isOnSale, onShelfDate:book.onShelfDate, versions:{ digital:{ enabled:false, price:'', salePrice:'', stock:'99999', isOnSale:true }, physical:{ enabled:false, price:'', salePrice:'', stock:'0', isOnSale:true } } })
const BookCover = ({ book }) => { const [failed, setFailed] = useState(false); return <div className="admin-book-cover">{book?.coverImage && !failed ? <img src={book.coverImage} alt={book.title} onError={() => setFailed(true)} /> : <span>{book?.title?.slice(0, 1) || '书'}</span>}</div> }
const makeBookPayload = form => { const versions = Object.entries(form.versions).filter(([, value]) => value.enabled).map(([versionType, value]) => { const priceValue = Number(value.price), saleValue = Number(value.salePrice), stockValue = Number(value.stock); if (!Number.isFinite(priceValue) || priceValue < 0 || !Number.isFinite(saleValue) || saleValue < 0 || saleValue > priceValue || !Number.isSafeInteger(stockValue) || stockValue < 0) throw new Error(`${versionType === 'digital' ? '电子版' : '纸质版'}的价格或库存不合法`); return { version_type:versionType, price:priceValue.toFixed(2), sale_price:saleValue.toFixed(2), stock:stockValue, is_on_sale:Boolean(value.isOnSale) } }); if (!versions.length) throw new Error('至少选择一个版本'); for (const [label, value, max] of [['书名', form.title, 200], ['作者', form.author, 100], ['ISBN', form.isbn, 20], ['出版社', form.publisher, 100]]) if (!String(value).trim() || String(value).trim().length > max) throw new Error(`${label}不能为空或长度不合法`); if (form.categoryId && !Number.isSafeInteger(Number(form.categoryId))) throw new Error('请选择有效分类'); return { title:form.title.trim(), author:form.author.trim(), isbn:form.isbn.trim(), publisher:form.publisher.trim(), publish_date:form.publishDate || null, cover_image:form.coverImage.trim() || null, description:form.description.trim() || null, catalog:form.catalog.trim() || null, content_file_path:form.contentFilePath.trim() || null, category:form.categoryId ? Number(form.categoryId) : null, is_on_sale:Boolean(form.isOnSale), on_shelf_date:form.onShelfDate || null, versions } }
function Dashboard({ go }) { const [summary,setSummary]=useState(null),[loading,setLoading]=useState(true),[refreshing,setRefreshing]=useState(false),[error,setError]=useState(''),[last,setLast]=useState(''); const load=useCallback(async refresh=>{ if(refresh ? refreshing : loading && summary) return; refresh?setRefreshing(true):setLoading(true); setError(''); try{setSummary(await getAdminDashboardSummary());setLast(new Date().toLocaleString('zh-CN',{hour12:false}))}catch(e){setError(readableError(e))}finally{refresh?setRefreshing(false):setLoading(false)}},[loading,refreshing,summary]); useEffect(()=>{const t=window.setTimeout(()=>load(false),0);return()=>window.clearTimeout(t)},[load]); if(loading&&!summary)return <div className="admin-panel">正在加载经营概览……</div>; const s=summary; const status=[['待付款',s?.orders.pending,1],['待发货',s?.orders.submitted,2],['已发货',s?.orders.shipped,3],['已完成',s?.orders.completed,4],['已取消',s?.orders.cancelled,5]]; return <section className="admin-dashboard"><div className="admin-dashboard-header"><h2>经营概览</h2><button className="admin-refresh" disabled={refreshing} onClick={()=>load(true)}>{refreshing?'刷新中……':'刷新数据'}</button><span>页面更新时间：{last||'—'}</span></div>{error&&<div className="admin-error">{error}<button onClick={()=>load(Boolean(s))}>重新加载</button></div>}{s&&<><div className="admin-summary-grid">{[['用户',s.users.total,`启用 ${s.users.active} · 禁用 ${s.users.disabled} · 管理员 ${s.users.staff}`,()=>go('users')],['图书',s.books.total,`上架 ${s.books.onSale} · 下架 ${s.books.offSale} · 电子 ${s.books.digitalVersions} · 纸质 ${s.books.physicalVersions}`,()=>go('books')],['订单',s.orders.total,`待付款 ${s.orders.pending} · 待发货 ${s.orders.submitted} · 已完成 ${s.orders.completed}`,()=>go('orders')],['模拟已支付',s.sales.paidAmount===null?'暂无金额':`¥${s.sales.paidAmount.toFixed(2)}`,`订单 ${s.sales.paidOrderCount} · 纸质 ${s.sales.physicalQuantity} · 电子 ${s.sales.digitalQuantity}`,null]].map(([a,b,c,d])=><button className="admin-summary-card" key={a} onClick={d} disabled={!d}><strong>{a}</strong><span className="admin-summary-value">{b}</span><small>{c}</small></button>)}</div><p className="admin-summary-note">数据来自项目模拟支付状态，不代表真实支付网关到账、利润或可提现收入。</p><div className="admin-order-overview">{status.map(([name,value,code])=><button key={code} onClick={()=>go('orders')}><span>{name}</span><b>{value}</b><i style={{width:`${s.orders.total?value/s.orders.total*100:0}%`}} /></button>)}</div><h3>低库存纸质图书</h3>{s.lowStock.length?<div className="admin-low-stock">{s.lowStock.map(x=><article className="admin-low-stock-item" key={x.versionId}><span>{x.bookTitle}（ID：{x.bookId}）</span><b>{x.stock<0?'数据异常 ':''}{x.stock<=0?'缺货':x.stock<=5?'库存紧张':'库存偏低'}：{x.stock}</b><button onClick={()=>go('books',x.bookId)}>查看图书</button></article>)}</div>:<p>暂无低库存纸质图书</p>}<h3>最近订单</h3>{s.recentOrders.length?<div className="admin-recent-orders">{s.recentOrders.map(x=><article key={x.id}><strong>{x.orderNo}</strong><span>{x.username||'未知用户'} · {x.receiver}</span><span>{x.statusText} · {x.payAmount===null?'暂无金额':`¥${x.payAmount.toFixed(2)}`} · {date(x.createdAt)}</span><button onClick={()=>go('orders',x.id)}>查看详情</button></article>)}</div>:<p>暂无订单</p>}</>}</section> }

function BookManagement({ setNotice, onDirtyChange }) {
  const [filters, setFilters] = useState({ keyword:'', category:'', isOnSale:'' }), [data, setData] = useState({ total:0, page:1, pageSize:20, items:[] }), [categories, setCategories] = useState([]), [loading, setLoading] = useState(false), [error, setError] = useState(''), [detail, setDetail] = useState(null), [detailLoading, setDetailLoading] = useState(false), [form, setForm] = useState(null), [saving, setSaving] = useState(false), [busy, setBusy] = useState(null), [dirty, setDirty] = useState(false)
  const load = useCallback(async (next = filters, page = data.page) => { setLoading(true); setError(''); try { setData(await getAdminBooks({ ...next, isOnSale:next.isOnSale === '' ? undefined : next.isOnSale === 'true', page, pageSize:20 })) } catch (e) { setError(readableError(e)) } finally { setLoading(false) } }, [filters, data.page])
  useEffect(() => { onDirtyChange(dirty) }, [dirty, onDirtyChange])
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { const timer = window.setTimeout(async () => { try { setCategories(await getAdminCategories()) } catch (e) { setError(readableError(e)) }; load() }, 0); return () => window.clearTimeout(timer) }, [])
  const open = async id => { setDetail(null); setDetailLoading(true); setError(''); try { setDetail(await getAdminBookDetail(id)) } catch (e) { setError(e.status === 404 ? '图书不存在或已不可访问' : readableError(e)) } finally { setDetailLoading(false) } }
  const leaveForm = () => { if (dirty && !window.confirm('存在未保存的图书内容，确认放弃吗？')) return; setForm(null); setDirty(false) }
  const edit = book => { const next = bookFormFrom(book); book.versions.forEach(version => { next.versions[version.versionType] = { enabled:true, price:version.price ?? '', salePrice:version.salePrice ?? '', stock:String(version.stock), isOnSale:version.isOnSale } }); setForm(next); setDirty(false) }
  const save = async event => { event.preventDefault(); setSaving(true); setError(''); try { const payload = makeBookPayload(form); const updated = detail?.id ? await updateAdminBook(detail.id, payload) : await createAdminBook(payload); setDetail(updated); setForm(null); setDirty(false); setNotice(detail?.id ? '图书更新成功' : '图书创建成功'); load(filters, data.page) } catch (e) { setError(readableError(e)) } finally { setSaving(false) } }
  const sale = async book => { const next = !book.isOnSale; if (!window.confirm(`确认${next ? '上架' : '下架'}图书《${book.title}》（图书 ID：${book.id}）？${next ? '将恢复公开展示。' : '下架后将不再公开展示，但不会删除版本、订单或购买权限。'}`)) return; setBusy(book.id); try { const updated = await setAdminBookSale(book.id, next); setData(current => ({ ...current, items:current.items.map(item => item.id === updated.id ? updated : item) })); setDetail(current => current?.id === updated.id ? updated : current); setNotice(next ? '图书已上架' : '图书已下架') } catch (e) { setError(readableError(e)) } finally { setBusy(null) } }
  const pages = Math.max(1, Math.ceil(data.total / data.pageSize)); const field = (name, label, type = 'text') => <label>{label}<input type={type} value={form[name]} onChange={e => { setForm({ ...form, [name]:e.target.value }); setDirty(true) }} /></label>
  const version = type => { const value = form.versions[type], label = type === 'digital' ? '电子版' : '纸质版'; return <fieldset className="admin-version-editor"><legend><label><input type="checkbox" checked={value.enabled} onChange={e => { setForm({ ...form, versions:{ ...form.versions, [type]:{ ...value, enabled:e.target.checked } } }); setDirty(true) }} />{label}</label></legend>{value.enabled && <div className="admin-book-grid">{['price','salePrice','stock'].map(key => <label key={key}>{key === 'price' ? '定价' : key === 'salePrice' ? '售价' : '库存'}<input type="number" min="0" step={key === 'stock' ? '1' : '0.01'} value={value[key]} onChange={e => { setForm({ ...form, versions:{ ...form.versions, [type]:{ ...value, [key]:e.target.value } } }); setDirty(true) }} /></label>)}<label><input type="checkbox" checked={value.isOnSale} onChange={e => { setForm({ ...form, versions:{ ...form.versions, [type]:{ ...value, isOnSale:e.target.checked } } }); setDirty(true) }} />版本在售</label></div>}{type === 'digital' && <small>电子版库存仅为模型兼容字段，不表示会扣减库存。</small>}</fieldset> }
  if (form) return <form className="admin-book-form admin-panel" onSubmit={save}><button type="button" onClick={leaveForm}>取消</button><h2>{detail?.id ? '编辑图书' : '新增图书'}</h2><div className="admin-book-grid">{field('title','书名')}{field('author','作者')}{field('isbn','ISBN')}{field('publisher','出版社')}{field('publishDate','出版日期','date')}{field('onShelfDate','上架日期','date')}<label>分类<select value={form.categoryId} onChange={e => { setForm({ ...form, categoryId:e.target.value }); setDirty(true) }}><option value="">未分类</option>{categories.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label><input type="checkbox" checked={form.isOnSale} onChange={e => { setForm({ ...form, isOnSale:e.target.checked }); setDirty(true) }} />图书上架</label>{field('coverImage','封面路径（http(s)、/media 或 media）')}{field('contentFilePath','正文相对路径，例如 books/content/1.txt')}<label>简介<textarea value={form.description} onChange={e => { setForm({ ...form, description:e.target.value }); setDirty(true) }} /></label><label>目录<textarea value={form.catalog} onChange={e => { setForm({ ...form, catalog:e.target.value }); setDirty(true) }} /></label></div><BookCover book={{ title:form.title, coverImage:form.coverImage }} />{version('digital')}{version('physical')}{error && <div className="admin-error">{error}</div>}<button className="admin-primary" disabled={saving}>{saving ? '保存中……' : detail?.id ? '保存修改' : '创建图书'}</button></form>
  if (detailLoading) return <div className="admin-panel">正在加载图书详情……</div>
  if (detail) return <section className="admin-book-detail admin-panel"><button onClick={() => setDetail(null)}>返回图书列表</button><button onClick={() => edit(detail)}>编辑图书</button><button className={detail.isOnSale ? 'admin-danger' : 'admin-primary'} disabled={busy === detail.id} onClick={() => sale(detail)}>{busy === detail.id ? '处理中……' : detail.isOnSale ? '下架' : '重新上架'}</button><h2>{detail.title}</h2><BookCover book={detail} /><p>ID：{detail.id}；作者：{detail.author}；ISBN：{detail.isbn}</p><p>分类：{detail.categoryName || '未分类'}；状态：{detail.isOnSale ? '已上架' : '已下架'}</p><p>销量：{detail.salesCount}；评分：{detail.rating ?? '—'}</p><p>创建：{date(detail.createdAt)}；更新：{date(detail.updatedAt)}</p><p>正文相对路径：{detail.contentFilePath || '无'}；有正文：{detail.hasContent ? '是' : '否'}；可用：{detail.contentAvailable ? '是' : '否'}</p><p>简介：{detail.description || '—'}</p><p>目录：{detail.catalog || '—'}</p>{detail.versions.map(item => <p key={item.versionType}>{item.versionLabel}：定价 {price(item.price)}，售价 {price(item.salePrice)}，库存 {item.stock}，{item.isOnSale ? '在售' : '停售'}</p>)}{error && <div className="admin-error">{error}<button onClick={() => open(detail.id)}>重新加载</button></div>}</section>
  return <><form className="admin-book-toolbar admin-panel" onSubmit={e => { e.preventDefault(); const next = { ...filters, keyword:filters.keyword.trim() }; setFilters(next); load(next, 1) }}><label>搜索<input placeholder="书名、作者或 ISBN" value={filters.keyword} onChange={e => setFilters({ ...filters, keyword:e.target.value })} /></label><label>分类<select value={filters.category} onChange={e => setFilters({ ...filters, category:e.target.value })}><option value="">全部分类</option>{categories.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>状态<select value={filters.isOnSale} onChange={e => setFilters({ ...filters, isOnSale:e.target.value })}><option value="">全部</option><option value="true">已上架</option><option value="false">已下架</option></select></label><button className="admin-primary" disabled={loading}>查询</button><button type="button" disabled={loading} onClick={() => { const next = { keyword:'', category:'', isOnSale:'' }; setFilters(next); load(next, 1) }}>重置</button><button type="button" onClick={() => { setDetail(null); setForm(emptyBookForm()); setDirty(false) }}>新增图书</button></form>{error && <div className="admin-error">{error}<button onClick={() => load()}>重新加载</button></div>}{loading ? <div className="admin-panel">正在加载图书……</div> : !data.items.length ? <div className="admin-empty admin-panel">没有符合条件的图书</div> : <div className="admin-book-list">{data.items.map(book => <article className="admin-book-card" key={book.id}><BookCover book={book} /><div><strong>{book.title}</strong><p>ID：{book.id} · {book.author} · {book.isbn}</p><p>{book.categoryName || '未分类'} · {book.isOnSale ? '已上架' : '已下架'}</p><p>{book.versions.map(item => `${item.versionLabel} ${price(item.salePrice)}${item.versionType === 'physical' ? ` 库存 ${item.stock}` : ''}`).join('；')}</p><p>销量 {book.salesCount} · 评分 {book.rating ?? '—'}</p></div><div className="admin-user-actions"><button onClick={() => open(book.id)}>查看/编辑</button><button className={book.isOnSale ? 'admin-danger' : 'admin-primary'} disabled={busy === book.id} onClick={() => sale(book)}>{busy === book.id ? '处理中……' : book.isOnSale ? '下架' : '重新上架'}</button></div></article>)}</div>}<div className="admin-pagination"><span>第 {data.page} 页，共 {pages} 页，共 {data.total} 本图书</span><button disabled={loading || data.page <= 1} onClick={() => load(filters, data.page - 1)}>上一页</button><button disabled={loading || data.page >= pages} onClick={() => load(filters, data.page + 1)}>下一页</button></div></>
}

function UserManagement({ auth, setNotice }) {
  const [filters, setFilters] = useState({ keyword: '' }), [data, setData] = useState({ total: 0, page: 1, pageSize: 20, items: [] }), [loading, setLoading] = useState(false), [detail, setDetail] = useState(null), [detailLoading, setDetailLoading] = useState(false), [error, setError] = useState(''), [busy, setBusy] = useState(null)
  const load = useCallback(async (next = filters, page = data.page) => { setLoading(true); setError(''); try { setData(await getAdminUsers({ keyword: next.keyword.trim(), page, pageSize: 20 })) } catch (e) { setError(readableError(e)) } finally { setLoading(false) } }, [filters, data.page])
  // The page only loads on entry; subsequent requests are explicitly user-driven.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { const timer = window.setTimeout(() => load(), 0); return () => window.clearTimeout(timer) }, [])
  const open = async id => { setDetail(null); setDetailLoading(true); setError(''); try { setDetail(await getAdminUserDetail(id)) } catch (e) { setError(e.status === 404 ? '用户不存在或已不可访问' : readableError(e)) } finally { setDetailLoading(false) } }
  const toggle = async user => { const next = !user.isActive, action = next ? '启用' : '禁用', text = next ? '启用后该用户可重新登录' : '禁用后该用户将无法继续登录'; if (!window.confirm(`确认${action}用户 ${user.username || '（未设置用户名）'}（用户 ID：${user.id}）？\n${text}`)) return; setBusy(user.id); setError(''); try { const updated = await toggleAdminUser(user.id, next); const value = { ...user, ...updated, isActive: updated.isActive }; setData(current => ({ ...current, items: current.items.map(item => item.id === user.id ? value : item) })); setDetail(current => current?.id === user.id ? { ...current, ...value } : current); setNotice(next ? '用户已启用' : '用户已禁用') } catch (e) { setError(readableError(e)) } finally { setBusy(null) } }
  const pages = Math.max(1, Math.ceil(data.total / data.pageSize)); const go = page => { if (!loading) load(filters, page) }
  if (detailLoading) return <div className="admin-panel">正在加载用户详情……<button onClick={() => setDetail(null)}>返回用户列表</button></div>
  if (detail) return <section className="admin-user-detail admin-panel"><button onClick={() => setDetail(null)}>返回用户列表</button><h2>用户详情</h2><UserAvatar user={detail} /><p>用户 ID：{detail.id ?? ''}</p><p>用户名：{detail.username}</p><p>手机号：{detail.phone}</p><p>邮箱：{detail.email}</p><p>性别：{detail.gender}</p><p>当前状态：{detail.isActive ? '正常' : '已禁用'}</p><p>用户角色：{userRole(detail)}</p><p>是否管理员：{detail.isStaff ? '是' : '否'}</p><p>是否超级管理员：{detail.isSuperuser ? '是' : '否'}</p>{error && <div className="admin-error">{error}<button onClick={() => open(detail.id)}>重新加载</button></div>}</section>
  return <><form className="admin-user-toolbar admin-panel" onSubmit={e => { e.preventDefault(); const next = { keyword: filters.keyword.trim() }; setFilters(next); load(next, 1) }}><label className="admin-user-search">搜索<input placeholder="搜索用户名或手机号" value={filters.keyword} onChange={e => setFilters({ keyword: e.target.value })} /></label><button className="admin-primary" disabled={loading}>查询</button><button type="button" disabled={loading} onClick={() => { const next = { keyword: '' }; setFilters(next); load(next, 1) }}>重置</button></form>{error && <div className="admin-error">{error}<button onClick={() => load()}>重新加载</button></div>}{loading ? <div className="admin-panel">正在加载用户……</div> : !data.items.length ? <div className="admin-empty admin-panel">没有符合条件的用户</div> : <div className="admin-user-list">{data.items.map(user => { const reason = user.id === auth.user?.id ? '当前账号' : user.isSuperuser ? '不可操作超级管理员' : user.isStaff ? '管理员账号不可在此操作' : ''; return <article className="admin-user-card" key={user.id}><UserAvatar user={user} /><div><strong>{user.username}</strong><p>用户 ID：{user.id}</p><p>手机号：{user.phone}</p><p>邮箱：{user.email}</p><span className={`admin-user-status ${user.isActive ? 'active' : 'disabled'}`}>{user.isActive ? '正常' : '已禁用'}</span><span className="admin-user-role">{userRole(user)}</span></div><div className="admin-user-actions"><button disabled={loading || busy === user.id} onClick={() => open(user.id)}>查看详情</button>{reason ? <span>{reason}</span> : <button className={user.isActive ? 'admin-danger' : 'admin-primary'} disabled={busy === user.id} onClick={() => toggle(user)}>{busy === user.id ? (user.isActive ? '禁用中……' : '启用中……') : user.isActive ? '禁用用户' : '启用用户'}</button>}</div></article> })}</div>}<div className="admin-pagination"><span>第 {data.page} 页，共 {pages} 页，共 {data.total} 位用户</span><button disabled={loading || data.page <= 1} onClick={() => go(data.page - 1)}>上一页</button><button disabled={loading || data.page >= pages} onClick={() => go(data.page + 1)}>下一页</button></div><p className="admin-confirm">禁用用户会阻止其后续登录；当前后端是否立即使其已有 JWT 失效，取决于后端认证校验规则。</p></>
}

export default function AdminPortal() {
  const auth = useAuth()
  const [filters, setFilters] = useState({ status: '', orderNo: '', receiver: '' })
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(false)
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [shipping, setShipping] = useState(null)
  const [shipForm, setShipForm] = useState({ expressCompany: '', expressNo: '' })
  const [shipBusy, setShipBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [section, setSection] = useState('dashboard')
  const [bookDirty, setBookDirty] = useState(false)
  const [categoryDirty, setCategoryDirty] = useState(false)
  const isAdmin = Boolean(auth.user?.is_staff || auth.user?.is_superuser)

  const reload = useCallback(async nextFilters => {
    setLoading(true); setError('')
    try { setOrders(await getAdminOrders(nextFilters)) }
    catch (requestError) { setError(requestError.status === 403 ? '管理员权限校验失败' : readableError(requestError)) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => {
    if (!auth.authLoading && isAdmin) {
      const timer = window.setTimeout(() => reload({ status: '', orderNo: '', receiver: '' }), 0)
      return () => window.clearTimeout(timer)
    }
  }, [auth.authLoading, auth.user?.id, isAdmin, reload])

  const login = async event => {
    event.preventDefault()
    const form = event.currentTarget
    const username = form.username.value
    const password = form.password.value
    setError('')
    try { await auth.login({ username, password }) }
    catch (requestError) { setError(readableError(requestError)) }
    finally { form.password.value = '' }
  }
  const query = event => { event.preventDefault(); reload(filters) }
  const reset = () => { const next = { status: '', orderNo: '', receiver: '' }; setFilters(next); reload(next) }
  const changeSection = next => { if ((section === 'books' && bookDirty) || (section === 'categories' && categoryDirty)) { if (!window.confirm('存在未保存的管理内容，确认放弃吗？')) return } setSection(next); setDetail(null); setShipping(null) }
  const dashboardGo = (next, id) => { changeSection(next); if (id && next === 'orders') openDetail(id) }
  const logout = () => { if (((section === 'books' && bookDirty) || (section === 'categories' && categoryDirty)) && !window.confirm('存在未保存的管理内容，确认放弃并退出吗？')) return; setSection('dashboard'); setBookDirty(false); setCategoryDirty(false); auth.logout() }
  const openDetail = async id => {
    setDetail(null); setDetailLoading(true); setError('')
    try { setDetail(await getAdminOrderDetail(id)) }
    catch (requestError) { setError(readableError(requestError)) }
    finally { setDetailLoading(false) }
  }
  const submitShipping = async event => {
    event.preventDefault()
    const expressCompany = shipForm.expressCompany.trim(), expressNo = shipForm.expressNo.trim()
    if (!expressCompany || !expressNo || expressCompany.length > 50 || expressNo.length > 50) return setError('请填写不超过 50 字的快递公司和快递单号')
    if (!window.confirm(`确认订单 ${shipping.orderNo} 发货？快递：${expressCompany}，单号：${expressNo}`)) return
    setShipBusy(true); setError('')
    try {
      const updated = await shipAdminOrder(shipping.id, { expressCompany, expressNo })
      setDetail(updated); setOrders(current => current.map(item => item.id === updated.id ? updated : item))
      setShipping(null); setShipForm({ expressCompany: '', expressNo: '' }); setNotice('发货成功')
    } catch (requestError) { setError(readableError(requestError)) }
    finally { setShipBusy(false) }
  }

  if (auth.authLoading) return <div className="admin-portal"><div className="admin-panel">正在恢复登录状态……</div></div>
  if (!auth.user) return <div className="admin-portal"><form className="admin-login admin-panel" onSubmit={login}><h1>书店管理台</h1><p>使用管理员账号登录</p><label>用户名<input name="username" required /></label><label>密码<input name="password" type="password" required /></label>{(error || auth.authError) && <div className="admin-error">{error || auth.authError}</div>}<button className="admin-primary" type="submit">登录管理台</button><a href="/">返回书店</a></form></div>
  if (!isAdmin) return <div className="admin-portal"><div className="admin-panel"><h1>当前账号没有管理员权限</h1><p>{auth.user.username}</p><button className="admin-primary" onClick={auth.logout}>退出并切换账号</button><a href="/">返回书店</a></div></div>

  const canShip = detail && detail.status === 2 && hasPhysical(detail)
  return <div className="admin-portal">
    <header className="admin-header"><div><strong>书店管理台</strong><span>{auth.user.username} · {auth.user.is_superuser ? '超级管理员' : '管理员'}</span></div><div><a href="/">返回书店</a><button onClick={logout}>退出管理账号</button></div></header>
    <div className="admin-layout"><aside className="admin-sidebar"><button className={section === 'dashboard' ? 'active' : ''} onClick={() => changeSection('dashboard')}>经营概览</button><button className={section === 'orders' ? 'active' : ''} onClick={() => changeSection('orders')}>订单管理</button><button className={section === 'users' ? 'active' : ''} onClick={() => changeSection('users')}>用户管理</button><button className={section === 'books' ? 'active' : ''} onClick={() => changeSection('books')}>图书管理</button><button className={section === 'categories' ? 'active' : ''} onClick={() => changeSection('categories')}>图书分类管理</button></aside><main className="admin-content">
      {notice && <div className="admin-notice">{notice}</div>}
      {section === 'dashboard' ? <Dashboard go={dashboardGo} /> : section === 'users' ? <UserManagement auth={auth} setNotice={setNotice} /> : section === 'books' ? <BookManagement setNotice={setNotice} onDirtyChange={setBookDirty} /> : section === 'categories' ? <CategoryManagement setNotice={setNotice} onDirtyChange={setCategoryDirty} /> : <>
      {error && <div className="admin-error">{error}<button onClick={() => reload(filters)}>重新加载</button></div>}
      {detailLoading ? <div className="admin-panel">订单详情加载中……<button onClick={() => setDetail(null)}>返回订单列表</button></div> : detail ? <section className="admin-detail admin-panel">
        <button onClick={() => { setDetail(null); setShipping(null) }}>返回订单列表</button><h2>订单 {detail.orderNo}</h2>
        <p>用户：{detail.user}；状态：{detail.statusText}</p><p>创建：{date(detail.createdAt)}；支付：{date(detail.payTime)}；发货：{date(detail.shipTime)}</p><p>收货：{date(detail.receiveTime)}；取消：{date(detail.cancelTime)}</p>
        <p>收货人：{detail.receiver} {detail.receiverPhone}</p><p>地址：{detail.receiverAddress || '—'}</p><p>备注：{detail.remark || '—'}</p><p>总金额：{price(detail.totalAmount)}；实付：{price(detail.payAmount)}</p>
        <p>物流：{detail.expressCompany ? `${detail.expressCompany} ${detail.expressNo}` : hasPhysical(detail) ? '待发货' : '电子订单，无需物流'}</p>
        {canShip && <button className="admin-primary" onClick={() => setShipping(detail)}>发货</button>}
        <div className="admin-items">{detail.items.map(item => <article key={item.id}><Cover item={item} /><div><strong>{item.title}</strong><p>{item.author} · {item.versionLabel}</p><p>{price(item.salePrice)} × {item.quantity}，小计 {price(item.subtotal)}</p></div></article>)}</div>
        {shipping && <form className="admin-shipping-form" onSubmit={submitShipping}><h3>订单 {shipping.orderNo} 发货</h3><label>快递公司<input value={shipForm.expressCompany} onChange={event => setShipForm({ ...shipForm, expressCompany: event.target.value })} /></label><label>快递单号<input value={shipForm.expressNo} onChange={event => setShipForm({ ...shipForm, expressNo: event.target.value })} /></label><button className="admin-primary" disabled={shipBusy}>{shipBusy ? '发货中……' : '确认发货'}</button><button type="button" disabled={shipBusy} onClick={() => setShipping(null)}>取消</button></form>}
      </section> : <>
        <form className="admin-filters admin-panel" onSubmit={query}><label>订单状态<select value={filters.status} onChange={event => setFilters({ ...filters, status: event.target.value })}>{statusOptions.map(([value, label]) => <option key={String(value)} value={value}>{label}</option>)}</select></label><label>订单号<input value={filters.orderNo} onChange={event => setFilters({ ...filters, orderNo: event.target.value })} /></label><label>收货人<input value={filters.receiver} onChange={event => setFilters({ ...filters, receiver: event.target.value })} /></label><button className="admin-primary" disabled={loading}>查询</button><button type="button" onClick={reset} disabled={loading}>重置</button></form>
        {loading ? <div className="admin-panel">订单加载中……</div> : !orders.length ? <div className="admin-empty admin-panel">没有符合条件的订单</div> : <div className="admin-order-list">{orders.map(order => { const physical = hasPhysical(order), first = order.items[0]; const logistics = !physical ? '电子订单，无需物流' : order.expressCompany ? `${order.expressCompany} ${order.expressNo}` : order.status === 2 ? '待发货' : '暂无物流信息'; return <article className="admin-order-card" key={order.id}><Cover item={first} /><div><strong>{order.orderNo}</strong><p>{order.user} · {date(order.createdAt)}</p><p>收货人：{order.receiver}</p><p>{order.statusText} · {price(order.payAmount)} · {physical ? '含纸质版' : '纯数字订单'}</p><p>{logistics}</p></div><button onClick={() => openDetail(order.id)}>查看详情</button></article> })}</div>}
      </>}</>}
    </main></div>
  </div>
}
