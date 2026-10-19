import { ImageResponse } from 'next/og'
export const dynamic = 'force-static'
export async function GET() {
  return new ImageResponse(<div style={{ width:'100%',height:'100%',display:'flex',flexDirection:'column',background:'#faf9f4',padding:80,color:'#193e32' }}><div style={{display:'flex',alignItems:'center',fontSize:42}}><span style={{display:'flex',background:'#be4727',color:'white',padding:20,marginRight:24,borderRadius:12}}>LD</span>Land Discover</div><div style={{display:'flex',fontSize:76,marginTop:72}}>Find your place.</div><div style={{display:'flex',fontSize:32,marginTop:24}}>Homes and land for sale and rent in Kathmandu Valley</div></div>, { width:1200,height:630 })
}
