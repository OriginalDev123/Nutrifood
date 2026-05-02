import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  UtensilsCrossed,
  Apple,
  ChefHat,
  Calendar,
  BarChart3,
  Target,
  User,
  Settings,
  Users,
  Shield,
  ChevronLeft,
  ChevronRight,
  Leaf,
} from 'lucide-react';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  adminOnly?: boolean;
}

const mainNavItems: NavItem[] = [
  { path: '/dashboard', label: 'Tổng quan', icon: <LayoutDashboard className="w-5 h-5" /> },
  { path: '/food-log', label: 'Nhật ký ăn', icon: <UtensilsCrossed className="w-5 h-5" /> },
  { path: '/foods', label: 'Thực phẩm', icon: <Apple className="w-5 h-5" /> },
  { path: '/recipes', label: 'Công thức', icon: <ChefHat className="w-5 h-5" /> },
  { path: '/meal-plans', label: 'Kế hoạch ăn', icon: <Calendar className="w-5 h-5" /> },
  { path: '/analytics', label: 'Phân tích', icon: <BarChart3 className="w-5 h-5" /> },
  { path: '/goals', label: 'Mục tiêu', icon: <Target className="w-5 h-5" /> },
  { path: '/profile', label: 'Hồ sơ', icon: <User className="w-5 h-5" /> },
];

const adminNavItems: NavItem[] = [
  { path: '/admin', label: 'Quản trị', icon: <Shield className="w-5 h-5" />, adminOnly: true },
  { path: '/admin/users', label: 'Người dùng', icon: <Users className="w-5 h-5" />, adminOnly: true },
];

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  isAdmin?: boolean;
}

export function Sidebar({ isCollapsed, onToggle, isAdmin = false }: SidebarProps) {
  const location = useLocation();

  return (
    <aside
      className={`
        fixed left-0 top-0 h-full bg-white/95 backdrop-blur border-r border-gray-200/80
        transition-all duration-300 z-30 flex flex-col shadow-sm
        ${isCollapsed ? 'w-16' : 'w-64'}
      `}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200/80">
        <Link to="/dashboard" className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 bg-gradient-to-br from-primary to-emerald-600 rounded-2xl flex items-center justify-center shadow-sm">
            <Leaf className="w-5 h-5 text-white" />
          </div>
          {!isCollapsed && (
            <div className="min-w-0">
              <span className="block text-lg font-bold text-gray-900">NutriAI</span>
              <span className="block text-xs text-gray-500">Healthy eating companion</span>
            </div>
          )}
        </Link>
        <button
          onClick={onToggle}
          className="p-1.5 hover:bg-gray-100 rounded-xl transition-colors text-gray-500"
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto">
        <div className="space-y-1.5 px-3">
          {mainNavItems.map((item) => (
            <NavLink
              key={item.path}
              item={item}
              isActive={location.pathname === item.path || location.pathname.startsWith(item.path + '/')}
              isCollapsed={isCollapsed}
            />
          ))}
        </div>

        {/* Admin Section */}
        {isAdmin && (
          <>
            <div className={`mt-6 mb-2 px-4 ${isCollapsed ? 'text-center' : ''}`}>
              {!isCollapsed && (
                <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Quản trị
                </span>
              )}
            </div>
            <div className="space-y-1 px-2">
              {adminNavItems.map((item) => (
                <NavLink
                  key={item.path}
                  item={item}
                  isActive={location.pathname === item.path || location.pathname.startsWith(item.path + '/')}
                  isCollapsed={isCollapsed}
                />
              ))}
            </div>
          </>
        )}
      </nav>

      {/* Settings */}
      <div className="border-t border-gray-200 px-2 py-4">
        <Link
          to="/settings"
          className={`
            flex items-center gap-3 px-3 py-2 rounded-lg
            text-gray-600 hover:bg-gray-50 transition-colors
            ${isCollapsed ? 'justify-center' : ''}
          `}
        >
          <Settings className="w-5 h-5" />
          {!isCollapsed && <span>Cài đặt</span>}
        </Link>
      </div>
    </aside>
  );
}

function NavLink({ item, isActive, isCollapsed }: { item: NavItem; isActive: boolean; isCollapsed: boolean }) {
  return (
    <Link
      to={item.path}
      className={`
        group flex items-center gap-3 px-3 py-2.5 rounded-xl
        transition-all duration-200
        ${isActive
          ? 'bg-primary/10 text-primary font-semibold shadow-sm'
          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800'
        }
        ${isCollapsed ? 'justify-center' : ''}
      `}
      title={isCollapsed ? item.label : undefined}
    >
      <span className={`transition-transform duration-200 ${isActive ? '' : 'group-hover:scale-105'}`}>
        {item.icon}
      </span>
      {!isCollapsed && <span>{item.label}</span>}
      {!isCollapsed && isActive && <span className="ml-auto h-2 w-2 rounded-full bg-primary" />}
    </Link>
  );
}