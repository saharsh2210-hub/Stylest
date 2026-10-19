import { useCallback, useEffect, useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  ArrowDownUp, ArrowRight, CalendarDays, Check, ChevronDown, CircleHelp,
  CloudSun, Grid2X2, Heart, History, LayoutDashboard, List, LoaderCircle,
  Menu, Pencil, Plus, Search, Shirt, SlidersHorizontal, Sparkles, Trash2, WashingMachine,
  X,
} from 'lucide-react'
import { Link, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import EditItemModal from './EditItemModal.jsx'
import './App.css'

const API = import.meta.env.VITE_API_URL || (
  import.meta.env.DEV
    ? `${window.location.protocol}//${window.location.hostname}:8001`
    : window.location.origin
)
const AESTHETICS = [
  'Formal / College', 'Smart Casual', 'Streetwear', 'Old Money', 'Minimalist',
  'Casual', 'Business Casual', 'Party / Going Out', 'Monochrome', 'Vintage', 'Summer', 'Winter',
]
const CATEGORIES = [
  'Shirts', 'T-shirts', 'Polo shirts', 'Hoodies', 'Sweaters', 'Jackets', 'Jeans',
  'Formal trousers', 'Cargo pants', 'Shorts', 'Sneakers', 'Formal shoes', 'Boots',
  'Belts', 'Watches', 'Other accessories',
]
const NAVIGATION = [
  { label: 'Dashboard', to: '/', icon: LayoutDashboard },
  { label: 'My Wardrobe', to: '/wardrobe', icon: Shirt },
  { label: 'Generate Outfit', to: '/generate', icon: Sparkles },
  { label: 'Outfit Planner', to: '/planner', icon: CalendarDays },
  { label: 'Favorites', to: '/favorites', icon: Heart },
  { label: 'Laundry Manager', to: '/laundry', icon: WashingMachine },
  { label: 'Outfit History', to: '/history', icon: History },
]

function isToday(value) {
  return value && new Date(value).toDateString() === new Date().toDateString()
}

async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, { credentials: 'include', ...options })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = body.detail
    throw new Error(typeof detail === 'string' ? detail : detail?.message || `Request failed (${response.status})`)
  }
  if (response.status === 204) return null
  return response.json()
}

function imageUrl(path) {
  if (!path) return null
  return path.startsWith('http') ? path : `${API}${path}`
}

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [auth, setAuth] = useState({ loading: true, authenticated: false, error: '' })
  const location = useLocation()

  useEffect(() => {
    let active = true
    const timer = window.setTimeout(() => {
      api('/api/auth/session')
        .then((session) => {
          if (active) setAuth({ loading: false, authenticated: session.authenticated, error: '' })
        })
        .catch((error) => {
          if (active) setAuth({ loading: false, authenticated: false, error: error.message })
        })
    }, 0)
    return () => {
      active = false
      window.clearTimeout(timer)
    }
  }, [])

  if (auth.loading) return <div className="auth-loading"><span className="brand-mark"><span /></span><span className="eyebrow">OPENING YOUR WARDROBE</span></div>
  if (!auth.authenticated) {
    return <LoginPage
      initialError={auth.error}
      onAuthenticated={() => setAuth({ loading: false, authenticated: true, error: '' })}
    />
  }

  const signOut = async () => {
    try {
      await api('/api/auth/logout', { method: 'POST' })
      setAuth({ loading: false, authenticated: false, error: '' })
    } catch (error) {
      setAuth({ loading: false, authenticated: false, error: error.message })
    }
  }

  return (
    <div className="app-shell">
      <AnimatePresence>
        {sidebarOpen && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setSidebarOpen(false)} />}
      </AnimatePresence>
      <Sidebar open={sidebarOpen} onNavigate={() => setSidebarOpen(false)} />
      <main className="main-area">
        <header className="topbar">
          <button className="icon-button mobile-menu" aria-label="Open navigation" onClick={() => setSidebarOpen(true)}><Menu size={19} /></button>
          <div className="crumb"><span>FITCHECK</span><span className="crumb-slash">/</span><span>{NAVIGATION.find((item) => item.to === location.pathname)?.label || 'Settings'}</span></div>
          <div className="topbar-right">
            <div className="weather-pill"><CloudSun size={16} /><span>Dress for your day</span></div>
            <Link to="/settings" className="avatar" aria-label="Open settings">S</Link>
          </div>
        </header>
        <div className="page-container">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/wardrobe" element={<WardrobePage />} />
            <Route path="/generate" element={<GeneratePage />} />
            <Route path="/planner" element={<OutfitCollection title="Outfit planner" subtitle="Your upcoming looks, thoughtfully planned." filter="planned" />} />
            <Route path="/favorites" element={<OutfitCollection title="Your favorites" subtitle="The combinations worth wearing again." favorite />} />
            <Route path="/laundry" element={<LaundryPage />} />
            <Route path="/history" element={<OutfitCollection title="Outfit history" subtitle="A little look back at what you have worn." filter="worn" />} />
            <Route path="/settings" element={<SettingsPage onSignOut={signOut} />} />
            <Route path="*" element={<Dashboard />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}

function LoginPage({ initialError, onAuthenticated }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState(initialError)
  const [busy, setBusy] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await api('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })
      onAuthenticated()
    } catch (exception) {
      setError(exception.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="login-page">
      <div className="login-card">
        <Link to="/" className="brand login-brand" aria-label="FITCHECK">
          <span className="brand-mark"><span /></span>
          <span className="brand-word">fitcheck<span>.</span><small>YOUR PERSONAL STYLIST</small></span>
        </Link>
        <span className="eyebrow">A CLOSET THAT'S JUST YOURS</span>
        <h1>Welcome back.</h1>
        <p>Sign in to open your wardrobe and personal looks.</p>
        {error && <div className="notice" role="alert"><CircleHelp size={16} /><span>{error}</span></div>}
        <form onSubmit={submit}>
          <label className="control-label">Your password
            <input
              autoComplete="current-password"
              autoFocus
              required
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          <button className="button button-primary generate-button" disabled={busy}>
            {busy ? <LoaderCircle className="spin" size={16} /> : null}
            {busy ? 'Signing in…' : 'Open my wardrobe'}
            {!busy && <ArrowRight size={15} />}
          </button>
        </form>
        <span className="login-private"><Heart size={13} /> Your wardrobe is private to you.</span>
      </div>
    </main>
  )
}

function Sidebar({ open, onNavigate }) {
  return (
    <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
      <Link to="/" className="brand" aria-label="FITCHECK home" onClick={onNavigate}>
        <span className="brand-mark"><span /></span>
        <span className="brand-word">fitcheck<span>.</span><small>YOUR PERSONAL STYLIST</small></span>
      </Link>
      <div className="side-label">MENU</div>
      <nav className="navigation" aria-label="Main navigation">
        {NAVIGATION.map(({ label, to, icon: Icon }) => (
          <NavLink key={to} to={to} end={to === '/'} onClick={onNavigate} className={({ isActive }) => `nav-link ${isActive ? 'nav-active' : ''}`}>
            <Icon size={18} strokeWidth={1.8} /><span>{label}</span>
            {label === 'Generate Outfit' && <span className="nav-spark">✳</span>}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="stylist-card">
          <span className="stylist-icon"><Sparkles size={16} /></span>
          <p>Your wardrobe,<br />with a little more <em>inspiration.</em></p>
          <Link to="/generate" onClick={onNavigate}>Meet your stylist <ArrowRight size={14} /></Link>
        </div>
        <NavLink to="/settings" onClick={onNavigate} className={({ isActive }) => `nav-link settings-link ${isActive ? 'nav-active' : ''}`}>
          <SlidersHorizontal size={18} /><span>Settings</span>
        </NavLink>
        <div className="profile-row"><div className="avatar avatar-large">S</div><div><strong>Your closet</strong><span>Personal wardrobe</span></div><ChevronDown size={15} className="profile-chevron" /></div>
      </div>
    </aside>
  )
}

function PageHeading({ eyebrow, title, subtitle, action }) {
  return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{subtitle && <p>{subtitle}</p>}</div>{action}</div>
}

function EmptyWardrobe({ onAdd, compact = false }) {
  return (
    <div className={`empty-wardrobe ${compact ? 'empty-compact' : ''}`}>
      <div className="empty-illustration"><Shirt size={28} strokeWidth={1.4} /><span className="empty-orbit">✦</span></div>
      <span className="eyebrow">A FRESH START</span>
      <h2>Your wardrobe, your rules.</h2>
      <p>Add a few pieces you love and FITCHECK will start building outfits from your actual closet.</p>
      <button className="button button-primary" onClick={onAdd}><Plus size={16} /> Add your first item</button>
    </div>
  )
}

function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [items, setItems] = useState([])
  const [outfits, setOutfits] = useState([])
  const [recentOutfits, setRecentOutfits] = useState([])
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  const refresh = useCallback(async () => {
    try {
      const [nextStats, nextItems, nextOutfits, nextRecentOutfits] = await Promise.all([
        api('/api/wardrobe/stats'), api('/api/wardrobe'), api('/api/outfits'),
        api('/api/outfits?status_filter=worn'),
      ])
      setStats(nextStats)
      setItems(nextItems)
      setOutfits(nextOutfits)
      setRecentOutfits(nextRecentOutfits)
      setMessage('')
    } catch (error) { setMessage(error.message) }
  }, [])
  useEffect(() => {
    const timer = window.setTimeout(() => { void refresh() }, 0)
    return () => window.clearTimeout(timer)
  }, [refresh])

  const generateToday = async () => {
    setBusy(true)
    setMessage('')
    try {
      await api('/api/outfits/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ aesthetic: 'Casual', occasion: 'Everyday' }) })
      await refresh()
    } catch (error) { setMessage(error.message) }
    finally { setBusy(false) }
  }

  const todaysFit = outfits.find((outfit) => isToday(outfit.created_at))
  return (
    <>
      <PageHeading eyebrow="YOUR STYLE, AT A GLANCE" title="Good things to wear." subtitle="A considered closet makes getting dressed feel easy." action={<button className="button button-primary" onClick={() => navigate('/wardrobe')}><Plus size={16} /> Add to wardrobe</button>} />
      {message && <Notice message={message} />}
      <section className="dashboard-hero">
        <div className="hero-copy"><div className="hero-kicker"><Sparkles size={14} /> YOUR DAILY EDIT</div><h2>{todaysFit ? 'A look, made for you.' : 'What feels like you today?'}</h2><p>{todaysFit ? `Your ${todaysFit.aesthetic.toLowerCase()} look is ready. Every piece comes from your wardrobe.` : 'Tell us your mood. We’ll put together a look from pieces you already own.'}</p><button className="button button-light" disabled={busy || !items.length} onClick={todaysFit ? () => navigate('/generate') : generateToday}>{busy ? <LoaderCircle className="spin" size={16} /> : <Sparkles size={16} />}{items.length ? (todaysFit ? 'Explore today’s fit' : 'Find my fit') : 'Add clothes to get started'}<ArrowRight size={15} /></button></div>
        <div className="hero-visual"><div className="hero-ring ring-one" /><div className="hero-ring ring-two" /><div className="hero-star star-one">✳</div><div className="hero-star star-two">✦</div><div className="hero-label">THE<br /><strong>EDIT</strong><br />NO. 01</div><div className="hero-caption">MADE FROM YOUR WARDROBE</div></div>
      </section>
      <section className="stats-grid">
        <StatCard label="IN YOUR WARDROBE" value={stats?.total ?? '—'} suffix="pieces" icon={<Shirt size={17} />} />
        <StatCard label="READY TO WEAR" value={stats?.clean ?? '—'} suffix="clean" icon={<Check size={17} />} tone="green" />
        <StatCard label="IN THE LAUNDRY" value={stats ? stats.dirty + stats.in_laundry : '—'} suffix="pieces" icon={<WashingMachine size={17} />} tone="orange" />
        <StatCard label="LOVED LOOKS" value={stats?.favorites ?? '—'} suffix="favorites" icon={<Heart size={17} />} tone="pink" />
      </section>
      <div className="dashboard-columns">
        <section className="panel wardrobe-panel">
          <div className="section-head"><div><span className="eyebrow">THE COLLECTION</span><h2>Recently added</h2></div><button className="text-link" onClick={() => navigate('/wardrobe')}>View wardrobe <ArrowRight size={14} /></button></div>
          {items.length ? <div className="mini-items">{items.slice(0, 4).map((item) => <ItemCard key={item.id} item={item} compact />)}</div> : <EmptyWardrobe compact onAdd={() => navigate('/wardrobe')} />}
        </section>
        <section className="panel color-panel">
          <div className="section-head"><div><span className="eyebrow">A PALETTE OF YOU</span><h2>Wardrobe colors</h2></div></div>
          {stats?.colors?.length ? <><div className="color-bars">{stats.colors.map((color) => <div key={color.name} className="color-bar-row"><span>{color.name}</span><div className="color-track"><span style={{ width: `${Math.max(9, color.count / stats.total * 100)}%`, background: colorHex(color.name) }} /></div><small>{color.count}</small></div>)}</div><div className="color-note"><span className="color-dot" /> Built from pieces you actually own</div></> : <div className="muted-empty"><span className="palette-dots"><i /><i /><i /></span><p>Your colors will show up here once you add a few pieces.</p></div>}
        </section>
      </div>
      <section className="panel weekly-panel"><div className="section-head"><div><span className="eyebrow">A LITTLE LOOK AHEAD</span><h2>Your week, in outfits</h2></div><button className="text-link" onClick={() => navigate('/planner')}>Open planner <ArrowRight size={14} /></button></div>{outfits.some((outfit) => outfit.status === 'planned') ? <OutfitStrip outfits={outfits.filter((outfit) => outfit.status === 'planned').slice(0, 5)} items={items} /> : <div className="plan-empty"><div className="plan-icon"><CalendarDays size={18} /></div><div><strong>Make room for getting dressed.</strong><p>Generate a look you love and add it to your plan.</p></div><button className="button button-outline" onClick={() => navigate('/generate')}>Plan an outfit <ArrowRight size={14} /></button></div>}</section>
      <section className="panel weekly-panel"><div className="section-head"><div><span className="eyebrow">YOUR RECENT ROTATION</span><h2>Recently worn</h2></div><button className="text-link" onClick={() => navigate('/history')}>View history <ArrowRight size={14} /></button></div>{recentOutfits.length ? <OutfitStrip outfits={recentOutfits.slice(0, 5)} items={items} isWorn /> : <div className="plan-empty"><div className="plan-icon"><History size={18} /></div><div><strong>Your first worn look starts here.</strong><p>Mark an outfit as worn and it will become part of your history.</p></div><button className="button button-outline" onClick={() => navigate('/generate')}>Create a look <ArrowRight size={14} /></button></div>}</section>
    </>
  )
}

function StatCard({ label, value, suffix, icon, tone = 'purple' }) {
  return <div className="stat-card"><div className="stat-top"><span>{label}</span><span className={`stat-icon ${tone}`}>{icon}</span></div><div className="stat-value">{value}<small>{suffix}</small></div></div>
}

function WardrobePage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [color, setColor] = useState('')
  const [fit, setFit] = useState('')
  const [aesthetic, setAesthetic] = useState('')
  const [status, setStatus] = useState('')
  const [sort, setSort] = useState('newest')
  const [view, setView] = useState('grid')
  const [modal, setModal] = useState(false)
  const [editingItem, setEditingItem] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (category) params.set('category', category)
      if (color) params.set('color', color)
      if (fit) params.set('fit', fit)
      if (aesthetic) params.set('aesthetic', aesthetic)
      if (status) params.set('laundry_status', status)
      params.set('sort', sort)
      setItems(await api(`/api/wardrobe?${params}`))
      setError('')
    } catch (exception) { setError(exception.message) }
    finally { setLoading(false) }
  }, [search, category, color, fit, aesthetic, status, sort])
  useEffect(() => { const timeout = setTimeout(load, 180); return () => clearTimeout(timeout) }, [load])

  const update = async (id, values) => {
    try { await api(`/api/wardrobe/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values) }); load() }
    catch (exception) { setError(exception.message) }
  }
  const remove = async (id) => {
    if (!window.confirm('Remove this piece from your wardrobe?')) return
    try { await api(`/api/wardrobe/${id}`, { method: 'DELETE' }); load() }
    catch (exception) { setError(exception.message) }
  }

  return (
    <>
      <PageHeading eyebrow="YOUR CLOSET, DIGITIZED" title="My wardrobe." subtitle="Every piece you own, ready for a new point of view." action={<button className="button button-primary" onClick={() => setModal(true)}><Plus size={16} /> Add piece</button>} />
      {error && <Notice message={error} />}
      <div className="wardrobe-tools">
        <label className="search-field"><Search size={16} /><input aria-label="Search wardrobe" placeholder="Search your wardrobe..." value={search} onChange={(event) => setSearch(event.target.value)} /></label>
        <div className="filter-set"><select aria-label="Filter by category" value={category} onChange={(event) => setCategory(event.target.value)}><option value="">All categories</option>{CATEGORIES.map((value) => <option key={value}>{value}</option>)}</select><select aria-label="Filter by color" value={color} onChange={(event) => setColor(event.target.value)}><option value="">All colors</option>{['Black', 'White', 'Gray', 'Navy', 'Beige', 'Brown', 'Blue', 'Green', 'Red'].map((value) => <option key={value}>{value}</option>)}</select><select aria-label="Filter by fit" value={fit} onChange={(event) => setFit(event.target.value)}><option value="">All fits</option>{['Regular', 'Slim', 'Relaxed', 'Oversized', 'Fitted', 'Loose'].map((value) => <option key={value}>{value}</option>)}</select><select aria-label="Filter by aesthetic" value={aesthetic} onChange={(event) => setAesthetic(event.target.value)}><option value="">All aesthetics</option>{AESTHETICS.map((value) => <option key={value}>{value}</option>)}</select><select aria-label="Filter by laundry status" value={status} onChange={(event) => setStatus(event.target.value)}><option value="">All laundry</option><option value="clean">Clean</option><option value="dirty">Dirty</option><option value="in_laundry">In laundry</option></select><select aria-label="Sort wardrobe" value={sort} onChange={(event) => setSort(event.target.value)}><option value="newest">Recently added</option><option value="name">Name A–Z</option><option value="most_worn">Most worn</option></select></div>
        <div className="view-toggle"><button aria-label="Grid view" className={view === 'grid' ? 'selected' : ''} onClick={() => setView('grid')}><Grid2X2 size={16} /></button><button aria-label="List view" className={view === 'list' ? 'selected' : ''} onClick={() => setView('list')}><List size={17} /></button></div>
      </div>
      <div className="result-count"><span>{items.length} {items.length === 1 ? 'piece' : 'pieces'}</span><span><ArrowDownUp size={13} /> {sort === 'newest' ? 'Recently added' : sort === 'name' ? 'Name A–Z' : 'Most worn'}</span></div>
      {loading ? <LoadingState /> : items.length ? <div className={`item-grid ${view === 'list' ? 'list-view' : ''}`}>{items.map((item) => <ItemCard key={item.id} item={item} onFavorite={() => update(item.id, { is_favorite: !item.is_favorite })} onLaundry={(laundry_status) => update(item.id, { laundry_status })} onEdit={() => setEditingItem(item)} onDelete={() => remove(item.id)} list={view === 'list'} />)}</div> : search || category || color || fit || aesthetic || status ? <EmptySearch clear={() => { setSearch(''); setCategory(''); setColor(''); setFit(''); setAesthetic(''); setStatus('') }} /> : <EmptyWardrobe onAdd={() => setModal(true)} />}
      {modal && <AddItemModal onClose={() => setModal(false)} onCreated={() => { setModal(false); load() }} onError={setError} />}
      {editingItem && <EditItemModal item={editingItem} onClose={() => setEditingItem(null)} onSaved={() => { setEditingItem(null); load() }} onError={setError} />}
    </>
  )
}

function ItemCard({ item, compact = false, onFavorite, onLaundry, onEdit, onDelete, list = false }) {
  return <article className={`item-card ${compact ? 'item-compact' : ''} ${list ? 'item-list-card' : ''}`}>
    <div className="item-photo">{item.image_path ? <img src={imageUrl(item.image_path)} alt={item.name} /> : <div className="no-photo"><Shirt size={28} /><span>NO IMAGE</span></div>}<span className={`laundry-badge ${item.is_available ? item.laundry_status : 'unavailable'}`}>{!item.is_available ? 'Unavailable' : item.laundry_status === 'in_laundry' ? 'In laundry' : item.laundry_status}</span>{onFavorite && <button className={`favorite-button ${item.is_favorite ? 'is-favorite' : ''}`} title={item.is_favorite ? 'Remove from favorites' : 'Add to favorites'} aria-label={item.is_favorite ? 'Remove from favorites' : 'Add to favorites'} onClick={onFavorite}><Heart size={16} fill={item.is_favorite ? 'currentColor' : 'none'} /></button>}</div>
    <div className="item-info"><div className="item-name-row"><h3>{item.name}</h3>{item.is_favorite && <Heart className="tiny-heart" size={13} fill="currentColor" />}</div><p>{item.category}{item.subcategory ? ` · ${item.subcategory}` : ''}</p><div className="item-tags"><span><i className="tiny-color" style={{ background: colorHex(item.primary_color) }} />{item.primary_color}</span><span>{item.fit} fit</span></div>{!compact && <div className="item-footer"><span>{item.times_worn} {item.times_worn === 1 ? 'wear' : 'wears'}</span><select aria-label={`Laundry status for ${item.name}`} value={item.laundry_status} onChange={(event) => onLaundry?.(event.target.value)}><option value="clean">Clean</option><option value="dirty">Dirty</option><option value="in_laundry">In laundry</option></select>{onEdit && <button className="delete-button" title="Edit item" aria-label={`Edit ${item.name}`} onClick={onEdit}><Pencil size={14} /></button>}{onDelete && <button className="delete-button" title="Delete item" aria-label={`Delete ${item.name}`} onClick={onDelete}><Trash2 size={15} /></button>}</div>}</div>
  </article>
}

function AddItemModal({ onClose, onCreated, onError }) {
  const [form, setForm] = useState({ name: '', category: 'T-shirts', subcategory: '', primary_color: 'Black', secondary_color: '', fit: 'Regular', pattern: 'Solid', material: '', style: '', laundry_status: 'clean', is_available: true, suitable_occasions: [], compatible_aesthetics: [], seasons: [] })
  const [files, setFiles] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const change = (event) => {
    const value = event.target.type === 'checkbox'
      ? event.target.checked
      : event.target.multiple
        ? Array.from(event.target.selectedOptions, (option) => option.value)
        : event.target.value
    setForm((previous) => ({ ...previous, [event.target.name]: value }))
  }
  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (files.length > 1) {
        const data = new FormData()
        files.forEach((file) => data.append('files', file))
        await api('/api/wardrobe/upload-multiple', { method: 'POST', body: data })
      } else if (files.length === 1) {
        const params = new URLSearchParams({ name: form.name, category: form.category, primary_color: form.primary_color })
        const data = new FormData()
        data.append('file', files[0])
        const item = await api(`/api/wardrobe/upload?${params}`, { method: 'POST', body: data })
        const attributes = Object.fromEntries(
          Object.entries(form).filter(([key]) => !['name', 'category', 'primary_color'].includes(key)),
        )
        await api(`/api/wardrobe/${item.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(attributes) })
      } else {
        await api('/api/wardrobe', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
      }
      onCreated()
    } catch (exception) { setError(exception.message); onError(exception.message) }
    finally { setBusy(false) }
  }
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
      <motion.div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="add-item-title" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
        <div className="modal-head">
          <div><span className="eyebrow">GIVE IT A PLACE</span><h2 id="add-item-title">Add a piece</h2></div>
          <button className="icon-button" aria-label="Close" onClick={onClose}><X size={18} /></button>
        </div>
        <form onSubmit={submit}>
          <label className="upload-drop">
            <input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={(event) => setFiles(Array.from(event.target.files || []).slice(0, 20))} />
            <span className="upload-icon"><Plus size={20} /></span>
            <strong>{files.length ? `${files.length} photo${files.length === 1 ? '' : 's'} selected` : 'Add photo(s) (optional)'}</strong>
            <small>JPEG, PNG, WebP · up to 8 MB each</small>
          </label>
          {files.length > 1 && <p className="form-hint">Bulk upload creates draft pieces named from each filename. You can edit details afterwards.</p>}
          <div className="form-grid">
            <label>Item name<input name="name" required={files.length < 2} maxLength="120" placeholder="e.g. Everyday white tee" value={form.name} onChange={change} /></label>
            <label>Category<select name="category" value={form.category} onChange={change}>{CATEGORIES.map((category) => <option key={category}>{category}</option>)}</select></label>
            <label>Subcategory<input name="subcategory" maxLength="80" placeholder="e.g. Oxford" value={form.subcategory} onChange={change} /></label>
            <label>Primary color<select name="primary_color" value={form.primary_color} onChange={change}>{['Black', 'White', 'Gray', 'Navy', 'Beige', 'Brown', 'Blue', 'Green', 'Red', 'Cream', 'Other'].map((color) => <option key={color}>{color}</option>)}</select></label>
            <label>Secondary color<input name="secondary_color" maxLength="40" placeholder="Optional" value={form.secondary_color} onChange={change} /></label>
            <label>Fit<select name="fit" value={form.fit} onChange={change}>{['Regular', 'Slim', 'Relaxed', 'Oversized', 'Fitted', 'Loose'].map((fit) => <option key={fit}>{fit}</option>)}</select></label>
            <label>Pattern<select name="pattern" value={form.pattern} onChange={change}>{['Solid', 'Striped', 'Checked', 'Graphic', 'Floral', 'Other'].map((pattern) => <option key={pattern}>{pattern}</option>)}</select></label>
            <label>Material<input name="material" maxLength="80" placeholder="e.g. Cotton" value={form.material} onChange={change} /></label>
            <label>Style<input name="style" maxLength="80" placeholder="e.g. Streetwear" value={form.style} onChange={change} /></label>
            <label>Laundry status<select name="laundry_status" value={form.laundry_status} onChange={change}><option value="clean">Clean</option><option value="dirty">Dirty</option><option value="in_laundry">In laundry</option></select></label>
            <label className="check-field"><input name="is_available" type="checkbox" checked={form.is_available} onChange={change} />Available for recommendations</label>
            <label>Suitable occasions<select name="suitable_occasions" multiple value={form.suitable_occasions} onChange={change}>{['Everyday', 'College', 'Work', 'Formal event', 'Date night', 'Party', 'Travel', 'Weekend'].map((value) => <option key={value}>{value}</option>)}</select></label>
            <label>Compatible aesthetics<select name="compatible_aesthetics" multiple value={form.compatible_aesthetics} onChange={change}>{AESTHETICS.map((value) => <option key={value}>{value}</option>)}</select></label>
            <label>Seasons<select name="seasons" multiple value={form.seasons} onChange={change}>{['Spring', 'Summer', 'Autumn', 'Winter'].map((value) => <option key={value}>{value}</option>)}</select></label>
          </div>
          <p className="form-hint">For multi-select fields, hold Ctrl (Windows) while choosing more than one option.</p>
          {error && <Notice message={error} />}
          <div className="modal-actions">
            <button type="button" className="button button-outline" onClick={onClose}>Cancel</button>
            <button className="button button-primary" disabled={busy}>{busy ? <LoaderCircle size={16} className="spin" /> : <Plus size={16} />} Add to wardrobe</button>
          </div>
        </form>
      </motion.div>
    </div>
  )
}

function GeneratePage() {
  const [items, setItems] = useState([])
  const [aesthetic, setAesthetic] = useState('Casual')
  const [occasion, setOccasion] = useState('Everyday')
  const [season, setSeason] = useState('')
  const [outfit, setOutfit] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const refreshItems = useCallback(async () => {
    try {
      const [wardrobe, outfits] = await Promise.all([api('/api/wardrobe'), api('/api/outfits')])
      setItems(wardrobe)
      setOutfit(outfits.find((entry) => isToday(entry.created_at)) || null)
    } catch (exception) { setError(exception.message) }
  }, [])
  useEffect(() => {
    const timer = window.setTimeout(() => { void refreshItems() }, 0)
    return () => window.clearTimeout(timer)
  }, [refreshItems])
  const pieces = useMemo(() => outfit ? outfit.item_ids.map((id) => items.find((item) => item.id === id)).filter(Boolean) : [], [outfit, items])

  const generate = async () => {
    setLoading(true)
    setError('')
    try {
      const result = await api('/api/outfits/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ aesthetic, occasion, season: season || null }) })
      setOutfit(result)
      await refreshItems()
    } catch (exception) { setError(exception.message) }
    finally { setLoading(false) }
  }
  const action = async (path, body) => {
    try { const updated = await api(`/api/outfits/${outfit.id}/${path}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) }); setOutfit(updated) }
    catch (exception) { setError(exception.message) }
  }

  return <>
    <PageHeading eyebrow="YOUR CLOSET, REIMAGINED" title="Find your fit." subtitle="A thoughtful combination, built from what you already own." />
    {error && <Notice message={error} />}
    <div className="generator-layout">
      <section className="panel generator-controls"><div className="section-head"><div><span className="eyebrow">SET THE SCENE</span><h2>What are we dressing for?</h2></div></div><label className="control-label">Aesthetic<select value={aesthetic} onChange={(event) => setAesthetic(event.target.value)}>{AESTHETICS.map((option) => <option key={option}>{option}</option>)}</select></label><label className="control-label">Occasion<select value={occasion} onChange={(event) => setOccasion(event.target.value)}>{['Everyday', 'College', 'Work', 'Formal event', 'Date night', 'Party', 'Travel', 'Weekend'].map((option) => <option key={option}>{option}</option>)}</select></label><label className="control-label">Season / weather<select value={season} onChange={(event) => setSeason(event.target.value)}><option value="">Any season</option>{['Spring', 'Summer', 'Autumn', 'Winter'].map((option) => <option key={option}>{option}</option>)}</select></label><div className="stylist-note"><Sparkles size={16} /><p><strong>Only your closet.</strong> Recommendations use clean, available items you’ve added — never made-up pieces.</p></div><button className="button button-primary generate-button" onClick={generate} disabled={loading || !items.length}>{loading ? <LoaderCircle className="spin" size={17} /> : <Sparkles size={17} />}{outfit ? 'Reroll this look' : 'Generate my outfit'}<ArrowRight size={15} /></button>{!items.length && <p className="form-hint">Your wardrobe is empty. Add a top, bottom and shoes to get started.</p>}</section>
      <section className="outfit-result">{outfit ? <div className="panel result-panel"><div className="result-title-row"><div><span className="eyebrow">YOUR {aesthetic.toUpperCase()} LOOK</span><h2>A look that feels like you.</h2></div><div className="score-badge"><Sparkles size={13} /> {Math.round(outfit.score)}<small>/100</small></div></div><div className="result-pieces">{pieces.map((item) => <div className="result-piece" key={item.id}>{item.image_path ? <img src={imageUrl(item.image_path)} alt={item.name} /> : <div className="no-photo"><Shirt size={24} /></div>}<div><strong>{item.name}</strong><span>{item.category} · {item.primary_color}</span></div></div>)}</div><div className="explanation"><span className="eyebrow">WHY IT WORKS</span>{outfit.explanation.map((line) => <p key={line}><span className="explain-dot">✦</span>{line}</p>)}</div><div className="result-actions"><button className={`button ${outfit.is_favorite ? 'button-loved' : 'button-outline'}`} onClick={() => action('favorite')}><Heart size={16} fill={outfit.is_favorite ? 'currentColor' : 'none'} />{outfit.is_favorite ? 'Saved to favorites' : 'Save this look'}</button><button className="button button-outline" onClick={() => { const date = window.prompt('Plan this look for (YYYY-MM-DD):'); if (date) action('plan', { planned_for: date }) }}><CalendarDays size={15} /> Plan it</button><button className="button button-outline" onClick={() => action('worn')}><Check size={16} /> Wore this</button></div></div> : <div className="result-placeholder"><div className="result-orbit orbit-a" /><div className="result-orbit orbit-b" /><span className="result-spark"><Sparkles size={23} /></span><span className="eyebrow">YOUR NEXT LOOK IS WAITING</span><h2>A new point of view,<br />from your own closet.</h2><p>Choose your mood and let your wardrobe do the talking.</p></div>}</section>
    </div>
  </>
}

function OutfitCollection({ title, subtitle, filter, favorite = false }) {
  const [outfits, setOutfits] = useState([])
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const load = useCallback(async () => {
    try {
      const [allOutfits, wardrobe] = await Promise.all([api(`/api/outfits${favorite ? '?favorite=true' : ''}`), api('/api/wardrobe')])
      setOutfits(filter ? allOutfits.filter((outfit) => outfit.status === filter) : allOutfits)
      setItems(wardrobe)
      setError('')
    } catch (exception) { setError(exception.message) }
  }, [filter, favorite])
  useEffect(() => {
    const timer = window.setTimeout(() => { void load() }, 0)
    return () => window.clearTimeout(timer)
  }, [load])
  const doAction = async (id, action, body = {}) => { try { await api(`/api/outfits/${id}/${action}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }); load() } catch (exception) { setError(exception.message) } }
  return <><PageHeading eyebrow="YOUR PERSONAL LOOKBOOK" title={title} subtitle={subtitle} />{error && <Notice message={error} />}{outfits.length ? <div className="collection-grid">{outfits.map((outfit) => <OutfitCard key={outfit.id} outfit={outfit} items={items} onFavorite={() => doAction(outfit.id, 'favorite')} onWorn={() => doAction(outfit.id, 'worn')} onPlan={() => { const date = window.prompt('Plan for (YYYY-MM-DD):'); if (date) doAction(outfit.id, 'plan', { planned_for: date }) }} />)}</div> : <div className="collection-empty"><div className="empty-illustration"><Sparkles size={25} /></div><span className="eyebrow">NOTHING HERE JUST YET</span><h2>{favorite ? 'Your next favorite is out there.' : filter === 'worn' ? 'Your story starts with a first fit.' : 'Your week is still wide open.'}</h2><p>Generate a look from your real wardrobe, then save, schedule, or wear it.</p><Link to="/generate" className="button button-primary"><Sparkles size={16} /> Create an outfit</Link></div>}</>
}

function OutfitCard({ outfit, items, onFavorite, onWorn, onPlan }) {
  const outfitItems = outfit.item_ids.map((id) => items.find((item) => item.id === id)).filter(Boolean)
  return <article className="outfit-card"><div className="outfit-card-images">{outfitItems.slice(0, 3).map((item) => item.image_path ? <img key={item.id} src={imageUrl(item.image_path)} alt={item.name} /> : <div className="no-photo" key={item.id}><Shirt size={20} /></div>)}</div><div className="outfit-card-content"><div className="outfit-card-kicker"><span>{outfit.aesthetic} · {outfit.occasion}</span><button className={`favorite-button collection-heart ${outfit.is_favorite ? 'is-favorite' : ''}`} onClick={onFavorite} aria-label="Toggle favorite"><Heart size={16} fill={outfit.is_favorite ? 'currentColor' : 'none'} /></button></div><h3>{outfitItems.map((item) => item.name).join(' + ') || 'Wardrobe look'}</h3><p>{outfit.planned_for ? `Planned for ${outfit.planned_for}` : outfit.status === 'worn' ? 'Worn' : 'Created from your wardrobe'}</p><div className="outfit-card-actions"><button onClick={onPlan}><CalendarDays size={14} /> Plan</button><button onClick={onWorn}><Check size={14} /> Wore this</button></div></div></article>
}

function OutfitStrip({ outfits, items, isWorn = false }) {
  return <div className="plan-strip">{outfits.map((outfit) => { const first = items.find((item) => outfit.item_ids.includes(item.id)); const date = isWorn && outfit.worn_at ? new Date(outfit.worn_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : outfit.planned_for; return <div className="plan-day" key={outfit.id}><span>{date || 'Upcoming'}</span>{first?.image_path ? <img src={imageUrl(first.image_path)} alt="" /> : <div className="plan-day-placeholder"><Shirt size={18} /></div>}<strong>{outfit.aesthetic}</strong></div> })}</div>
}

function LaundryPage() {
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const load = useCallback(async () => { try { setItems(await api('/api/wardrobe')); setError('') } catch (exception) { setError(exception.message) } }, [])
  useEffect(() => {
    const timer = window.setTimeout(() => { void load() }, 0)
    return () => window.clearTimeout(timer)
  }, [load])
  const change = async (item, laundry_status) => { try { await api(`/api/wardrobe/${item.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ laundry_status }) }); load() } catch (exception) { setError(exception.message) } }
  const groups = [['clean', 'Ready to wear', 'Fresh, clean pieces for your next look.'], ['dirty', 'Ready for laundry', 'Set these aside for a wash.'], ['in_laundry', 'In the wash', 'These are taking a little breather.']]
  return <><PageHeading eyebrow="CARE FOR YOUR CLOSET" title="Laundry manager." subtitle="A little care keeps your favorite pieces in rotation." />{error && <Notice message={error} />}{groups.map(([status, title, subtitle]) => { const filtered = items.filter((item) => item.laundry_status === status); return <section className="laundry-section" key={status}><div className="laundry-heading"><div><h2>{title}</h2><p>{subtitle}</p></div><span className={`laundry-count ${status}`}>{filtered.length}</span></div>{filtered.length ? <div className="laundry-list">{filtered.map((item) => <div className="laundry-row" key={item.id}>{item.image_path ? <img src={imageUrl(item.image_path)} alt="" /> : <div className="laundry-placeholder"><Shirt size={18} /></div>}<div className="laundry-name"><strong>{item.name}</strong><span>{item.category} · {item.primary_color}</span></div><select aria-label={`Update laundry status for ${item.name}`} value={item.laundry_status} onChange={(event) => change(item, event.target.value)}><option value="clean">Clean</option><option value="dirty">Dirty</option><option value="in_laundry">In laundry</option></select></div>)}</div> : <div className="laundry-empty">{status === 'clean' ? 'Your clean pieces will appear here.' : 'Nothing here right now.'}</div>}</section>})}</>
}

function SettingsPage({ onSignOut }) {
  return (
    <>
      <PageHeading eyebrow="MADE TO FEEL LIKE YOURS" title="Settings." subtitle="A few details about how FITCHECK works." />
      <section className="panel settings-panel">
        <div><span className="eyebrow">YOUR DATA</span><h2>Private by design.</h2><p>Your wardrobe is accessible only after signing in. Photos and wardrobe details are stored using the configured private database and image storage.</p></div>
        <div className="settings-row"><div><strong>AI clothing recognition</strong><p>Manual item entry and rule-based recommendations are available without API keys.</p></div><span className="status-pill">Optional</span></div>
        <div className="settings-row"><div><strong>Outfit recommendations</strong><p>Only clean and available pieces in your wardrobe are considered.</p></div><span className="status-pill status-enabled">On</span></div>
        <div className="settings-row"><div><strong>Sign-in session</strong><p>Your private sign-in stays active on this device for up to 30 days.</p></div><button className="button button-outline" onClick={onSignOut}>Sign out</button></div>
      </section>
    </>
  )
}

function Notice({ message }) {
  return <div className="notice" role="alert"><CircleHelp size={16} /><span>{message}</span></div>
}

function LoadingState() {
  return <div className="loading-state"><LoaderCircle className="spin" size={22} /><span>Gathering your pieces…</span></div>
}

function EmptySearch({ clear }) {
  return <div className="collection-empty search-empty"><Search size={21} /><h2>No pieces found.</h2><p>Try another search or clear your filters.</p><button className="button button-outline" onClick={clear}>Clear filters</button></div>
}

function colorHex(color) {
  return ({ Black: '#242323', White: '#f1eee6', Gray: '#898a8a', Grey: '#898a8a', Navy: '#333f56', Beige: '#c5b49b', Brown: '#80634f', Blue: '#7a94b7', Green: '#7a927f', Red: '#b56b65', Cream: '#e4dcc9', Denim: '#546a82' })[color] || '#bcb6a9'
}

export default App
