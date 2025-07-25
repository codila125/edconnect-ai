export default function SidebarOverlay() {
  return (
    <div id="sidebar-overlay" className="fixed inset-0 bg-black bg-opacity-50 hidden z-30" onClick={() => closeSidebar()}></div>
  );
}
