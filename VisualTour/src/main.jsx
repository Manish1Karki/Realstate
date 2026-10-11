import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import ListingTour from './ListingTour.jsx'
import './styles.css'

const demo=new URLSearchParams(window.location.search).get('demo')==='1'
createRoot(document.getElementById('root')).render(demo ? <StrictMode><App /></StrictMode> : <ListingTour />)
