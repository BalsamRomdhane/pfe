/*
  layout.js provides global UI behavior for the ComplianceAI dashboard.
*/

(function () {
  const SIDEBAR_STATE_KEY = 'complianceai:sidebarCollapsed';
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('sidebarToggle');
  const profileToggle = document.getElementById('topbar-profile-toggle');
  const profileDropdown = document.getElementById('topbar-profile');
  const notificationBtn = document.getElementById('topbar-notifications');

  const setSidebarState = (collapsed) => {
    if (!sidebar) return;
    sidebar.classList.toggle('collapsed', collapsed);
    try {
      localStorage.setItem(SIDEBAR_STATE_KEY, collapsed ? '1' : '0');
    } catch {
      // ignore storage errors
    }
  };

  const initSidebar = () => {
    if (!sidebar || !toggle) return;

    // Restore sidebar state from previous session
    try {
      const stored = localStorage.getItem(SIDEBAR_STATE_KEY);
      if (stored !== null) {
        setSidebarState(stored === '1');
      } else if (window.innerWidth <= 768) {
        setSidebarState(true);
      }
    } catch {
      // ignore storage failures
    }

    toggle.addEventListener('click', () => {
      setSidebarState(!sidebar.classList.contains('collapsed'));
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (event) => {
      if (!sidebar.contains(event.target) && !toggle.contains(event.target)) {
        if (!sidebar.classList.contains('collapsed') && window.innerWidth <= 768) {
          setSidebarState(true);
        }
      }
    });
  };

  const initProfileMenu = () => {
    if (!profileToggle || !profileDropdown) return;

    profileToggle.addEventListener('click', (event) => {
      event.stopPropagation();
      profileDropdown.classList.toggle('open');
    });

    document.addEventListener('click', (event) => {
      if (!profileDropdown.contains(event.target)) {
        profileDropdown.classList.remove('open');
      }
    });
  };

  const initSearch = () => {
    const searchInput = document.getElementById('topbar-search');
    if (!searchInput) return;

    searchInput.addEventListener('keypress', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        // Placeholder: implement global search behavior.
        console.log('Search:', searchInput.value);
      }
    });
  };

  const initNotifications = () => {
    if (!notificationBtn) return;

    notificationBtn.addEventListener('click', () => {
      // Placeholder: implement notifications panel.
      alert('No notifications currently.');
    });
  };

  const initLayout = () => {
    initSidebar();
    initProfileMenu();
    initSearch();
    initNotifications();
  };

  window.initLayout = initLayout;
})();
