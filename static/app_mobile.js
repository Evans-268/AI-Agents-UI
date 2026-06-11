document.addEventListener('DOMContentLoaded', function() {
    const openMobileSidebarBtn = document.getElementById('openMobileSidebarBtn');
    const sidebar = document.querySelector('.sidebar');
    const toggleSidebarBtn = document.getElementById('toggleSidebarBtn'); // Tombol yang ada di dalam sidebar

    let overlay = document.createElement('div');
    overlay.className = 'mobile-overlay';
    document.body.appendChild(overlay);

    function toggleMobileSidebar() {
        if (window.innerWidth <= 768) {
            sidebar.classList.toggle('mobile-open');
            overlay.classList.toggle('active');
        }
    }

    if (openMobileSidebarBtn) {
        openMobileSidebarBtn.addEventListener('click', toggleMobileSidebar);
    }

    if (toggleSidebarBtn) {
        toggleSidebarBtn.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                toggleMobileSidebar();
                e.stopImmediatePropagation(); 
            }
        });
    }

    overlay.addEventListener('click', toggleMobileSidebar);
});