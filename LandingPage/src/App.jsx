import './App.css'
import LoginPage from './LoginPage'
import PropertyDashboard from './PropertyDashboard'
import AccountMenu from './AccountMenu'

const DASHBOARD_URL = import.meta.env.VITE_DASHBOARD_URL || '/properties'

const Icon = ({ children, size = 20 }) => <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{children}</svg>
const Arrow = () => <Icon size={18}><path d="M5 12h14M13 6l6 6-6 6" /></Icon>
const Pin = ({ size }) => <Icon size={size}><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="2.5" /></Icon>
const Search = () => <Icon><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></Icon>
const Spark = () => <Icon><path d="m12 3 1.4 4.1L17.5 9l-4.1 1.4L12 15l-1.4-4.6L6.5 9l4.1-1.9L12 3Z" /></Icon>
const Chart = () => <Icon><path d="M4 19V9M10 19V5M16 19v-7M22 19V3" /></Icon>
const Shield = () => <Icon><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" /><path d="m9 12 2 2 4-5" /></Icon>
const Road = () => <Icon><path d="M8 3 5 21M16 3l3 18M12 5v3M12 12v3M12 19v2" /></Icon>
const Layers = () => <Icon><path d="m12 2 9 5-9 5-9-5 9-5Z" /><path d="m3 12 9 5 9-5M3 17l9 5 9-5" /></Icon>

const features = [
  [<Search key="i" />, '01', 'Find land that fits', 'Search verified listings by neighborhood, budget, plot size, and road access—not vague promises.'],
  [<Spark key="i" />, '02', 'Know the fair price', 'Get an instant AI-backed valuation based on location, access, nearby facilities, and market patterns.'],
  [<Chart key="i" />, '03', 'See what comes next', 'Understand today’s value and explore projected price ranges across the next one to three years.'],
  [<Shield key="i" />, '04', 'Decide with confidence', 'Compare properties with a clear score out of 100 and the context behind every recommendation.'],
]

function App() {
  if (window.location.pathname === '/login' || window.location.hash === '#login') return <LoginPage />
  if (window.location.pathname === '/properties' || window.location.pathname.startsWith('/properties/')) return <PropertyDashboard />
  return <div className="site-shell">
    <header className="nav-wrap">
      <a className="brand" href="#top"><span className="brand-mark"><Pin size={18} /></span><span>Land<span>Discover</span></span></a>
      <nav><a href="#how">How it works</a><a href="/aggregator/">Aggregator</a><a href="#explore">Explore</a></nav>
      <div className="nav-actions"><AccountMenu signInClass="nav-signin" /><a className="nav-cta" href={DASHBOARD_URL}>Browse properties <Arrow /></a></div>
    </header>

    <main id="top">
      <section className="hero section-pad">
        <div className="hero-copy">
          <div className="eyebrow"><span /> Property intelligence for Nepal</div>
          <h1>Know the land.<br /><em>Own the future.</em></h1>
          <p className="hero-lede">Search real land listings across Kathmandu, discover a fair price, and understand tomorrow’s potential—all before you make your move.</p>
          <div className="hero-actions"><a className="button primary hero-browse" href={DASHBOARD_URL}>Browse properties <Arrow /></a><a className="text-link" href="#intelligence">See how valuation works <span>↘</span></a></div>
          <div className="trust-row"><div className="avatar-stack"><span>क</span><span>ल</span><span>घ</span></div><p><strong>Built for Kathmandu</strong><br />Local data. Clear decisions.</p></div>
        </div>
        <div className="hero-visual" aria-label="Sample Kathmandu property valuation">
          <div className="sun-disc" /><div className="mountains mountain-back" /><div className="mountains mountain-front" /><div className="map-grid" />
          <div className="location-label label-one"><span /> Baluwatar</div><div className="location-label label-two"><span /> Lazimpat</div><div className="location-label label-three"><span /> Maharajgunj</div><div className="property-pin"><Pin size={22} /></div>
          <div className="valuation-card"><div className="valuation-head"><span>AI LAND SCORE</span><span className="live-dot">Live analysis</span></div><div className="score-row"><div className="score-ring"><strong>87</strong><small>/100</small></div><div><span>Estimated fair value</span><strong>NPR 72–78L</strong><small>4.2 aana · Sample property</small></div></div><div className="growth-row"><div><span>3-year outlook</span><strong>+18.4%</strong></div><svg viewBox="0 0 160 45" preserveAspectRatio="none"><path className="area" d="M0 40C24 38 28 31 48 33s29-9 45-7 30-15 67-21v40H0Z" /><path d="M0 40C24 38 28 31 48 33s29-9 45-7 30-15 67-21" /></svg></div></div>
        </div>
      </section>

      <section className="signal-strip"><span>FAIR PRICE ESTIMATES</span><i>✦</i><span>VERIFIED LISTINGS</span><i>✦</i><span>LOCATION INTELLIGENCE</span><i>✦</i><span>FUTURE VALUE</span></section>

      <section className="problem section-pad">
        <div className="section-label">The old way is broken</div><div className="problem-grid"><h2>Property decisions shouldn’t depend on <em>guesswork.</em></h2><div className="problem-copy"><p>Buying land in Kathmandu often means trusting a broker you barely know or scrolling through listings with no real context. Is the asking price fair? Is the road access reliable? Will the area grow?</p><p><strong>Land Discover brings the answers into one clear place.</strong> We combine real listings, location data, and AI-backed analysis so ordinary people can make extraordinary decisions.</p></div></div>
        <div className="contrast-cards"><div className="contrast-card old"><span className="card-kicker">BEFORE</span><h3>“The broker said it’s a good deal.”</h3><ul><li>Unexplained asking prices</li><li>Scattered, unreliable listings</li><li>No view of future potential</li></ul></div><div className="contrast-arrow"><Arrow /></div><div className="contrast-card new"><span className="card-kicker">WITH LAND DISCOVER</span><h3>“The data shows me why.”</h3><ul><li>Transparent AI valuation</li><li>One property score out of 100</li><li>1–3 year value projection</li></ul></div></div>
      </section>

      <section className="features section-pad" id="how"><div className="section-heading"><div><div className="section-label light">From search to certainty</div><h2>Everything you need.<br /><em>Nothing you don’t.</em></h2></div><p>One platform to discover, evaluate, compare, and understand land across Kathmandu.</p></div><div className="feature-grid">{features.map(([icon, num, title, text]) => <article className="feature-card" key={title}><div className="feature-top"><span>{icon}</span><span>{num}</span></div><h3>{title}</h3><p>{text}</p></article>)}</div></section>

      <section className="intelligence section-pad" id="intelligence">
        <div className="intel-copy"><div className="section-label">Intelligence you can explain</div><h2>Not just a number.<br /><em>The reason behind it.</em></h2><p>Our valuation system studies the signals that shape a property’s real value and turns them into an analysis anyone can understand.</p><div className="intel-list"><div><span><Pin size={19} /></span><p><strong>Location strength</strong>Neighborhood demand and development patterns</p></div><div><span><Road /></span><p><strong>Access & infrastructure</strong>Road width, connectivity, and nearby major routes</p></div><div><span><Layers /></span><p><strong>Nearby essentials</strong>Schools, hospitals, markets, and public services</p></div><div><span><Chart /></span><p><strong>Market momentum</strong>Comparable prices and projected local growth</p></div></div></div>
        <div className="report-card"><div className="report-header"><div><span>PROPERTY ANALYSIS</span><strong>Bhaisepati, Lalitpur</strong></div><span className="verified"><Shield /> Verified data</span></div><div className="report-score"><div className="big-score">84<span>/100</span></div><div><strong>Strong investment</strong><p>Above-average fundamentals with healthy long-term potential.</p></div></div>{[['Location', '91'], ['Road access', '78'], ['Amenities', '86'], ['Growth outlook', '82']].map(([name, score]) => <div className="metric" key={name}><div><span>{name}</span><strong>{score}</strong></div><div className="bar"><i style={{ width: `${score}%` }} /></div></div>)}<div className="report-value"><span>ESTIMATED FAIR VALUE</span><strong>NPR 1.24–1.32 Cr</strong><small>Sample analysis · 6.1 aana</small></div></div>
      </section>

      <section className="explore section-pad" id="explore"><div className="explore-map"><div className="road r1" /><div className="road r2" /><div className="road r3" /><div className="river" /><span className="map-area a1">Baluwatar</span><span className="map-area a2">Baneshwor</span><span className="map-area a3">Patan</span><span className="map-area a4">Kirtipur</span><div className="price-pin p1">NPR 16L/aana</div><div className="price-pin p2">NPR 24L/aana</div><div className="price-pin p3">NPR 18L/aana</div><div className="price-pin p4">NPR 12L/aana</div></div><div className="explore-copy"><div className="section-label light">See the whole picture</div><h2>Kathmandu,<br /><em>mapped for clarity.</em></h2><p>Explore live property pins, compare neighborhood prices at a glance, and see what surrounds every plot before visiting it.</p><div className="map-legend"><span><i className="orange" /> Property listings</span><span><i className="gold" /> Price heatmap</span><span><i className="blue" /> Nearby facilities</span></div><a className="button cream" href={DASHBOARD_URL}>Search listings <Arrow /></a></div></section>

      <section className="audience section-pad"><div className="section-label">Built around your next move</div><h2>One source of truth.<br /><em>For every side of the deal.</em></h2><div className="audience-grid">{[['01', 'For buyers', 'Find the right land and know when the asking price makes sense.', 'Browse properties', DASHBOARD_URL], ['02', 'For sellers', 'List confidently with a fair, data-informed estimate behind your price.', 'Value your land', '#access'], ['03', 'For investors', 'Compare opportunities and uncover areas with stronger growth potential.', 'Search listings', DASHBOARD_URL]].map(([n, t, p, a, href]) => <article key={t}><span>{n}</span><h3>{t}</h3><p>{p}</p><a href={href}>{a} <Arrow /></a></article>)}</div></section>

      <section className="cta section-pad" id="access"><div className="cta-pattern" /><div className="cta-content"><span className="mini-mark"><Pin size={20} /></span><div className="section-label light">A clearer property market starts here</div><h2>Stop guessing.<br /><em>Start discovering.</em></h2><p>Browse available properties without signing in. Compare locations, prices, road access, and nearby facilities before you decide.</p><div className="cta-actions"><a className="button cta-primary" href={DASHBOARD_URL}>Browse properties <Arrow /></a><a className="button cta-secondary" href={DASHBOARD_URL}>Search listings</a></div><small>No sign-in required to explore properties.</small></div></section>
    </main>
    <footer><a className="brand footer-brand" href="#top"><span className="brand-mark"><Pin size={18} /></span><span>Land<span>Discover</span></span></a><p>Transparent property intelligence for Nepal.</p><div><a href="#how">How it works</a><a href="#intelligence">AI valuation</a><a href="#explore">Map</a></div><span>© 2026 Land Discover</span></footer>
  </div>
}

export default App
