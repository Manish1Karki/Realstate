import { useEffect, useState } from 'react'
import AccountMenu from './AccountMenu'
import './AskingPriceRange.css'

const API = (import.meta.env.VITE_PROPERTY_API_URL || '').replace(/\/$/, '')
const format = value => `NPR ${(value / 1e5).toLocaleString('en', { maximumFractionDigits: 2 })} lakh`
const surfaces = { asphalt: 'Asphalt / pitched', concrete: 'Concrete / dhalan', gravel: 'Gravel', earth: 'Earth / unpaved' }
const startingForm = { mode: 'example', neighbourhood: 'Banasthali', size_aana: '4', road_width_ft: '16', road_surface: 'asphalt', frontage: 'inner' }

async function compare(form, signal) {
  const response = await fetch(`${API}/api/asking-range`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, signal,
    body: JSON.stringify({ ...form, size_aana: Number(form.size_aana), road_width_ft: Number(form.road_width_ft) }),
  })
  if (!response.ok) throw new Error(response.status === 422 ? 'Check the neighbourhood, plot size and road width, then try again.' : 'The comparison service is unavailable. Please try again.')
  return response.json()
}

export default function AskingPriceRange() {
  const [form, setForm] = useState(startingForm)
  const [result, setResult] = useState(null)
  const [submitted, setSubmitted] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  useEffect(() => {
    const controller = new AbortController()
    compare(startingForm, controller.signal).then(value => { setResult(value); setSubmitted(JSON.stringify(startingForm)) })
      .catch(cause => { if (cause.name !== 'AbortError') setError(cause instanceof TypeError ? 'Unable to connect. Start the local property service and try again.' : cause.message) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [])

  function update(key, value) { setForm(current => ({ ...current, [key]: value })) }
  function changeMode(mode) { setForm(current => ({ ...current, mode })); setResult(null); setSubmitted(''); setError('') }
  async function submit(event) {
    event.preventDefault()
    setLoading(true); setError(''); setResult(null)
    const snapshot = { ...form }
    try { setResult(await compare(snapshot)); setSubmitted(JSON.stringify(snapshot)) }
    catch (cause) { setError(cause instanceof TypeError ? 'Unable to connect to the property service. Please try again.' : cause.message) }
    finally { setLoading(false) }
  }
  const dirty = result && submitted !== JSON.stringify(form)
  const ready = result?.status === 'ready'
  const range = result?.range
  const example = result?.mode === 'example'

  return <div className="asking-shell">
    <header className="asking-header"><a className="asking-brand" href="/">◈ <span>Land Discover</span></a><nav aria-label="Price range navigation"><a href="/properties">Browse properties ↗</a><AccountMenu signInClass="asking-signin" /></nav></header>
    <main className="asking-main">
      <a className="asking-back" href="/properties">← Back to properties</a>
      <section className="asking-intro"><div><p className="asking-eyebrow">KATHMANDU · LAND · PROTOTYPE</p><h1>Start with a range.<br /><em>See the evidence.</em></h1></div><p>Compare similar plots by neighbourhood,<br className="asking-wide" /> size and road access. Understand what<br className="asking-wide" /> sellers are asking before you decide.</p></section>
      <div className="asking-workspace">
        <section className="asking-input-panel" aria-labelledby="asking-input-title">
          <p className="asking-eyebrow">01 / YOUR COMPARISON</p><h2 id="asking-input-title">Describe the plot</h2><p className="asking-muted">Kathmandu district · Land for sale</p>
          <fieldset className="asking-mode" disabled={loading}><legend>Choose evidence</legend><label className={form.mode === 'example' ? 'selected' : ''}><input type="radio" name="mode" checked={form.mode === 'example'} onChange={() => changeMode('example')} />Illustrative example</label><label className={form.mode === 'collected' ? 'selected' : ''}><input type="radio" name="mode" checked={form.mode === 'collected'} onChange={() => changeMode('collected')} />Collected listings</label></fieldset>
          <div className={`asking-mode-note ${form.mode === 'example' ? 'example' : ''}`}>{form.mode === 'example' ? <><strong>Fictional properties. Demonstration only.</strong><p>These prices show how the prototype works. They do not describe the Banasthali market.</p></> : <><strong>Use the local listing database.</strong><p>A range appears only when at least five eligible properties match. Listings are not verified sales.</p></>}</div>
          <form className="asking-form" onSubmit={submit}><fieldset disabled={loading}>
            <label>Neighbourhood<input required minLength={2} maxLength={100} value={form.neighbourhood} onChange={event => update('neighbourhood', event.target.value)} placeholder="e.g. Banasthali" /></label>
            <div className="asking-form-row"><label>Plot size <span>aana</span><input type="number" required min="0.01" max="1000" step="any" value={form.size_aana} onChange={event => update('size_aana', event.target.value)} /></label><label>Road width <span>feet</span><input type="number" required min="0.1" max="100" step="any" value={form.road_width_ft} onChange={event => update('road_width_ft', event.target.value)} /></label></div>
            <label>Road surface<select value={form.road_surface} onChange={event => update('road_surface', event.target.value)}>{Object.entries(surfaces).map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select></label>
            <label>Position relative to main road<select value={form.frontage} onChange={event => update('frontage', event.target.value)}><option value="inner">Inside a neighbourhood / inner plot</option><option value="main_road">Direct main-road frontage</option></select></label>
            <button className="asking-primary" type="submit">{loading ? 'Comparing…' : 'Compare asking prices'} <span aria-hidden="true">↗</span></button>
          </fieldset></form>
          <p className="asking-input-foot">Houses, apartments, and explicitly commercial or agricultural plots are excluded from this land comparison.</p>
        </section>
        <div className="asking-output" aria-live="polite" aria-busy={loading}>
          {error ? <section className="asking-empty" role="alert"><span className="asking-empty-icon">!</span><h2>Comparison unavailable</h2><p>{error}</p><p>Your inputs are saved here. Select Compare asking prices to retry.</p></section> : loading ? <section className="asking-empty"><span className="asking-loading" /><h2>Finding comparable plots…</h2><p>Checking location, size, road access and listing dates.</p></section> : !result ? <section className="asking-empty"><span className="asking-empty-icon">↗</span><h2>Build your comparison</h2><p>Review the plot details, then select Compare asking prices.</p></section> : <>
            {dirty && <p className="asking-dirty" role="status">Inputs changed. Compare again to update the results below.</p>}
            <section className={`asking-result ${ready ? '' : 'asking-result-insufficient'}`}>
              <div className="asking-result-top"><p className="asking-eyebrow">02 / {example ? 'ILLUSTRATIVE RESULT' : 'ASKING-PRICE COMPARISON'}</p><span className="asking-badge">{example ? 'FICTIONAL EXAMPLE' : 'UNVERIFIED LISTINGS'}</span></div>
              <h2>{ready ? example ? 'Example asking-price range' : 'Estimated asking-price range' : 'Insufficient comparable data'}</h2>
              <p className="asking-result-location">{result.subject.neighbourhood} · {result.subject.size_aana} aana · {result.subject.road_width_ft} ft {surfaces[result.subject.road_surface].toLowerCase()} road</p>
              {ready ? <><div className="asking-price">{format(range.low_per_aana_npr)} <span>—</span> {format(range.high_per_aana_npr)}</div><p className="asking-price-unit">per aana · middle 50% of matching asking rates</p><div className="asking-result-stats"><div><span>Indicative plot total</span><strong>{format(range.low_total_npr)} – {format(range.high_total_npr)}</strong></div><div><span>Median asking rate</span><strong>{format(range.median_per_aana_npr)} / aana</strong></div></div><div className="asking-spread"><div><span>Lowest observed {format(range.observed_min_per_aana_npr)}</span><span>Highest observed {format(range.observed_max_per_aana_npr)}</span></div><div className="asking-spread-track"><i style={{ left: `${100*(range.low_per_aana_npr-range.observed_min_per_aana_npr)/(range.observed_max_per_aana_npr-range.observed_min_per_aana_npr || 1)}%`, width: `${100*(range.high_per_aana_npr-range.low_per_aana_npr)/(range.observed_max_per_aana_npr-range.observed_min_per_aana_npr || 1)}%` }} /><b style={{ left: `${100*(range.median_per_aana_npr-range.observed_min_per_aana_npr)/(range.observed_max_per_aana_npr-range.observed_min_per_aana_npr || 1)}%` }} /></div><small>Highlighted: middle 50% · marker: median</small></div></> : <div className="asking-insufficient"><strong>{result.comparable_count} of {result.minimum_comparables} required matches</strong><p>We do not expand to unrelated neighbourhoods or fill in missing road details to create a price. Try a supported example, or collect more complete, recent listings for this area.</p></div>}
              <div className="asking-evidence-line"><span>◉ {result.comparable_count} {example ? 'example plots' : 'matched listings'}</span><span>{example ? 'No market accuracy claim' : 'Accuracy not validated against completed sales'}</span></div>
              {example && <p className="asking-fictional">All prices and properties in this result are fictional.</p>}
            </section>
            <section className="asking-comparables" aria-labelledby="asking-comparables-title"><div className="asking-section-title"><div><p className="asking-eyebrow">03 / THE EVIDENCE</p><h2 id="asking-comparables-title">{example ? 'Example comparable plots' : 'Matching listings'}</h2></div><span>{result.comparable_count} matches</span></div>
              {result.comparables.length ? <div className="asking-table-wrap"><table><caption className="asking-sr-only">Comparable asking prices with plot size, road access and source dates</caption><thead><tr><th>Property / source</th><th>Plot & road</th><th>Asking / aana</th><th>Source date</th></tr></thead><tbody>{result.comparables.map(row => <tr key={row.id}><td>{example ? <strong>{row.title}</strong> : <a href={`/properties/${row.id}`}>{row.title} ↗</a>}<small>{row.source}{/^https:\/\//.test(row.source_url) && <> · <a href={row.source_url} target="_blank" rel="noreferrer">Original listing ↗</a></>}</small></td><td>{row.size_aana} aana<small>{row.road_width_ft} ft · {surfaces[row.road_surface]} · {row.frontage === 'inner' ? 'Inner plot' : 'Main-road frontage'}</small></td><td><strong>{format(row.per_aana_npr)}</strong></td><td>{row.listing_date}{example && <small>Example date</small>}</td></tr>)}</tbody></table></div> : <p className="asking-muted asking-no-matches">No eligible comparable listings were found for these inputs.</p>}
            </section>
            {!!result.excluded.length && <details className="asking-exclusions"><summary>Why other records were excluded ({result.excluded.reduce((sum, row) => sum + row.count, 0)})</summary><ul>{result.excluded.map(row => <li key={row.reason}><span>{row.reason}</span><strong>{row.count}</strong></li>)}</ul></details>}
          </>}
          <section className="asking-method"><p className="asking-eyebrow">HOW THIS PROTOTYPE WORKS</p><h2>Similar plots. Clear limits.</h2><div className="asking-method-grid"><div><span>01</span><h3>Match the context</h3><p>Same neighbourhood, road surface and frontage. Road width within 4 feet; plot size from half to twice yours.</p></div><div><span>02</span><h3>Check the evidence</h3><p>Known asking-price units and source dates within 180 days. Exclude incomplete access, sold records and possible duplicates.</p></div><div><span>03</span><h3>Show a range</h3><p>At least five matches. Show the middle 50%, median and observed extremes. No fixed road premiums or discounts.</p></div></div><p className="asking-method-note">These matching rules are provisional. A price range is not a confidence interval or a verified sale valuation. A new scrape does not prove that an offer is current.</p></section>
        </div>
      </div>
      <footer className="asking-footer"><span>Land Discover · Kathmandu asking-price prototype</span><span>Government values and verified sales will be separate measures.</span></footer>
    </main>
  </div>
}
