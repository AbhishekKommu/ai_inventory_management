/* ============================================================
   SMARTSTOCK AI - MAIN JAVASCRIPT
   ============================================================ */

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages
    setTimeout(() => {
        document.querySelectorAll('.flash').forEach(el => {
            el.style.transition = 'all 0.5s ease';
            el.style.opacity = '0';
            el.style.transform = 'translateX(100%)';
            setTimeout(() => el.remove(), 500);
        });
    }, 5000);
    
    // Add ripple effect to buttons
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                border-radius: 50%;
                background: rgba(255,255,255,0.5);
                transform: scale(0);
                animation: ripple 0.6s linear;
                pointer-events: none;
                width: ${rect.width}px;
                height: ${rect.width}px;
                left: ${e.clientX - rect.left - rect.width/2}px;
                top: ${e.clientY - rect.top - rect.width/2}px;
            `;
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });
});

/* Password toggle */
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const btn = input.parentElement.querySelector('.password-toggle i');
    if (input.type === 'password') {
        input.type = 'text';
        btn.classList.remove('fa-eye');
        btn.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        btn.classList.remove('fa-eye-slash');
        btn.classList.add('fa-eye');
    }
}

/* Password strength checker */
function checkPasswordStrength(password) {
    const bars = document.querySelectorAll('#passwordStrength .strength-bar');
    bars.forEach(b => b.className = 'strength-bar');
    
    if (!password) return;
    
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password) && /[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password) && /[^A-Za-z0-9]/.test(password)) strength++;
    
    const level = strength === 1 ? 'weak' : strength === 2 ? 'medium' : 'strong';
    for (let i = 0; i < strength; i++) {
        bars[i].classList.add(level);
    }
}

/* Confirm dialogs */
function confirmDelete(name) {
    return confirm(`Are you sure you want to delete "${name}"? This cannot be undone.`);
}

/* Number formatter */
function formatCurrency(num) {
    return '$' + parseFloat(num).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}