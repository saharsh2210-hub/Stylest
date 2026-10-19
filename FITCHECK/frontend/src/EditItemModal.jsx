import { useState } from 'react'
import { LoaderCircle, X } from 'lucide-react'
import { motion } from 'framer-motion'

const AESTHETICS = [
  'Formal / College', 'Smart Casual', 'Streetwear', 'Old Money', 'Minimalist',
  'Casual', 'Business Casual', 'Party / Going Out', 'Monochrome', 'Vintage', 'Summer', 'Winter',
]
const OCCASIONS = ['Everyday', 'College', 'Work', 'Formal event', 'Date night', 'Party', 'Travel', 'Weekend']
const SEASONS = ['Spring', 'Summer', 'Autumn', 'Winter']

export default function EditItemModal({ item, onClose, onSaved, onError }) {
  const [form, setForm] = useState({
    name: item.name,
    category: item.category,
    subcategory: item.subcategory || '',
    primary_color: item.primary_color,
    secondary_color: item.secondary_color || '',
    pattern: item.pattern,
    fit: item.fit,
    material: item.material || '',
    style: item.style || '',
    laundry_status: item.laundry_status,
    is_available: item.is_available,
    suitable_occasions: item.suitable_occasions || [],
    compatible_aesthetics: item.compatible_aesthetics || [],
    seasons: item.seasons || [],
  })
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
      const apiOrigin = import.meta.env.VITE_API_URL || (
        import.meta.env.DEV
          ? `${window.location.protocol}//${window.location.hostname}:8001`
          : window.location.origin
      )
      const response = await fetch(`${apiOrigin}/api/wardrobe/${item.id}`, {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(typeof body.detail === 'string' ? body.detail : body.detail?.message || `Request failed (${response.status})`)
      }
      onSaved()
    } catch (exception) {
      setError(exception.message)
      onError(exception.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
      <motion.div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="edit-item-title" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
        <div className="modal-head">
          <div><span className="eyebrow">YOUR PIECE, YOUR DETAILS</span><h2 id="edit-item-title">Edit wardrobe item</h2></div>
          <button className="icon-button" aria-label="Close" onClick={onClose}><X size={18} /></button>
        </div>
        <form onSubmit={submit}>
          <div className="form-grid">
            <label>Item name<input name="name" required maxLength="120" value={form.name} onChange={change} /></label>
            <label>Category<input name="category" required maxLength="40" value={form.category} onChange={change} /></label>
            <label>Subcategory<input name="subcategory" maxLength="80" value={form.subcategory} onChange={change} /></label>
            <label>Primary color<input name="primary_color" required maxLength="40" value={form.primary_color} onChange={change} /></label>
            <label>Secondary color<input name="secondary_color" maxLength="40" value={form.secondary_color} onChange={change} /></label>
            <label>Pattern<input name="pattern" maxLength="40" value={form.pattern} onChange={change} /></label>
            <label>Fit<input name="fit" maxLength="40" value={form.fit} onChange={change} /></label>
            <label>Material<input name="material" maxLength="80" value={form.material} onChange={change} /></label>
            <label>Style<input name="style" maxLength="80" value={form.style} onChange={change} /></label>
            <label>Laundry status<select name="laundry_status" value={form.laundry_status} onChange={change}><option value="clean">Clean</option><option value="dirty">Dirty</option><option value="in_laundry">In laundry</option></select></label>
            <label className="check-field"><input name="is_available" type="checkbox" checked={form.is_available} onChange={change} />Available for recommendations</label>
            <label>Suitable occasions<select name="suitable_occasions" multiple value={form.suitable_occasions} onChange={change}>{OCCASIONS.map((value) => <option key={value}>{value}</option>)}</select></label>
            <label>Compatible aesthetics<select name="compatible_aesthetics" multiple value={form.compatible_aesthetics} onChange={change}>{AESTHETICS.map((value) => <option key={value}>{value}</option>)}</select></label>
            <label>Seasons<select name="seasons" multiple value={form.seasons} onChange={change}>{SEASONS.map((value) => <option key={value}>{value}</option>)}</select></label>
          </div>
          {error && <div className="notice" role="alert">{error}</div>}
          <p className="form-hint">For multi-select fields, hold Ctrl (Windows) while choosing more than one option.</p>
          <div className="modal-actions">
            <button type="button" className="button button-outline" onClick={onClose}>Cancel</button>
            <button className="button button-primary" disabled={busy}>{busy ? <LoaderCircle size={16} className="spin" /> : null}Save changes</button>
          </div>
        </form>
      </motion.div>
    </div>
  )
}
