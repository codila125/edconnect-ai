export default function ProfileMenu() {
  return (
    <div id="profile-menu" className="fixed top-16 right-6 w-64 bg-white rounded-lg shadow-lg hidden z-50">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-gradient-to-r from-purple-300 to-blue-300 rounded-full flex items-center justify-center">
            <span className="text-white text-lg font-medium">T</span>
          </div>
          <div>
            <div className="font-medium text-gray-900">Teacher</div>
            <div className="text-sm text-gray-500">teacher@school.edu</div>
          </div>
        </div>
      </div>
      <div className="py-2">
        <a href="#" className="flex items-center space-x-3 px-4 py-2 text-gray-700 hover:bg-gray-100">
          <span className="material-icons text-gray-600">logout</span>
          <span>Sign out</span>
        </a>
      </div>
    </div>
  );
}