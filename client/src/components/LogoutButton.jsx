import { useMsal } from "@azure/msal-react";

export default function LogoutButton() {
  const { instance } = useMsal();

  const handleLogout = async () => {
    await instance.logoutPopup();
  };

  return (
    <button
      onClick={handleLogout}
      className="px-4 py-2 bg-gray-700 text-white rounded-xl hover:bg-gray-800"
    >
      Logout
    </button>
  );
}
