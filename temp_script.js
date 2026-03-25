document.addEventListener('DOMContentLoaded', () => {
  if (typeof window.initLayout === 'function') {
    window.initLayout();
  }

  // Activate sidebar link based on current path
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar__link').forEach((link) => {
    const target = link.getAttribute('data-nav');
    if (target && (path === target || path.startsWith(target))) {
      link.classList.add('active');
    }
  });

  // Profile dropdown toggle
  const profileToggle = document.getElementById('topbar-profile-toggle');
  const profileMenu = document.getElementById('topbar-profile-menu');
  if (profileToggle && profileMenu) {
    profileToggle.addEventListener('click', (e) => {
      e.preventDefault();
      profileMenu.classList.toggle('show');
    });
    document.addEventListener('click', (e) => {
      if (!e.target.closest('#topbar-profile')) {
        profileMenu.classList.remove('show');
      }
    });
  }

  // Sidebar toggle for mobile
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('hidden');
    });
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.sidebar') && !e.target.closest('#sidebarToggle')) {
        sidebar.classList.add('hidden');
      }
    });
  }

  // Setup language switcher
  const updateLanguageCheckmarks = () => {
    document.querySelectorAll('[id^="lang-check-"]').forEach(el => el.style.display = 'none');
    const currentLang = i18n.getLanguage();
    const checkEl = document.getElementById(`lang-check-${currentLang}`);
    if (checkEl) checkEl.style.display = 'inline';
  };

  updateLanguageCheckmarks();

  // Toggle language menu
  const langToggle = document.getElementById('topbar-language-toggle');
  const langMenu = document.getElementById('topbar-language-menu');
  if (langToggle && langMenu) {
    langToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      langMenu.classList.toggle('show');
    });
    document.addEventListener('click', () => langMenu.classList.remove('show'));
  }
});