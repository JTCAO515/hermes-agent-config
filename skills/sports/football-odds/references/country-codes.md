# Country ISO Codes for World Cup 2026 Teams

For use with flagcdn.com (`https://flagcdn.com/20x15/{code}.png`).

## Group A — Mexico, South Africa, Netherlands, Saudi Arabia
mx, za, nl, sa

## Group B — Spain, France, Tunisia, Ecuador
es, fr, tn, ec

## Group C — Egypt, Croatia, Curaçao, Senegal
eg, hr, cw, sn

## Group D — Algeria, Paraguay, Japan, Haiti
dz, py, jp, ht

## Group E — Germany, Côte d'Ivoire, Sweden, Panama
de, ci, se, pa

## Group F — Brazil, Iran, Uzbekistan, Belgium
br, ir, uz, be

## Group G — Argentina, Switzerland, Morocco, Jordan
ar, ch, ma, jo

## Group H — England, Czechia, Korea Republic, New Zealand
gb-eng, cz, kr, nz

## Group I — Norway, Iraq, Congo DR, Canada
no, iq, cd, ca

## Group J — Portugal, Ghana, Uruguay, Qatar
pt, gh, uy, qa

## Group K — USA, Australia, Scotland, Colombia
us, au, gb-sct, co

## Group L — Austria, Türkiye, Cabo Verde, Bosnia and Herz.
at, tr, cv, ba

## Notes
- `gb-eng` and `gb-sct` use subdivision codes; flagcdn.com supports these
- Normalize team names to NFC before matching in JS/Python
- flagcdn.com returns 204 for valid codes, 404 for invalid
- Fallback CDN: `https://flagpedia.net/data/flags/h20/{code}.png`
