document.addEventListener('DOMContentLoaded', function() {
    const authContainer = document.getElementById('authContainer');
    const showSignup = document.getElementById('showSignup');
    const showLogin = document.getElementById('showLogin');
    
    showSignup.addEventListener('click', function(e) {
        e.preventDefault();
        authContainer.classList.add('active');
    });
    
    showLogin.addEventListener('click', function(e) {
        e.preventDefault();
        authContainer.classList.remove('active');
    });
});
// Show/hide password toggle
const togglePassword = document.getElementById('togglePassword');
const loginPassword = document.getElementById('loginPassword');
if (togglePassword && loginPassword) {
    togglePassword.addEventListener('click', function() {
        const type = loginPassword.getAttribute('type') === 'password' ? 'text' : 'password';
        loginPassword.setAttribute('type', type);
        this.innerHTML = type === 'password' ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
    });
}
