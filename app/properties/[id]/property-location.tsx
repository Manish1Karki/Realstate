'use client'
import { useEffect, useRef, useState } from 'react'
import WhatsAppIcon from '../../whatsapp-icon'
import WhatsAppButton from '../../whatsapp-button'
export default function PropertyLocation({ title, tourUrl, canTour, whatsappUrl }: { title: string; tourUrl: string; canTour: boolean; whatsappUrl: string }) {
 const dialog = useRef<HTMLDialogElement>(null)
 const [tourOpen, setTourOpen] = useState(false)
 useEffect(() => {
   if (!tourOpen) return
   const previousOverflow = document.body.style.overflow
   document.body.style.overflow = 'hidden'
   return () => { document.body.style.overflow = previousOverflow }
 }, [tourOpen])
 function openTour() { setTourOpen(true); dialog.current?.showModal() }
 function closeTour() { dialog.current?.close() }
 return <><div className="property-map-viewport">{canTour && !tourOpen ? <iframe title={'Map showing the published location of ' + title} src={tourUrl + '&mode=map'} loading="lazy" referrerPolicy="strict-origin-when-cross-origin" /> : tourOpen ? <div className="property-map-empty"><p>Visual Tour is open.</p></div> : <div className="property-map-empty"><h2>Map unavailable</h2><p>Contact the advertiser for the exact property location.</p></div>}<div className="property-map-actions">{canTour ? <button type="button" className="button primary property-tour-action" onClick={openTour} aria-haspopup="dialog"><TourIcon /><span>Visual Tour</span></button> : <button type="button" className="button primary property-tour-action" disabled title="A source map pin is required for a visual tour"><TourIcon /><span>Visual Tour</span></button>}{whatsappUrl ? <WhatsAppButton className="button property-whatsapp-action" href={whatsappUrl} label="Contact advertiser on WhatsApp" /> : <button type="button" className="button property-whatsapp-action" disabled aria-label="WhatsApp unavailable: no valid contact number" title="No valid WhatsApp contact number is listed"><WhatsAppIcon /></button>}</div></div>
 <dialog ref={dialog} className="property-tour-dialog" aria-label={'Visual Tour of ' + title} onClose={() => setTourOpen(false)}>
   <button type="button" className="property-tour-close" onClick={closeTour} autoFocus aria-label="Close Visual Tour"><span aria-hidden="true">&#215;</span> Close tour</button>
   {tourOpen && <iframe title={'Visual Tour of ' + title} src={tourUrl + '&mode=tour'} referrerPolicy="strict-origin-when-cross-origin" onLoad={event => { event.currentTarget.contentWindow?.addEventListener('keydown', event => { if (event.key === 'Escape') { event.preventDefault(); closeTour() } }) }} />}
 </dialog></>
}


function TourIcon() {
 return <span className="property-tour-icon" aria-hidden="true"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="12" r="9" /><path d="m10 8 6 4-6 4Z" fill="currentColor" stroke="none" /></svg></span>
}
