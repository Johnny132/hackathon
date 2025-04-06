document.addEventListener('DOMContentLoaded', () => {
    const wrapper = document.querySelector('.wrapper');
    const loginLink = document.querySelector('.login-link');
    const registerLink = document.querySelector('.register-link');
    const btnPopup = document.querySelector('.btnLogin-popup');
    const iconClose = document.querySelector('.icon-close');
    
    registerLink.addEventListener('click', (e) => {
        e.preventDefault();
        wrapper.classList.add('active');
    });
    
    loginLink.addEventListener('click', (e) => {
        e.preventDefault();
        wrapper.classList.remove('active');
    });
    
    btnPopup.addEventListener('click', () => {
        wrapper.classList.add('active-popup');
    });
    
    iconClose.addEventListener('click', () => {
        wrapper.classList.remove('active-popup');
    });
    
    // Handle login form submission
    const loginForm = document.querySelector('.form-box.login form');
    
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        // Get the form data
        const email = loginForm.querySelector('input[name="email"]').value;
        const password = loginForm.querySelector('input[name="password"]').value;
        
        // In a real application, you would validate these credentials with your server
        // For this example, we'll just simulate a successful login
        
        // Simple validation (just checking if fields are filled)
        if (email && password) {
            // Redirect to chatbot page
            window.location.href = '/chatbot';
        } else {
            alert('Please enter both email and password');
        }
    });
    
    // Handle registration form submission
    const registerForm = document.querySelector('.form-box.register form');
    
    registerForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        // Get the form data
        const username = registerForm.querySelector('input[name="username"]').value;
        const email = registerForm.querySelector('input[name="email"]').value;
        const password = registerForm.querySelector('input[name="password"]').value;
        const terms = registerForm.querySelector('input[name="terms"]').checked;
        
        // In a real application, you would send this data to your server
        
        // Simple validation
        if (username && email && password && terms) {
            alert('Registration successful! Please login.');
            wrapper.classList.remove('active');
        } else {
            alert('Please fill all fields and agree to the terms');
        }
    });
});