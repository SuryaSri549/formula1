'use strict';

// Import Firebase SDK
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js';
import { 
    getAuth, 
    createUserWithEmailAndPassword, 
    signInWithEmailAndPassword, 
    signOut, 
    onAuthStateChanged 
} from 'https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js';

// Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyAfR_9gYFabi9rYpd0a0SB9yBJppdYiCIU",
    authDomain: "formula1-a45c7.firebaseapp.com",
    projectId: "formula1-a45c7",
    storageBucket: "formula1-a45c7.firebasestorage.app",
    messagingSenderId: "200804652101",
    appId: "1:200804652101:web:3ed5ec7803a7e6a76fbf2c"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Handle authentication state changes
onAuthStateChanged(auth, (user) => {
    if (user) {
        console.log("User is logged in:", user.email);
        
        user.getIdToken().then((token) => {
            // Set cookie with SameSite=Lax for better compatibility
            document.cookie = `token=${token}; path=/; SameSite=Lax`;
            
            // Redirect logic
            if (window.location.pathname !== "/dashboard" && !sessionStorage.getItem("authRedirected")) {
                sessionStorage.setItem("authRedirected", "true");
                window.location.href = "/dashboard";
            }
        });
    } else {
        console.log("User is not logged in");
        // Clear cookie on logout
        document.cookie = "token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
        
        // Redirect from dashboard if logged out
        if (window.location.pathname === "/dashboard") {
            window.location.href = "/";
        }
    }
});

// Attach event listeners after DOM loads
window.addEventListener("load", function () {
    console.log("Firebase authentication script loaded");

    // Sign Up Handler
    const signUpButton = document.getElementById("sign-up");
    if (signUpButton) {
        signUpButton.addEventListener('click', function () {
            const email = document.getElementById("email").value;
            const password = document.getElementById("password").value;
            const alertMessage = document.getElementById("alert-message");

            createUserWithEmailAndPassword(auth, email, password)
                .then((userCredential) => {
                    return userCredential.user.getIdToken();
                })
                .then((token) => {
                    document.cookie = `token=${token}; path=/; SameSite=Lax`;
                    alertMessage.style.display = "block";
                    alertMessage.classList.add("alert-success");
                    alertMessage.textContent = "✅ Signup successful! Redirecting...";

                    sessionStorage.removeItem("authRedirected");
                    setTimeout(() => window.location.href = "/dashboard", 2000);
                })
                .catch((error) => {
                    console.error("Sign-up error:", error);
                    alertMessage.style.display = "block";
                    alertMessage.classList.remove("alert-success");
                    alertMessage.classList.add("alert-danger");
                    alertMessage.textContent = `❌ Error: ${error.message}`;
                });
        });
    }

    // Login Handler
    const loginButton = document.getElementById("login");
    if (loginButton) {
        loginButton.addEventListener('click', function () {
            const email = document.getElementById("email").value;
            const password = document.getElementById("password").value;

            signInWithEmailAndPassword(auth, email, password)
                .then((userCredential) => {
                    return userCredential.user.getIdToken();
                })
                .then((token) => {
                    document.cookie = `token=${token}; path=/; SameSite=Lax`;
                    sessionStorage.removeItem("authRedirected");
                    window.location.href = "/dashboard";
                })
                .catch((error) => {
                    console.error("Login error:", error);
                    const alertMessage = document.getElementById("alert-message");
                    if (alertMessage) {
                        alertMessage.style.display = "block";
                        alertMessage.textContent = `❌ Error: ${error.message}`;
                    }
                });
        });
    }

    // Logout Handler
    const logoutButton = document.getElementById("logout-btn");
    if (logoutButton) {
        logoutButton.addEventListener("click", function () {
            signOut(auth)
                .then(() => {
                    document.cookie = "token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
                    sessionStorage.removeItem("authRedirected");
                    window.location.href = "/";
                })
                .catch((error) => {
                    console.error("Logout error:", error);
                    alert(`Logout failed: ${error.message}`);
                });
        });
    }
});