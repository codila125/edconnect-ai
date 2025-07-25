export default function Sidebar() {
  return (
    <div id="sidebar" className="fixed inset-y-0 left-0 w-64 bg-white shadow-lg transform -translate-x-full transition-transform duration-300 ease-in-out z-40">
      <div className="p-6">
        <div className="flex items-center space-x-2 mb-8">
          <div className="w-8 h-8 bg-gradient-to-r from-purple-300 to-blue-300 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">ED</span>
          </div>
          <span className="text-lg text-gray-700 font-semibold">Ed-Connect AI</span>
        </div>
        <nav className="space-y-2">
          <a href="#" onClick={() => { showDashboard(); closeSidebar(); }} className="flex items-center space-x-3 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
            <span className="material-icons text-gray-600">home</span>
            <span>Classes</span>
          </a>
          <a href="#" onClick={() => { showCalendar(); closeSidebar(); }} className="flex items-center space-x-3 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
            <span className="material-icons text-gray-600">calendar_today</span>
            <span>Calendar</span>
          </a>
        </nav>
        <div className="mt-8">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">Teaching</h3>
          <div id="teaching-classes" className="space-y-1">
            {/* Dynamic classes */}
          </div>
        </div>
      </div>
    </div>
  );
}