import { ChevronDown } from 'lucide-react'
import { useState } from 'react'

interface SiteSelectorProps {
  selectedSite: string
  onSiteChange: (site: string) => void
}

const SITES = [
  { code: 'KET', name: 'Ketane', country: 'Lesotho', connections: 1279 },
  { code: 'MAK', name: 'Makhoarane', country: 'Lesotho', connections: 850 },
  { code: 'LEB', name: 'Lebesa', country: 'Lesotho', connections: 620 },
  { code: 'MAT', name: 'Matsoku', country: 'Lesotho', connections: 480 },
  { code: 'SEB', name: 'Seboche', country: 'Lesotho', connections: 390 },
  { code: 'TOS', name: 'Tosing', country: 'Lesotho', connections: 320 },
  { code: 'SEH', name: 'Sehong-hong', country: 'Lesotho', connections: 280 },
  { code: 'TLH', name: 'Tlhanyaku', country: 'Lesotho', connections: 250 },
  { code: 'MAS', name: 'Mashai', country: 'Lesotho', connections: 220 },
  { code: 'SHG', name: 'Shang', country: 'Lesotho', connections: 180 },
  { code: 'RIB', name: 'Ribaneng', country: 'Lesotho', connections: 150 },
]

export function SiteSelector({ selectedSite, onSiteChange }: SiteSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const currentSite = SITES.find(s => s.code === selectedSite) || SITES[0]

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
      >
        <div className="text-left">
          <div className="font-semibold text-gray-900">{currentSite.code}</div>
          <div className="text-xs text-gray-500">{currentSite.name}</div>
        </div>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 z-20">
            <div className="p-2">
              {SITES.map((site) => (
                <button
                  key={site.code}
                  onClick={() => {
                    onSiteChange(site.code)
                    setIsOpen(false)
                  }}
                  className={`
                    w-full text-left px-3 py-2 rounded-md transition-colors
                    ${site.code === selectedSite 
                      ? 'bg-blue-50 text-blue-600' 
                      : 'hover:bg-gray-50'
                    }
                  `}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{site.code} - {site.name}</div>
                      <div className="text-xs text-gray-500">
                        {site.country} • {site.connections} connections
                      </div>
                    </div>
                    {site.code === selectedSite && (
                      <div className="w-2 h-2 bg-blue-600 rounded-full" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
