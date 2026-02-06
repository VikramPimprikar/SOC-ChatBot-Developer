import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyD9jFH_8yKLZMy5LzPZSUuQsm1Rkp0JpIw",
  authDomain: "soc-chatbot-10663.firebaseapp.com",
  projectId: "soc-chatbot-10663",
  storageBucket: "soc-chatbot-10663.firebasestorage.app",
  messagingSenderId: "528255087612",
  appId: "1:528255087612:web:70fe6f4602e4f97cb27879",
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);

export const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({
  prompt: "select_account",
});
