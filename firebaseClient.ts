// firebase.ts
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyCVlyesFrNYFPTagle51w7U9TY0SZ3F1ms",
  authDomain: "jurisclarify.firebaseapp.com",
  projectId: "jurisclarify",
  storageBucket: "jurisclarify.appspot.com",
  messagingSenderId: "289623964924",
  appId: "1:289623964924:web:26e5f45e089d2841f06b79"
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const provider = new GoogleAuthProvider();
