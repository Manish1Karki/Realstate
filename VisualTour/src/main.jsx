import { lazy, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const App = lazy(() => import('./App.jsx'))
const ListingTour = lazy(() => import('./ListingTour.jsx'))
const demo = new URLSearchParams(window.location.search).get('demo') === '1'
createRoot(document.getElementById('root')).render(<Suspense fallback={<p role="status">Loading location viewer...</p>}>{demo ? <App /> : <ListingTour />}</Suspense>)
