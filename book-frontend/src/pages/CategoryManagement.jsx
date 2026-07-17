import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  createAdminCategory,
  deleteAdminCategory,
  getAdminBooks,
  getAdminCategories,
  getAdminCategoryBooks,
  updateAdminCategory,
  updateAdminCategoryBooks,
} from '../api/admin'

const emptyForm = () => ({ name:'', parent:'', sort:'0', description:'', isActive:true })
const formFrom = category => ({ name:category.name, parent:category.parent || '', sort:String(category.sort), description:category.description, isActive:category.isActive })

const readableError = error => {
  const value = error?.data?.errors ?? error?.data?.msg ?? error?.message ?? '请求失败'
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.join('；')
  if (value && typeof value === 'object') return Object.entries(value).map(([key, item]) => `${key}：${Array.isArray(item) ? item.join('、') : String(item)}`).join('；')
  return '请求失败'
}

export default function CategoryManagement({ setNotice, onDirtyChange }) {
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [dirty, setDirty] = useState(false)
  const [saving, setSaving] = useState(false)
  const [selectedId, setSelectedId] = useState(null)
  const [members, setMembers] = useState({ total:0, page:1, pageSize:10, items:[] })
  const [memberLoading, setMemberLoading] = useState(false)
  const [memberKeyword, setMemberKeyword] = useState('')
  const [searchKeyword, setSearchKeyword] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [checkedIds, setCheckedIds] = useState([])
  const [bookBusy, setBookBusy] = useState(false)

  useEffect(() => onDirtyChange?.(dirty), [dirty, onDirtyChange])
  useEffect(() => () => onDirtyChange?.(false), [onDirtyChange])

  const selected = useMemo(() => categories.find(item => item.id === selectedId) || null, [categories, selectedId])
  const memberPages = Math.max(1, Math.ceil(members.total / members.pageSize))

  const loadCategories = useCallback(async () => {
    setLoading(true); setError('')
    try { setCategories(await getAdminCategories()) }
    catch (requestError) { setError(readableError(requestError)) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { const timer = window.setTimeout(loadCategories, 0); return () => window.clearTimeout(timer) }, [loadCategories])

  const loadMembers = useCallback(async (categoryId, keyword = memberKeyword, page = 1) => {
    if (!categoryId) return
    setMemberLoading(true); setError('')
    try { setMembers(await getAdminCategoryBooks(categoryId, { keyword, page, pageSize:10 })) }
    catch (requestError) { setError(readableError(requestError)) }
    finally { setMemberLoading(false) }
  }, [memberKeyword])

  const choose = category => {
    if (dirty && !window.confirm('当前分类字段尚未保存，确认放弃修改吗？')) return
    setSelectedId(category.id); setEditingId(category.id); setForm(formFrom(category)); setDirty(false)
    setMemberKeyword(''); setSearchKeyword(''); setSearchResults([]); setCheckedIds([])
    loadMembers(category.id, '', 1)
  }

  const startCreate = () => {
    if (dirty && !window.confirm('当前分类字段尚未保存，确认放弃修改吗？')) return
    setEditingId('new'); setSelectedId(null); setForm(emptyForm()); setDirty(false); setMembers({ total:0, page:1, pageSize:10, items:[] }); setSearchResults([]); setCheckedIds([])
  }

  const change = patch => { setForm(current => ({ ...current, ...patch })); setDirty(true) }

  const save = async event => {
    event.preventDefault()
    const name = form.name.trim(), description = form.description.trim(), sort = Number(form.sort), parent = form.parent === '' ? null : Number(form.parent)
    if (!name || name.length > 50) return setError('分类名称不能为空且不能超过 50 字')
    if (description.length > 500) return setError('分类说明不能超过 500 字')
    if (!Number.isSafeInteger(sort) || sort < 0) return setError('排序必须是大于等于 0 的整数')
    if (parent !== null && (!Number.isSafeInteger(parent) || parent <= 0)) return setError('请选择有效父分类')
    setSaving(true); setError('')
    try {
      const payload = { name, parent, sort, description, is_active:Boolean(form.isActive) }
      const saved = editingId === 'new' ? await createAdminCategory(payload) : await updateAdminCategory(editingId, payload)
      const nextCategories = await getAdminCategories()
      setCategories(nextCategories); setEditingId(saved.id); setSelectedId(saved.id); setForm(formFrom(saved)); setDirty(false)
      await loadMembers(saved.id, '', 1); setNotice(editingId === 'new' ? '分类创建成功' : '分类修改已保存')
    } catch (requestError) { setError(readableError(requestError)) }
    finally { setSaving(false) }
  }

  const removeCategory = async category => {
    if (category.childCount > 0) return setError(`“${category.name}”仍有 ${category.childCount} 个子分类，请先移动或删除子分类`)
    const text = category.bookCount ? `删除后，分类中的 ${category.bookCount} 本图书会变为“未分类”。` : '该分类当前没有图书。'
    if (!window.confirm(`确认删除分类“${category.name}”？\n${text}`)) return
    setError('')
    try {
      const result = await deleteAdminCategory(category.id)
      if (selectedId === category.id) { setSelectedId(null); setEditingId(null); setForm(emptyForm()); setMembers({ total:0, page:1, pageSize:10, items:[] }) }
      setDirty(false); await loadCategories(); setNotice(`分类已删除${result.affectedBooks ? `，${result.affectedBooks} 本图书已设为未分类` : ''}`)
    } catch (requestError) { setError(readableError(requestError)) }
  }

  const searchBooks = async event => {
    event?.preventDefault(); setSearchLoading(true); setError(''); setCheckedIds([])
    try { const data = await getAdminBooks({ keyword:searchKeyword.trim(), page:1, pageSize:20 }); setSearchResults(data.items) }
    catch (requestError) { setError(readableError(requestError)) }
    finally { setSearchLoading(false) }
  }

  const addBooks = async () => {
    if (!selected || !checkedIds.length) return
    const moving = searchResults.filter(book => checkedIds.includes(book.id) && book.categoryId && book.categoryId !== selected.id)
    if (moving.length && !window.confirm(`选中的图书中有 ${moving.length} 本属于其他分类，继续后将改挂到“${selected.name}”。`)) return
    setBookBusy(true); setError('')
    try {
      const result = await updateAdminCategoryBooks(selected.id, 'add', checkedIds)
      setCheckedIds([]); await Promise.all([loadCategories(), loadMembers(selected.id, memberKeyword, 1), searchBooks()]); setNotice(`已将 ${result.changed} 本图书加入“${selected.name}”`)
    } catch (requestError) { setError(readableError(requestError)) }
    finally { setBookBusy(false) }
  }

  const removeBook = async book => {
    if (!window.confirm(`确认将《${book.title}》移出“${selected.name}”？图书会变为未分类。`)) return
    setBookBusy(true); setError('')
    try {
      await updateAdminCategoryBooks(selected.id, 'remove', [book.id]); await Promise.all([loadCategories(), loadMembers(selected.id, memberKeyword, members.page), searchResults.length ? searchBooks() : Promise.resolve()]); setNotice('图书已移出分类')
    } catch (requestError) { setError(readableError(requestError)) }
    finally { setBookBusy(false) }
  }

  const parentOptions = categories.filter(item => item.id !== editingId)

  return <section className="admin-category-management">
    <div className="admin-category-header"><div><h2>图书分类管理</h2><p>维护父子分类、展示状态，并把图书加入或移出分类。</p></div><button className="admin-primary" onClick={startCreate}>新增分类</button></div>
    {error && <div className="admin-error">{error}<button onClick={() => setError('')}>关闭</button></div>}
    <div className="admin-category-layout">
      <div className="admin-category-list admin-panel">
        <h3>分类列表</h3>
        {loading ? <p>正在加载分类……</p> : !categories.length ? <p className="admin-empty">暂无分类</p> : categories.map(category => <article className={selectedId === category.id ? 'active' : ''} key={category.id}>
          <button className="admin-category-name" onClick={() => choose(category)}><strong>{category.parentName ? `${category.parentName} / ` : ''}{category.name}</strong><span>排序 {category.sort} · 图书 {category.bookCount} · 子分类 {category.childCount}</span></button>
          <span className={category.isActive ? 'admin-category-status active' : 'admin-category-status disabled'}>{category.isActive ? '启用' : '停用'}</span>
          <button className="admin-danger" onClick={() => removeCategory(category)}>删除</button>
        </article>)}
      </div>
      <div className="admin-category-main">
        {editingId ? <form className="admin-category-form admin-panel" onSubmit={save}>
          <h3>{editingId === 'new' ? '新增分类' : `编辑分类：${selected?.name || ''}`}</h3>
          <div className="admin-category-fields"><label>分类名称<input value={form.name} maxLength="50" onChange={event => change({ name:event.target.value })} /></label><label>父分类<select value={form.parent} onChange={event => change({ parent:event.target.value })}><option value="">顶级分类</option>{parentOptions.map(item => <option key={item.id} value={item.id}>{item.parentName ? `${item.parentName} / ` : ''}{item.name}</option>)}</select></label><label>排序<input type="number" min="0" step="1" value={form.sort} onChange={event => change({ sort:event.target.value })} /></label><label className="admin-category-check"><input type="checkbox" checked={form.isActive} onChange={event => change({ isActive:event.target.checked })} />启用并在公开分类入口展示</label><label className="admin-category-description">分类说明<textarea maxLength="500" value={form.description} onChange={event => change({ description:event.target.value })} /></label></div>
          <button className="admin-primary" disabled={saving}>{saving ? '保存中……' : '保存分类'}</button>
        </form> : <div className="admin-panel admin-empty">选择左侧分类进行管理，或点击“新增分类”。</div>}

        {selected && <div className="admin-category-books admin-panel">
          <h3>“{selected.name}”中的图书</h3>
          <form className="admin-category-book-search" onSubmit={event => { event.preventDefault(); loadMembers(selected.id, memberKeyword.trim(), 1) }}><input placeholder="按书名、作者或 ISBN 筛选本分类" value={memberKeyword} onChange={event => setMemberKeyword(event.target.value)} /><button disabled={memberLoading}>筛选</button></form>
          {memberLoading ? <p>正在加载分类图书……</p> : !members.items.length ? <p className="admin-empty">该分类暂无图书</p> : <div className="admin-category-book-list">{members.items.map(book => <article key={book.id}><div><strong>{book.title}</strong><span>{book.author} · {book.isbn} · {book.isOnSale ? '已上架' : '已下架'}</span></div><button className="admin-danger" disabled={bookBusy} onClick={() => removeBook(book)}>移出分类</button></article>)}</div>}
          <div className="admin-pagination"><span>第 {members.page} 页，共 {memberPages} 页，共 {members.total} 本</span><button disabled={memberLoading || members.page <= 1} onClick={() => loadMembers(selected.id, memberKeyword, members.page - 1)}>上一页</button><button disabled={memberLoading || members.page >= memberPages} onClick={() => loadMembers(selected.id, memberKeyword, members.page + 1)}>下一页</button></div>
          <div className="admin-category-add-books"><h3>从图书库加入</h3><form className="admin-category-book-search" onSubmit={searchBooks}><input placeholder="留空可显示最近 20 本图书" value={searchKeyword} onChange={event => setSearchKeyword(event.target.value)} /><button disabled={searchLoading}>搜索图书</button></form>
            {searchLoading ? <p>正在搜索图书……</p> : searchResults.length ? <><div className="admin-category-search-results">{searchResults.map(book => { const already = book.categoryId === selected.id; return <label key={book.id}><input type="checkbox" disabled={already || bookBusy} checked={checkedIds.includes(book.id)} onChange={event => setCheckedIds(current => event.target.checked ? [...current, book.id] : current.filter(id => id !== book.id))} /><span><strong>{book.title}</strong><small>{book.author} · 当前分类：{book.categoryName || '未分类'}{already ? '（已在本分类）' : ''}</small></span></label> })}</div><button className="admin-primary" disabled={bookBusy || !checkedIds.length} onClick={addBooks}>{bookBusy ? '处理中……' : `加入所选图书（${checkedIds.length}）`}</button></> : <p className="admin-confirm">搜索后可批量选择图书；原本属于其他分类的图书会改挂到当前分类。</p>}
          </div>
        </div>}
      </div>
    </div>
  </section>
}
