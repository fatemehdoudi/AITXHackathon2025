// lib/auth.ts
import AsyncStorage from "@react-native-async-storage/async-storage";

export const API_BASE = "http://127.0.0.1:8000"; // change to your LAN / prod URL

export async function loginWithPassword(email: string, password: string) {
    console.log('logging in with email: ', email)
    console.log('logging in with password', password)
  const res = await fetch(`${API_BASE}/api/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: email, password }),
  });
  if (!res.ok) throw new Error("Invalid email or password.");
  const data = await res.json();
  await AsyncStorage.multiSet([
    ["access", data.access],
    ["refresh", data.refresh],
  ]);
  return data;
}

export async function registerAccount(payload: {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}) {
  // Point this to your DRF registration endpoint (adjust fields to your serializer)
  const res = await fetch(`${API_BASE}/api/auth/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Registration failed.");
  }
  return res.json();
}
