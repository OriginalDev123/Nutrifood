import { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

interface TabItem {
  id: string;
  label: string;
  icon?: ReactNode;
  disabled?: boolean;
}

interface TabsContextType {
  activeTab: string;
  setActiveTab: (id: string) => void;
}

const TabsContext = createContext<TabsContextType | null>(null);

interface TabsProps {
  defaultTab: string;
  children: ReactNode;
  onChange?: (tabId: string) => void;
  className?: string;
}

export function Tabs({ defaultTab, children, onChange, className = '' }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultTab);

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
    onChange?.(tabId);
  };

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab: handleTabChange }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

interface TabListProps {
  tabs?: TabItem[];
  className?: string;
  children?: ReactNode;
}

export function TabList({ tabs, className = '', children }: TabListProps) {
  const tabsContext = useContext(TabsContext);

  // If children are provided, render them (backward compatible)
  if (children) {
    return (
      <div className={`flex border-b border-gray-200 ${className}`}>
        {children}
      </div>
    );
  }

  // If tabs array is provided, render from array (requires Tabs context)
  if (!tabs || !Array.isArray(tabs) || !tabsContext) {
    return null;
  }

  const { activeTab, setActiveTab } = tabsContext;

  return (
    <div className={`flex border-b border-gray-200 ${className}`}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => !tab.disabled && setActiveTab(tab.id)}
          disabled={tab.disabled}
          className={`
            flex items-center gap-2 px-4 py-3 text-sm font-medium
            border-b-2 transition-colors duration-200
            ${
              activeTab === tab.id
                ? 'border-primary text-primary'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }
            ${tab.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
        >
          {tab.icon}
          {tab.label}
        </button>
      ))}
    </div>
  );
}

interface TabPanelProps {
  tabId: string;
  children: ReactNode;
}

export function TabPanel({ tabId, children }: TabPanelProps) {
  const tabsContext = useContext(TabsContext);

  if (!tabsContext) return null;

  if (tabsContext.activeTab !== tabId) return null;

  return <div>{children}</div>;
}