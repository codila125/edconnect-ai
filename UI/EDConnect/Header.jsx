export default function Header() {
  return (
    <header className="bg-white header-shadow">
      <div className="px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button className="p-3 hover:bg-gray-100 rounded-full" onClick={() => toggleSidebar()}>
              <span className="material-icons text-gray-600">menu</span>
            </button>
            <div className="flex items-center space-x-2">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-300 to-blue-300 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">ED</span>
              </div>
              <span className="text-xl text-gray-700 font-semibold">Ed-Connect AI</span>
            </div>
          </div>
          <div className="flex items-center">
            <div
              className="w-8 h-8 bg-gradient-to-r from-purple-300 to-blue-300 rounded-full flex items-center justify-center cursor-pointer"
              onClick={() => showProfileMenu()}
            >
              <span className="text-white text-sm font-medium">T</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}