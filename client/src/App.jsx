import { useEffect, useState } from "react";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { auth } from "./firebase";

import LoginPage from "./pages/LoginPage";
import MainPage from "./pages/MainPage";

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

 useEffect(() => {
  const unsub = onAuthStateChanged(auth, (u) => {
    console.log("Auth state changed:", u);
    setUser(u);
    setChecking(false);
  });

    return () => unsub();
  }, []);

  async function handleLogout() {
    await signOut(auth);
  }

  if (checking) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <div className="text-sm text-gray-300">Checking authentication...</div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  return <MainPage user={user} onLogout={handleLogout} />;
}
