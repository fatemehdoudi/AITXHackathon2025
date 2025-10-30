// app/(app)/settings.tsx
import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { View } from "react-native";
import {
  Text,
  Switch,
  List,
  Divider,
  TextInput,
  Button,
  ActivityIndicator,
  Snackbar,
} from "react-native-paper";

type AppSettings = {
  id?: number;
  user: number;
  // align these with your DRF serializer fields
  push_notifications?: boolean | null;
  age?: number | null;
  insurance_network?: number | null; // FK id
  insurance_network_name?: string | null; // FK name
  insurance_plan?: number | null;    // FK id
  insurance_plan_name?: string | null;    // FK name
  default_search_radius?: number | null;
  group_id?: string | null;
  member_id?: string | null;
  member_first_name?: string | null;
  member_last_name?: string | null;
  // add any others your serializer exposes
};

const USER_ID = 1; // replace with your logged-in user's id once auth is in place
const BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000"; // fallback for local dev

const ENDPOINT = `${BASE_URL}/api/app-settings/me?user=${USER_ID}`;

export default function Settings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [snack, setSnack] = useState<string | null>(null);

  const [data, setData] = useState<AppSettings>({
    user: USER_ID,
    push_notifications: true,
    age: undefined,
    insurance_network: undefined,
    insurance_plan: undefined,
    default_search_radius: 25,
  });

  // --- helpers ---
  const safeNumber = (v: string) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : undefined;
  };

  const fetchMe = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(ENDPOINT, { method: "GET" });
      if (!res.ok) throw new Error(`GET ${res.status}`);
      const body = (await res.json()) as AppSettings;
      setData((prev) => ({ ...prev, ...body, user: USER_ID }));
    } catch (e: any) {
      setError(e?.message ?? "Failed to load settings");
    } finally {
      setLoading(false);
    }
  }, []);

  const patchMe = useCallback(async (partial: Partial<AppSettings>) => {
    // optimistic update
    setData((prev) => ({ ...prev, ...partial }));
    try {
      setSaving(true);
      const res = await fetch(ENDPOINT, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...partial, user: USER_ID }),
      });
      if (!res.ok) throw new Error(`PATCH ${res.status}`);
      const body = (await res.json()) as AppSettings;
      setData((prev) => ({ ...prev, ...body }));
      setSnack("Saved");
    } catch (e: any) {
      setError(e?.message ?? "Failed to save");
    } finally {
      setSaving(false);
    }
  }, []);

  // debounce for text inputs (age, radius, insurance ids)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const debouncedPatch = useCallback(
    (partial: Partial<AppSettings>) => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        patchMe(partial);
      }, 450);
    },
    [patchMe]
  );

  useEffect(() => {
    fetchMe();
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [fetchMe]);

  if (loading) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
        <ActivityIndicator />
        <Text style={{ marginTop: 12 }}>Loading settings…</Text>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, paddingHorizontal: 8 }}>
      <List.Section>
        {/* <List.Subheader>Preferences</List.Subheader> */}

        {/* <List.Item
          title="Push notifications"
          right={() => (
            <Switch
              value={!!data.push_notifications}
              onValueChange={(val) => patchMe({ push_notifications: val })}
            />
          )}
        /> */}
        {/* <Divider /> */}

        <List.Subheader>Profile</List.Subheader>
        <View style={{ paddingHorizontal: 12, gap: 8 }}>
          <TextInput
            label="Age"
            mode="outlined"
            keyboardType="number-pad"
            value={data.age?.toString() ?? ""}
            onChangeText={(t) => {
              const age = safeNumber(t);
              setData((prev) => ({ ...prev, age }));
              debouncedPatch({ age });
            }}
          />
          <TextInput
            label="Default search radius (miles)"
            mode="outlined"
            keyboardType="number-pad"
            value={data.default_search_radius?.toString() ?? ""}
            onChangeText={(t) => {
              const r = safeNumber(t);
              setData((prev) => ({ ...prev, default_search_radius: r }));
              debouncedPatch({ default_search_radius: r });
            }}
          />
        </View>
        <Divider style={{ marginTop: 8 }} />

        <List.Subheader>Insurance</List.Subheader>
        <View style={{ paddingHorizontal: 12, gap: 8 }}>
          <TextInput
            label="Insurance Network"
            mode="outlined"
            keyboardType="number-pad"
            value={data.insurance_network_name ?? ""}
            onChangeText={(t) => {
              const id = safeNumber(t);
              setData((prev) => ({ ...prev, insurance_network: id }));
              debouncedPatch({ insurance_network: id });
            }}
          />
          <TextInput
            label="Insurance Plan"
            mode="outlined"
            keyboardType="number-pad"
            value={data.insurance_plan_name ?? ""}
            onChangeText={(t) => {
              const id = safeNumber(t);
              setData((prev) => ({ ...prev, insurance_plan: id }));
              debouncedPatch({ insurance_plan: id });
            }}
          />
          <TextInput
            label="Group ID"
            mode="outlined"
            keyboardType="number-pad"
            value={data.group_id ?? ""}
            onChangeText={(t) => {
              const id = safeNumber(t);
              setData((prev) => ({ ...prev, insurance_plan: id }));
              debouncedPatch({ insurance_plan: id });
            }}
          />
          <TextInput
            label="Member ID"
            mode="outlined"
            keyboardType="number-pad"
            value={data.member_id ?? ""}
            onChangeText={(t) => {
              const id = safeNumber(t);
              setData((prev) => ({ ...prev, insurance_plan: id }));
              debouncedPatch({ insurance_plan: id });
            }}
          />
          <TextInput
            label="Member First Name"
            mode="outlined"
            keyboardType="number-pad"
            value={data.member_first_name ?? ""}
            onChangeText={(t) => {
              const id = safeNumber(t);
              setData((prev) => ({ ...prev, insurance_plan: id }));
              debouncedPatch({ insurance_plan: id });
            }}
          />
          <TextInput
            label="Member Last Name"
            mode="outlined"
            keyboardType="number-pad"
            value={data.member_last_name ?? ""}
            onChangeText={(t) => {
              const id = safeNumber(t);
              setData((prev) => ({ ...prev, insurance_plan: id }));
              debouncedPatch({ insurance_plan: id });
            }}
          />
        </View>
        <Divider style={{ marginTop: 8 }} />

        <List.Item
          title="Account"
          description="Update email, password, insurance"
          right={() => (saving ? <ActivityIndicator /> : null)}
        />
        <Divider />
        <List.Item title="About MedMatch" />
      </List.Section>

      <View style={{ padding: 12 }}>
        <Button
          mode="contained"
          onPress={() =>
            // force a full sync (useful if autosave debounced changes are pending)
            patchMe({
              user: USER_ID,
              push_notifications: data.push_notifications,
              age: data.age,
              insurance_network: data.insurance_network,
              insurance_plan: data.insurance_plan,
              default_search_radius: data.default_search_radius,
            })
          }
          disabled={saving}
        >
          {saving ? "Saving…" : "Save"}
        </Button>
      </View>

      <Snackbar visible={!!snack} onDismiss={() => setSnack(null)} duration={1500}>
        {snack}
      </Snackbar>
      <Snackbar visible={!!error} onDismiss={() => setError(null)} duration={2500}>
        {error}
      </Snackbar>
    </View>
  );
}
