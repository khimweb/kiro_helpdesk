/* HelpDesk — Dashboard UI */

document.addEventListener('DOMContentLoaded', function () {

  // ── Sidebar toggle ──────────────────────────────────────
  const sidebar     = document.getElementById('sidebar');
  const mainContent = document.getElementById('mainContent');
  const toggleBtn   = document.getElementById('sidebarToggle');

  if (sidebar && mainContent && toggleBtn) {
    const STATE_KEY = 'hdSidebar'; // hidden | icon | expanded
    let state = localStorage.getItem(STATE_KEY) || 'icon';

    function applyState(s, animate) {
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
        toggleBtn.title = 'Show sidebar';
        toggleBtn.style.left = '16px';
      } else if (s === 'icon') {
        mainContent.style.marginLeft = '';
        toggleBtn.innerHTML = '<i class="fa fa-chevron-left"></i>';
        toggleBtn.title = 'Expand sidebar';
        toggleBtn.style.left = 'calc(72px + 12px + 8px)';
      } else if (s === 'expanded') {
        sidebar.classList.add('expanded');
        mainContent.classList.add('sidebar-expanded');
        toggleBtn.innerHTML = '<i class="fa fa-chevron-left"></i>';
        toggleBtn.title = 'Collapse sidebar';
        toggleBtn.style.left = 'calc(240px + 12px + 8px)';
      }
    }

    // Cycle: icon → expanded → hidden → icon
    toggleBtn.addEventListener('click', function () {
      if (state === 'hidden')   applyState('icon');
      else if (state === 'icon') applyState('expanded');
      else                       applyState('hidden');
    });

    applyState(state);
  }

  // ── Auto-dismiss alerts ─────────────────────────────────
  document.querySelectorAll('.alert').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      el.style.opacity = '0';
      el.style.transform = 'translateY(-8px)';
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });

  // ── Stagger card animations ─────────────────────────────
  document.querySelectorAll('.card').forEach((card, i) => {
    card.style.animationDelay = `${i * 0.04}s`;
  });

  // ── Stat card hover glow ────────────────────────────────
  document.querySelectorAll('.stat-card').forEach(card => {
    card.addEventListener('mousemove', function (e) {
      const r = this.getBoundingClientRect();
      const x = e.clientX - r.left;
      const y = e.clientY - r.top;
      this.style.background = `radial-gradient(circle at ${x}px ${y}px, rgba(108,92,231,0.06), transparent 70%)`;
    });
    card.addEventListener('mouseleave', function () {
      this.style.background = '';
    });
  });

});
  // ── AI Assistant functionality ────────────────────────────────
  const aiAssistant = document.getElementById('aiAssistant');
  if (aiAssistant) {
    // AI suggestion badges
    document.querySelectorAll('.ai-suggestion-badge').forEach(badge => {
      badge.addEventListener('click', function() {
        const prompt = this.dataset.prompt;
        const input = document.querySelector('.ai-prompt-input');
        if (input) {
          input.value = prompt;
          input.focus();
        }
      });
    });

    // Auto-expand textareas
    document.querySelectorAll('textarea').forEach(textarea => {
      textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
      });
    });
  }

  // ── File attachment preview ────────────────────────────────────
  const fileInputs = document.querySelectorAll('input[type="file"]');
  fileInputs.forEach(input => {
    input.addEventListener('change', function() {
      const files = this.files;
      const previewId = this.dataset.preview;
      
      if (previewId && files.length > 0) {
        const preview = document.getElementById(previewId);
        if (preview) {
          preview.innerHTML = '';
          
          Array.from(files).forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-preview-item';
            fileItem.innerHTML = `
              <div class="d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center gap-2">
                  <i class="fas fa-file text-primary"></i>
                  <div>
                    <div class="small fw-semibold">${file.name}</div>
                    <div class="text-muted x-small">${(file.size / 1024).toFixed(0)} KB</div>
                  </div>
                </div>
                <button type="button" class="btn btn-sm btn-outline-danger remove-file" data-index="${index}">
                  <i class="fas fa-times"></i>
                </button>
              </div>
            `;
            preview.appendChild(fileItem);
          });
          
          preview.style.display = 'block';
          
          // Add remove functionality
          preview.querySelectorAll('.remove-file').forEach(btn => {
            btn.addEventListener('click', function() {
              const index = parseInt(this.dataset.index);
              const dt = new DataTransfer();
              const filesArray = Array.from(files);
              
              filesArray.forEach((file, i) => {
                if (i !== index) {
                  dt.items.add(file);
                }
              });
              
              this.files = dt.files;
              this.dispatchEvent(new Event('change'));
            });
          });
        }
      }
    });
  });

  // ── Form validation enhancement ───────────────────────────────
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', function() {
      const submitButtons = this.querySelectorAll('button[type="submit"]');
      submitButtons.forEach(btn => {
        if (!btn.disabled) {
          const originalHTML = btn.innerHTML;
          btn.disabled = true;
          btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
          
          // Restore button after 5 seconds (in case of error)
          setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = originalHTML;
          }, 5000);
        }
      });
    });
  });

  // ── Tooltips initialization ───────────────────────────────────
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  if (tooltipTriggerList.length > 0) {
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
  }

  // ── Character counter for textareas ────────────────────────────
  document.querySelectorAll('textarea[data-maxlength]').forEach(textarea => {
    const maxLength = parseInt(textarea.dataset.maxlength);
    const counterId = textarea.dataset.counter;
    const counter = counterId ? document.getElementById(counterId) : null;
    
    function updateCounter() {
      const length = textarea.value.length;
      if (counter) {
        counter.textContent = `${length}/${maxLength}`;
        counter.classList.remove('text-warning', 'text-danger');
        
        if (length > maxLength * 0.9) {
          counter.classList.add('text-warning');
        } else if (length > maxLength) {
          counter.classList.add('text-danger');
        }
      }
      
      if (length > maxLength) {
        textarea.classList.add('is-invalid');
      } else {
        textarea.classList.remove('is-invalid');
      }
    }
    
    textarea.addEventListener('input', updateCounter);
    updateCounter(); // Initial update
  });

  // ── Smooth scrolling for in-page anchors ────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href !== '#') {
        e.preventDefault();
        const target = document.querySelector(href);
        if (target) {
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      }
    });
  });

  // ── Modal confirmation for destructive actions ─────────────────
  const confirmButtons = document.querySelectorAll('[data-confirm]');
  confirmButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      const message = this.dataset.confirm;
      if (!confirm(message)) {
        e.preventDefault();
        e.stopPropagation();
      }
    });
  });