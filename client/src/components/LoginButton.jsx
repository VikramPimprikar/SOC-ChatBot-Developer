import { useMsal } from "@azure/msal-react";
import { loginRequest } from "../authConfig";

export default function LoginButton() {
  const { instance } = useMsal();

  const handleLogin = async () => {
    await instance.loginPopup(loginRequest);
  };

  return (
    <button
      onClick={handleLogin}
      className="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700"
    >
      Login with Microsoft
    </button>
  );
}
