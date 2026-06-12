import { create } from "zustand";

interface AuthState {
  token: string | null;
  orgId: string | null;
  role: string | null;
  userEmail: string | null;
  isAuthenticated: boolean;
  login: (token: string, orgId: string, role: string, email: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => {
  // Initialize state from localStorage if running in browser
  const isBrowser = typeof window !== "undefined";
  const storedToken = isBrowser ? localStorage.getItem("token") : null;
  const storedOrgId = isBrowser ? localStorage.getItem("orgId") : null;
  const storedRole = isBrowser ? localStorage.getItem("role") : null;
  const storedEmail = isBrowser ? localStorage.getItem("userEmail") : null;

  return {
    token: storedToken,
    orgId: storedOrgId,
    role: storedRole,
    userEmail: storedEmail,
    isAuthenticated: !!storedToken,
    login: (token, orgId, role, email) => {
      if (isBrowser) {
        localStorage.setItem("token", token);
        localStorage.setItem("orgId", orgId);
        localStorage.setItem("role", role);
        localStorage.setItem("userEmail", email);
      }
      set({
        token,
        orgId,
        role,
        userEmail: email,
        isAuthenticated: true,
      });
    },
    logout: () => {
      if (isBrowser) {
        localStorage.removeItem("token");
        localStorage.removeItem("orgId");
        localStorage.removeItem("role");
        localStorage.removeItem("userEmail");
      }
      set({
        token: null,
        orgId: null,
        role: null,
        userEmail: null,
        isAuthenticated: false,
      });
    },
  };
});
