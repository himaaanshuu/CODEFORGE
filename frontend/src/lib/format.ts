export const fmtInt = (n: number) => n.toLocaleString('en-US')
export const fmtK = (n: number) => (n >= 1_000_000 ? `${(n / 1_000_000).toFixed(2)}M` : n >= 1000 ? `${(n / 1000).toFixed(1)}K` : String(n))
export const fmtUsd = (n: number, d = 3) => `$${n.toFixed(d)}`
