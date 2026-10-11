'use client'

import { useState, type FormEvent } from 'react'

export default function NewListingForm({ displayName }: { displayName: string }) {
  const [step, setStep] = useState<1 | 2 | 3>(1)
  const [transaction, setTransaction] = useState<'rent' | 'sale' | null>(null)
  const [type, setType] = useState<'house' | 'land' | null>(null)
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (step !== 3 || !transaction || !type) return
    setError(''); setPending(true)
    const values = Object.fromEntries(new FormData(event.currentTarget))
    const payload = {
      ...values,
      transaction_type: transaction,
      property_type: type,
      total_price_npr: Number(values.total_price_npr),
      bedrooms: type === 'land' || !values.bedrooms ? null : Number(values.bedrooms),
      bathrooms: type === 'land' || !values.bathrooms ? null : Number(values.bathrooms),
    }
    try {
      const response = await fetch('/api/properties', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      if (response.status === 401) {
        window.location.assign('/login?next=%2Fproperties%2Fnew')
        return
      }
      const body = await response.json()
      if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : Array.isArray(body.detail) ? body.detail.map((item: { msg: string }) => item.msg).join('. ') : 'Unable to submit this listing.')
      window.location.assign(`/properties/${body.id}`)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to reach the listing service.') }
    finally { setPending(false) }
  }
  return <section className="listing-wizard" aria-label="List a property">
    <aside className="listing-sidebar">
      <ol className="listing-steps" aria-label="Listing progress">
        {[['Listing purpose', 'Rent or sell'], ['Property type', 'House or land'], ['Property details', 'The essentials']].map(([title, description], index) => <li key={title} aria-current={step === index + 1 ? 'step' : undefined} className={step > index + 1 ? 'completed' : ''}><span className="listing-step-number">{index + 1}</span><div><strong>{title}</strong><span>{description}</span></div></li>)}
      </ol>
      <div className="listing-preparation"><ListingIcon kind="document" /><p>Have your property details ready.</p><p>Add accurate information and contact details before submitting.</p></div>
    </aside>
    <div className="listing-workspace">
    {step < 3 && <section className="listing-choice-panel" aria-labelledby="choice-heading">
      <div className="listing-panel-body">
        <p className="eyebrow">STEP {step} OF 3</p>
        <h2 id="choice-heading">{step === 1 ? 'How would you like to list it?' : 'What kind of property is it?'}</h2>
        <p>{step === 1 ? 'Choose the purpose of your listing.' : 'Choose the property you want to ' + (transaction === 'rent' ? 'rent out.' : 'sell.')}</p>
        <div className="listing-choices" role="radiogroup" aria-labelledby="choice-heading">
          {step === 1 ? <>
            <label className="listing-choice"><input type="radio" name="listing-purpose" checked={transaction === 'rent'} onChange={() => { setTransaction('rent'); setError('') }} /><ListingIcon kind="key" /><span className="listing-choice-copy"><strong>For rent</strong><span>Find a tenant for your property.</span></span><span className="listing-radio" aria-hidden="true" /></label>
            <label className="listing-choice"><input type="radio" name="listing-purpose" checked={transaction === 'sale'} onChange={() => { setTransaction('sale'); setError('') }} /><ListingIcon kind="sale" /><span className="listing-choice-copy"><strong>For sale</strong><span>Find a buyer for your property.</span></span><span className="listing-radio" aria-hidden="true" /></label>
          </> : <>
            <label className="listing-choice"><input type="radio" name="listing-property-type" checked={type === 'house'} onChange={() => setType('house')} /><ListingIcon kind="house" /><span className="listing-choice-copy"><strong>House</strong><span>A house or residential home.</span></span><span className="listing-radio" aria-hidden="true" /></label>
            <label className="listing-choice"><input type="radio" name="listing-property-type" checked={type === 'land'} onChange={() => setType('land')} /><ListingIcon kind="land" /><span className="listing-choice-copy"><strong>Land</strong><span>A plot of land.</span></span><span className="listing-radio" aria-hidden="true" /></label>
          </>}
        </div>
      </div>
      <div className="listing-panel-footer"><div><p>Signed in as <strong>{displayName}</strong></p>{step === 2 && <button type="button" className="text-button" onClick={() => setStep(1)}>Back</button>}</div><button type="button" className="button primary listing-continue" disabled={step === 1 ? !transaction : !type} onClick={() => setStep(step === 1 ? 2 : 3)}>Continue <span aria-hidden="true">&rarr;</span></button></div>
    </section>}
    {transaction && type && <div hidden={step !== 3}>
    <form className="submit-form" onSubmit={submit}>
    <div className="listing-selection"><div><p className="eyebrow">STEP 3 OF 3</p><h2>{type === 'house' ? 'House' : 'Land'} for {transaction === 'rent' ? 'rent' : 'sale'}</h2></div><button type="button" className="text-button" disabled={pending} onClick={() => setStep(2)}>Change choices</button></div>
    <label>Property title<input name="title" minLength={3} maxLength={140} required placeholder={type === 'land' ? 'e.g. Residential land in Bhaisepati' : 'e.g. Family home in Bhaisepati'} /></label>
    <div className="submit-grid"><label>District<select name="district"><option>Kathmandu</option><option>Lalitpur</option><option>Bhaktapur</option></select></label><label>Neighborhood<input name="area_name" minLength={2} maxLength={100} required /></label></div>
    <label>Address<input name="address" minLength={3} maxLength={250} required /></label>
    <div className="submit-grid"><label>{transaction === 'rent' ? 'Monthly rent (NPR)' : 'Asking price (NPR)'}<input name="total_price_npr" type="number" min="1" max="1000000000000" step="any" required /></label><label>{type === 'land' ? 'Plot size' : 'Plot or floor size'}<input name="size" minLength={1} maxLength={80} required placeholder="e.g. 4 aana or 1,250 sq ft" /></label></div>
    {type !== 'land' && <div className="submit-grid"><label>Bedrooms<input name="bedrooms" type="number" min="0" max="100" /></label><label>Bathrooms<input name="bathrooms" type="number" min="0" max="100" /></label></div>}
    <label>Property description<textarea name="description" minLength={10} maxLength={5000} rows={5} required /></label>
    <label>Road access details <span className="muted">optional</span><input name="road_access_note" maxLength={300} /></label>
    <label>Photo URL <span className="muted">required &middot; HTTPS</span><input name="image_url" type="url" required minLength={10} maxLength={2000} placeholder="https://..." /></label>
    <div className="submit-grid"><label>Contact name<input name="contact_name" minLength={2} maxLength={100} required /></label><label>Contact phone<input name="contact_phone" type="tel" minLength={7} maxLength={30} pattern="\+?[0-9 ()-]+" required /></label></div>
    <p className="submit-disclaimer">Your listing will be labelled owner-submitted and unverified. Only submit information and photos you have the right to share. Confirm the contact details and public visibility before submitting.</p>
    {error && <p role="alert" className="form-message error">{error}</p>}
    <button className="button primary" disabled={pending}>{pending ? 'Submitting…' : 'Submit property'}</button>
  </form>
    </div>}
    </div>
  </section>
}

function ListingIcon({ kind }: { kind: 'key' | 'sale' | 'house' | 'land' | 'document' }) {
  const paths = {
    key: 'M15 3a6 6 0 0 0-5.7 7.9L3 17.2V21h4v-3h3v-3l2.1-2.1A6 6 0 1 0 15 3 M16 7h.01',
    sale: 'M3 7l4-3 5 2 5-2 4 3-2 10-4 3-3-2-3 2-4-3-2-10 M7 4l-2 8 3 2 4-5 6 6 M12 6l-3 4 3 2 3-3 M8 14l6 5',
    house: 'M3 11l9-8 9 8 M5 10v11h14V10 M9 21v-8h6v8',
    land: 'M3 16l9-11 9 11-9 5-9-5 M8 12l9 6 M12 5v16',
    document: 'M6 3h8l4 4v14H6V3 M14 3v5h4 M9 12h6 M9 16h6',
  }
  return <svg className="listing-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[kind]} /></svg>
}
