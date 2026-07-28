/* HelpDesk — iOS-style UI JS */

document.addEventListener('DOMContentLoaded', function () {

  // ── Desktop Sidebar toggle ──────────────────────────────
  const sidebar     = document.getElementById('sidebar');
  const mainContent = document.getElementById('mainContent');
  const toggleBtn   = document.getElementById('sidebarToggle');

  if (sidebar && mainContent && toggleBtn) {
    const STATE_KEY = 'hdSidebar';
    let state = localStorage.getItem(STATE_KEY) || 'icon';

    function applyState(s) {
      state = s;
      localStorage.setItem(STATE_KEY, s);
      sidebar.classList.remove('hidden', 'expanded');
      mainContent.classList.remove('sidebar-collapsed', 'sidebar-expanded');
      toggleBtn.classList.remove('sidebar-hidden');

      if (s === 'hidden') {
        sidebar.classList.add('hidden');
        mainContent.classList.add('sidebar-collapsed');
        toggleBtn.classList.add('sidebar-hidden');
        toggleBtn.innerHTML = '<i class="fa fa-bars"></i>';
        toggleBtn.style.left = '16px';
      } else if (s === 'icon') {
        toggleBtn.innerHTML = '<i class="fa fa-chevron-left"></i>';
        toggleBtn.style.left = 'calc(72px + 12px + 8px)';
      } else if (s === 'expanded') {
        sidebar.classList.add('expanded');
        mainContent.classList.add('sidebar-expanded');
        toggleBtn.innerHTML = '<i class="fa fa-chevron-left"></i>';
        toggleBtn.style.left = 'calc(240px + 12px + 8px)';
      }
    }

    toggleBtn.addEventListener('click', function () {
      if (state === 'hidden')    applyState('icon');
      else if (state === 'icon') applyState('expanded');
      else                       applyState('hidden');
    });

    applyState(state);
  }

  // ── Mobile sidebar (hamburger) ──────────────────────────
  const mobileMenuBtn   = document.getElementById('mobileMenuBtn');
  const sidebarOverlay  = document.getElementById('sidebarOverlay');

  if (mobileMenuBtn && sidebar && sidebarOverlay) {
    function openMobileSidebar() {
      sidebar.classList.add('mobile-open');
      sidebarOverlay.style.display = 'block';
      document.body.style.overflow = 'hidden';
    }
    function closeMobileSidebar() {
      sidebar.classList.remove('mobile-open');
      sidebarOverlay.style.display = 'none';
      document.body.style.overflow = '';
    }
    mobileMenuBtn.addEventListener('click', openMobileSidebar);
    sidebarOverlay.addEventListener('click', closeMobileSidebar);
    // Close on nav link tap
    sidebar.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', closeMobileSidebar);
    });
  }

  // ── iOS spring press on interactive elements ────────────
  document.querySelectorAll('.btn, .stat-card, .card-hover, .mob-nav-item').forEach(el => {
    el.addEventListener('touchstart', function() {
      this.style.transition = 'transform 0.1s cubic-bezier(0.4,0,0.2,1)';
      this.style.transform = 'scale(0.96)';
    }, { passive: true });
    el.addEventListener('touchend', function() {
      this.style.transition = 'transform 0.35s cubic-bezier(0.34,1.56,0.64,1)';
      this.style.transform = 'scale(1)';
    }, { passive: true });
    el.addEventListener('touchcancel', function() {
      this.style.transform = 'scale(1)';
    }, { passive: true });
  });

  // ── Auto-dismiss alerts (iOS slide out) ─────────────────
  document.querySelectorAll('.alert').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.4s ease, transform 0.4s cubic-bezier(0.4,0,0.2,1), max-height 0.4s ease';
      el.style.opacity = '0';
      el.style.transform = 'translateY(-10px)';
      el.style.maxHeight = '0';
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });

  // ── Stagger card animations ─────────────────────────────
  document.querySelectorAll('.card').forEach((card, i) => {
    card.style.animationDelay = `${i * 0.05}s`;
  });

  // ── Stat card glow on hover ─────────────────────────────
  document.querySelectorAll('.stat-card').forEach(card => {
    card.addEventListener('mousemove', function (e) {
      const r = this.getBoundingClientRect();
      const x = e.clientX - r.left;
      const y = e.clientY - r.top;
      this.style.background = `radial-gradient(circle at ${x}px ${y}px, rgba(108,92,231,0.07), transparent 65%)`;
    });
    card.addEventListener('mouseleave', function () { this.style.background = ''; });
  });

  // ── Smooth scroll for anchors ───────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href !== '#') {
        e.preventDefault();
        const target = document.querySelector(href);
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ── Submit button loading state ─────────────────────────
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function() {
      const btns = this.querySelectorAll('button[type="submit"]');
      btns.forEach(btn => {
        if (!btn.disabled) {
          const orig = btn.innerHTML;
          btn.disabled = true;
          btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
          setTimeout(() => { btn.disabled = false; btn.innerHTML = orig; }, 6000);
        }
      });
    });
  });

  // ── Tooltips ────────────────────────────────────────────
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el);
  });

  // ── File preview ─────────────────────────────────────────
  document.querySelectorAll('input[type="file"]').forEach(input => {
    input.addEventListener('change', function() {
      const previewId = this.dataset.preview;
      if (!previewId || !this.files.length) return;
      const preview = document.getElementById(previewId);
      if (!preview) return;
      preview.innerHTML = '';
      Array.from(this.files).forEach(file => {
        const item = document.createElement('div');
        item.className = 'file-preview-item';
        item.innerHTML = `<div class="d-flex align-items-center gap-2"><i class="fa fa-file text-primary"></i><div><div class="small fw-semibold">${file.name}</div><div class="text-muted" style="font-size:.75rem">${(file.size/1024).toFixed(0)} KB</div></div></div>`;
        preview.appendChild(item);
      });
      preview.style.display = 'block';
    });
  });

  // ── Test notification button ─────────────────────────────
  const testBtn = document.getElementById('testNotificationBtn');
  if (testBtn) {
    testBtn.addEventListener('click', function() {
      if (window.SimpleNotifications) {
        window.SimpleNotifications.success('Test ✅', 'Notification system working!', 4000);
      }
    });
  }

  // ── Confirm on destructive actions ──────────────────────
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', function(e) {
      if (!confirm(this.dataset.confirm)) { e.preventDefault(); e.stopPropagation(); }
    });
  });

});


  // ── Living progress bars (animate width) ────────────────
  document.querySelectorAll('.progress-bar').forEach(bar => {
    const targetWidth = bar.style.width;
    bar.style.width = '0';
    setTimeout(() => { bar.style.width = targetWidth; }, 100);
  });

  // ── Icon rotation on hover ──────────────────────────────
  document.querySelectorAll('.fa').forEach(icon => {
    icon.addEventListener('mouseenter', function() {
      this.style.transition = 'transform 0.4s cubic-bezier(0.68,-0.55,0.265,1.55)';
      this.style.transform = 'scale(1.15) rotate(10deg)';
    });
    icon.addEventListener('mouseleave', function() {
      this.style.transform = 'scale(1) rotate(0deg)';
    });
  });

  // ── Ripple effect on buttons ───────────────────────────
  document.querySelectorAll('.btn, .mob-nav-item').forEach(btn => {
    btn.addEventListener('click', function(e) {
      const ripple = document.createElement('span');
      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;
      
      ripple.style.width = ripple.style.height = `${size}px`;
      ripple.style.left = `${x}px`;
      ripple.style.top = `${y}px`;
      ripple.style.position = 'absolute';
      ripple.style.borderRadius = '50%';
      ripple.style.background = 'rgba(255,255,255,0.5)';
      ripple.style.transform = 'scale(0)';
      ripple.style.animation = 'ripple 0.6s ease-out';
      ripple.style.pointerEvents = 'none';
      
      this.style.position = 'relative';
      this.style.overflow = 'hidden';
      this.appendChild(ripple);
      
      setTimeout(() => ripple.remove(), 600);
    });
  });

  // Add ripple keyframes
  const style = document.createElement('style');
  style.textContent = `
    @keyframes ripple {
      to { transform: scale(4); opacity: 0; }
    }
  `;
  document.head.appendChild(style);

  // ── Stat numbers count-up animation ────────────────────
  document.querySelectorAll('.stat-value').forEach(stat => {
    const target = parseInt(stat.textContent);
    if (isNaN(target)) return;
    let current = 0;
    const increment = target / 30;
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        stat.textContent = target;
        clearInterval(timer);
      } else {
        stat.textContent = Math.floor(current);
      }
    }, 30);
  });

  // ── Smooth scroll with momentum ────────────────────────
  let scrollTimeout;
  window.addEventListener('scroll', () => {
    document.body.style.pointerEvents = 'none';
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(() => {
      document.body.style.pointerEvents = 'auto';
    }, 50);
  }, { passive: true });

});
