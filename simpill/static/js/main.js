/**
 * SimPill – AI Powered Smart Healthcare & Medicine Management System
 * Frontend UI Interactions & Enhancements
 */

document.addEventListener('DOMContentLoaded', function() {
    // 1. Auto-dismiss Alert messages after 5 seconds
    const alerts = document.querySelectorAll('.alert-simpill');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            // Smoothly fade out using bootstrap transition helper if available, or basic css transition
            alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // 2. Toggle password visibility
    const passwordToggleButtons = document.querySelectorAll('.password-toggle-btn');
    passwordToggleButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const inputId = btn.getAttribute('data-target');
            const passwordInput = document.getElementById(inputId);
            if (passwordInput) {
                const icon = btn.querySelector('i');
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    icon.classList.remove('bi-eye');
                    icon.classList.add('bi-eye-slash');
                } else {
                    passwordInput.type = 'password';
                    icon.classList.remove('bi-eye-slash');
                    icon.classList.add('bi-eye');
                }
            }
        });
    });

    // 3. Confirm Delete Actions
    const deleteButtons = document.querySelectorAll('.confirm-delete-btn');
    deleteButtons.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            const name = btn.getAttribute('data-user-name') || 'this user';
            const role = btn.getAttribute('data-user-role') || 'staff member';
            const confirmed = confirm(`Are you sure you want to delete ${role} "${name}"?\nThis action cannot be undone.`);
            if (!confirmed) {
                e.preventDefault();
            }
        });
    });

    // 4. Subtle Micro-animations on cards
    const hoverCards = document.querySelectorAll('.glass-card, .stat-card');
    hoverCards.forEach(function(card) {
        card.addEventListener('mouseenter', function() {
            card.style.transform = 'translateY(-4px)';
            card.style.transition = 'transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1)';
        });
        card.addEventListener('mouseleave', function() {
            card.style.transform = 'translateY(0)';
        });
    });
});
