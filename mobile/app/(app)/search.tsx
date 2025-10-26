import React, { useEffect, useMemo, useState, useCallback } from "react";
import { View, FlatList } from "react-native";
import {
  Searchbar,
  TextInput,
  Button,
  Card,
  Text,
  Chip,
  Divider,
  Menu,
  IconButton,
  ActivityIndicator,
  HelperText,
} from "react-native-paper";
import * as Location from "expo-location";
import Constants from "expo-constants";

// ----------------- Types -----------------
type Provider = {
  id: string;
  name: string;
  phone: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  lat: number;
  lon: number;            // we’ll map backend lng -> lon
  medmatch_score: number; // 1-10 (placeholder for now)
};
type Coords = { lat: number; lon: number } | null;

type BackendProvider = {
  name: string;
  specialty?: string;
  address: string; // "3310 Longmire Dr, College Station, TX 77845"
  phone?: string;  // "Call (979) 691-3300"
  lat: number;
  lng: number;
  source_file?: string;
};

// ----------------- Config -----------------
const API_BASE = "http://127.0.0.1:8000/api";
const PROMPT = "Search by specialty, symptoms, or condition";

// Very light ZIP -> coords mock (replace with your geocoder/backend)
// const ZIP_TO_COORDS: Record<string, Coords> = {
//   "78701": { lat: 30.2715, lon: -97.7426 },
//   "78756": { lat: 30.3185, lon: -97.7446 },
//   "78758": { lat: 30.3718, lon: -97.7203 },
//   "78704": { lat: 30.2442, lon: -97.7619 },
//   "77840": { lat: 30.6154, lon: -96.3267 }, // College Station (rough)
// };

// ----------------- Utilities -----------------
function haversineMiles(a: Coords, b: Coords) {
  if (!a || !b) return null;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const R = 3958.8; // miles
  const dLat = toRad(b.lat - a.lat);
  const dLon = toRad(b.lon - a.lon);
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);

  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.asin(Math.sqrt(h));
  return R * c;
}

function splitAddress(addr: string) {
  // Expect formats like "3310 Longmire Dr, College Station, TX 77845"
  const [street, rest] = addr.split(",").map((s) => s.trim());
  if (!rest) return { address: addr, city: "", state: "", zip: "" };
  const parts = rest.split(/\s*,\s*/); // ["College Station", "TX 77845"]
  const city = parts[0] || "";
  const stateZip = parts[1] || "";
  const [state, zip] = stateZip.split(/\s+/);
  return { address: street || addr, city, state: state || "", zip: zip || "" };
}

function cleanPhone(maybeCall: string | undefined) {
  // Backend returns like "Call (979) 691-3300"
  if (!maybeCall) return "";
  const m = maybeCall.match(/\(?\d{3}\)?[ -.]?\d{3}[ -.]?\d{4}/);
  return m ? m[0] : maybeCall.replace(/^Call\s*/i, "").trim();
}

// ----------------- Screen -----------------
export default function SearchScreen() {
  // Search inputs
  const [query, setQuery] = useState("");
  const [zip, setZip] = useState(""); // matches your sample
  const [useMyLocation, setUseMyLocation] = useState(false);

  // Location
  const [deviceCoords, setDeviceCoords] = useState<Coords>(null);
  const [zipCoords, setZipCoords] = useState<Coords>(null);
  const [loadingLoc, setLoadingLoc] = useState(false);

  // Sorting
  const [sortOpen, setSortOpen] = useState(false);
  const [sortBy, setSortBy] = useState<"distance" | "score" | "name">("distance");

  // Data
  const [providers, setProviders] = useState<Provider[]>([]);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Which coords drive distance?
  const origin: Coords = useMyLocation ? deviceCoords : zipCoords;

  // --- Location handlers ---
  const handleUseMyLocation = useCallback(async () => {
    try {
      setLoadingLoc(true);
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") {
        setUseMyLocation(false);
        return;
      }
      const loc = await Location.getCurrentPositionAsync({});
      setDeviceCoords({ lat: loc.coords.latitude, lon: loc.coords.longitude });
      setUseMyLocation(true);
    } catch {
      setUseMyLocation(false);
    } finally {
      setLoadingLoc(false);
    }
  }, []);

//   useEffect(() => {
//     const cleaned = zip.trim();
//     setZipCoords(cleaned.length >= 5 ? ZIP_TO_COORDS[cleaned] ?? null : null);
//   }, [zip]);

  // --- Fetch from backend ---
  const runSearch = useCallback(async () => {
    setError(null);
    setFetching(true);
    try {
      // Build the body to match your backend
      const body = {
        query: query || "Find doctors",
        insurance_network: 1,                // you can wire this to UI later
        insurance: "Blue Cross Blue Shield", // ditto
        insurance_id: "ZGP123456789",
        specialty: "Cardiology",
        location: `${zip}`,
        postal_code: zip,
      };
      console.log('here is body -> ', body)

      const res = await fetch(`${API_BASE}/searches/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // Authorization: `Bearer ${token}`, // if your API is protected
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}: ${text}`);
      }

      const json = await res.json();
      const rawProviders: BackendProvider[] = json?.graph_state?.providers ?? [];

      // Map backend -> frontend type
      const mapped: Provider[] = rawProviders.map((p, idx) => {
        const { address, city, state, zip } = splitAddress(p.address);
        return {
          id: `${json.id}-${idx + 1}`,
          name: p.name,
          phone: cleanPhone(p.phone),
          address,
          city,
          state,
          zip,
          lat: p.lat,
          lon: p.lng, // NOTE: backend uses 'lng'; we store 'lon'
          medmatch_score: 7, // TODO: replace with real score when you have it
        };
      });

      setProviders(mapped);
    } catch (e: any) {
      setError(e?.message || "Failed to fetch results");
      setProviders([]);
    } finally {
      setFetching(false);
    }
  }, [API_BASE, query, zip]);

  // --- Distance + sorting computed list ---
  const filteredSorted = useMemo(() => {
    let rows = providers
      .map((p) => {
        const d = haversineMiles(origin, { lat: p.lat, lon: p.lon });
        return { ...p, distance: d };
      }) as (Provider & { distance: number | null })[];

    rows.sort((a, b) => {
      if (sortBy === "distance") {
        const da = a.distance ?? Number.POSITIVE_INFINITY;
        const db = b.distance ?? Number.POSITIVE_INFINITY;
        return da - db;
      }
      if (sortBy === "score") {
        return (b.medmatch_score ?? 0) - (a.medmatch_score ?? 0);
      }
      return a.name.localeCompare(b.name);
    });

    return rows;
  }, [providers, origin, sortBy]);

  return (
    <View style={{ flex: 1, padding: 12, gap: 8 }}>
      {/* Search input */}
      <Searchbar
        placeholder={PROMPT}
        value={query}
        onChangeText={setQuery}
        onSubmitEditing={runSearch}
        style={{ borderRadius: 12 }}
      />

      {/* Location Row */}
      <View style={{ flexDirection: "row", gap: 8 }}>
        <Button
          mode={useMyLocation ? "contained" : "outlined"}
          icon="crosshairs-gps"
          onPress={handleUseMyLocation}
        >
          Use my location
        </Button>

        <TextInput
          label="Search by ZIP"
          mode="outlined"
          keyboardType="number-pad"
          value={zip}
          onChangeText={(t) => {
            setZip(t);
            setUseMyLocation(false);
          }}
          style={{ flex: 1 }}
          right={
            zip ? <TextInput.Icon icon="close" onPress={() => setZip("")} /> : undefined
          }
        />
      </View>

      {/* Status + Sort */}
      <View style={{ flexDirection: "row", gap: 8, alignItems: "center" }}>
        <Chip selected={useMyLocation} onPress={() => setUseMyLocation(true)}>
          Device location
        </Chip>
        <Chip
          selected={!useMyLocation}
          onPress={() => setUseMyLocation(false)}
          disabled={!zipCoords}
        >
          ZIP {zipCoords ? "active" : "—"}
        </Chip>

        <Menu
          visible={sortOpen}
          onDismiss={() => setSortOpen(false)}
          anchor={
            <Button mode="outlined" onPress={() => setSortOpen(true)} icon="sort">
              Sort: {sortBy === "distance" ? "Distance" : sortBy === "score" ? "Score" : "Name"}
            </Button>
          }
        >
          <Menu.Item onPress={() => { setSortBy("distance"); setSortOpen(false); }} title="Distance" />
          <Menu.Item onPress={() => { setSortBy("score"); setSortOpen(false); }} title="MedMatch Score" />
          <Menu.Item onPress={() => { setSortBy("name"); setSortOpen(false); }} title="Name" />
        </Menu>

        <View style={{ flex: 1 }} />

        <Button
          mode="contained"
          icon={fetching ? "progress-clock" : "magnify"}
          onPress={runSearch}
          disabled={fetching}
        >
          {fetching ? "Searching..." : "Search"}
        </Button>
      </View>

      {loadingLoc && (
        <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
          <ActivityIndicator />
          <Text>Fetching device location…</Text>
        </View>
      )}

      {error && <HelperText type="error" visible>{error}</HelperText>}

      <Divider />

      {/* Results */}
      {fetching ? (
        <View style={{ paddingVertical: 24, alignItems: "center" }}>
          <ActivityIndicator />
          <Text>Loading results…</Text>
        </View>
      ) : (
        <FlatList
          data={filteredSorted}
          keyExtractor={(item) => item.id}
          contentContainerStyle={{ gap: 10, paddingVertical: 8 }}
          renderItem={({ item }) => (
            <Card mode="elevated" style={{ borderRadius: 16 }}>
              <Card.Title
                title={item.name}
                right={() => (
                  <View style={{ flexDirection: "row", alignItems: "center" }}>
                    <Chip compact style={{ marginRight: 8 }}>
                      Score: {item.medmatch_score}
                    </Chip>
                    <Chip compact>
                      {item.distance != null ? `${item.distance.toFixed(1)} mi` : "— mi"}
                    </Chip>
                  </View>
                )}
              />
              <Card.Content>
                <Text selectable>{item.phone}</Text>
                <Text selectable>
                  {item.address}
                  {", "}
                  {item.city}, {item.state} {item.zip}
                </Text>
              </Card.Content>
              <Card.Actions>
                <Button
                  icon="phone"
                  onPress={() => {
                    // Linking.openURL(`tel:${item.phone.replace(/\D/g, "")}`)
                  }}
                >
                  Call
                </Button>
                <Button
                  icon="map-marker"
                  onPress={() => {
                    // const q = encodeURIComponent(`${item.address}, ${item.city}, ${item.state} ${item.zip}`);
                    // Linking.openURL(`https://maps.apple.com/?q=${q}`);
                  }}
                >
                  Map
                </Button>
                <View style={{ flex: 1 }} />
                <IconButton icon="chevron-right" onPress={() => { /* navigate to detail */ }} />
              </Card.Actions>
            </Card>
          )}
          ListEmptyComponent={
            <View style={{ paddingVertical: 24, alignItems: "center" }}>
              <Text>No providers found. Try a broader search.</Text>
            </View>
          }
        />
      )}
    </View>
  );
}
