import { Map, Database, CheckCircle, Settings, FileText } from 'lucide-react'

interface NavigationProps {
  currentView: string
  onViewChange: (view: 'map' | 'stats' | 'validation') => void
}

export function Navigation({ currentView, onViewChange }: NavigationProps) {
  const navItems = [
    { id: 'map', label: 'Network Map', icon: Map },
    { id: 'stats', label: 'Data Stats', icon: Database },
    { id: 'validation', label: 'Validation', icon: CheckCircle },
  ]

  return (
    <nav className="w-64 bg-white border-r border-gray-200">
      <div className="p-4">
        <div className="flex items-center space-x-2 mb-8">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">1P</span>
          </div>
          <span className="font-semibold text-gray-900">Grid Platform</span>
        </div>

        <div className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = currentView === item.id
            
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id as any)}
                className={`
                  w-full flex items-center space-x-3 px-3 py-2 rounded-lg
                  transition-colors duration-200
                  ${isActive 
                    ? 'bg-blue-50 text-blue-600' 
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }
                `}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </button>
            )
          })}
        </div>

        <div className="mt-8 pt-8 border-t border-gray-200">
          <button className="w-full flex items-center space-x-3 px-3 py-2 text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-lg transition-colors">
            <FileText className="w-5 h-5" />
            <span className="font-medium">Reports</span>
          </button>
          <button className="w-full flex items-center space-x-3 px-3 py-2 text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-lg transition-colors">
            <Settings className="w-5 h-5" />
            <span className="font-medium">Settings</span>
          </button>
        </div>
      </div>
    </nav>
  )
}
