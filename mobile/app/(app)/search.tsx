// app/(app)/search.tsx
import React, { useEffect, useMemo, useState } from "react";
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
} from "react-native-paper";

// If you use Expo, install expo-location for "Use my location":
//   npx expo install expo-location
// and then uncomment the imports and code below.
import * as Location from "expo-location";

type Provider = {
  id: string;
  name: string;
  phone: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  lat: number;
  lon: number;
  medmatch_score: number; // 1-10
};

type Coords = { lat: number; lon: number } | null;

const PROMPT = "Search by specialty, symptoms, or condition";

// --- Mock provider data ---
const MOCK: Provider[] = [
  {
    id: "1",
    name: "Dr. Alicia Patel, MD",
    phone: "(512) 555-0143",
    address: "123 Main St",
    city: "Austin",
    state: "TX",
    zip: "78701",
    lat: 30.2715,
    lon: -97.7426,
    medmatch_score: 9,
  },
  {
    id: "2",
    name: "Riverbend Family Clinic",
    phone: "(512) 555-0199",
    address: "4501 Shoal Creek Blvd",
    city: "Austin",
    state: "TX",
    zip: "78756",
    lat: 30.3185,
    lon: -97.7446,
    medmatch_score: 7,
  },
  {
    id: "3",
    name: "Bryan Goerig, MD",
    phone: "(979) 703-1902",
    address: "1730 Birmingham Rd.",
    city: "College Station",
    state: "TX",
    zip: "77845",
    lat: 30.601389,
    lon: -96.314445,
    medmatch_score: 8,
  },
  {
    id: "4",
    name: "Southside Cardiology Group",
    phone: "(512) 555-8811",
    address: "2100 S 1st St",
    city: "Austin",
    state: "TX",
    zip: "78704",
    lat: 30.2442,
    lon: -97.7619,
    medmatch_score: 10,
  },
];

// --- Utilities ---
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

// Super-light ZIP → coords mock (replace with your geocoder/backend)
const ZIP_TO_COORDS: Record<string, Coords> = {
  "78701": { lat: 30.2715, lon: -97.7426 },
  "78756": { lat: 30.3185, lon: -97.7446 },
  "78758": { lat: 30.3718, lon: -97.7203 },
  "78704": { lat: 30.2442, lon: -97.7619 },
};

export default function SearchScreen() {
  const [query, setQuery] = useState("");
  const [zip, setZip] = useState("");
  const [useMyLocation, setUseMyLocation] = useState(false);
  const [deviceCoords, setDeviceCoords] = useState<Coords>(null);
  const [zipCoords, setZipCoords] = useState<Coords>(null);
  const [loadingLoc, setLoadingLoc] = useState(false);

  const [sortOpen, setSortOpen] = useState(false);
  const [sortBy, setSortBy] = useState<"distance" | "score" | "name">("distance");

  // On "Use my location", request location (Expo). Fallback: leave coords null.
  const handleUseMyLocation = async () => {
    // If you want live device location, uncomment this block and the import.
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
    } finally {
      setLoadingLoc(false);
    }
    // Mock fallback (Austin City Hall):
    setLoadingLoc(true);
    setTimeout(() => {
      setDeviceCoords({ lat: 30.2654, lon: -97.7431 });
      setUseMyLocation(true);
      setLoadingLoc(false);
    }, 600);
  };

  // When ZIP changes, set coords from our mock map
  useEffect(() => {
    const cleaned = zip.trim();
    setZipCoords(cleaned.length >= 5 ? ZIP_TO_COORDS[cleaned] ?? null : null);
  }, [zip]);

  // Which coords drive distance?
  const origin: Coords = useMyLocation ? deviceCoords : zipCoords;

  // Filter & sort the mock data
  const filteredSorted = useMemo(() => {
    const q = query.trim().toLowerCase();
    let rows = MOCK.filter((p) => {
      if (!q) return true;
      // fields to match for the demo; expand as needed
      const hay =
        `${p.name} ${p.address} ${p.city} ${p.state} ${p.zip}`.toLowerCase();
      return hay.includes(q);
    }).map((p) => {
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
      // name
      return a.name.localeCompare(b.name);
    });

    return rows;
  }, [query, origin, sortBy]);

  return (
    <View style={{ flex: 1, padding: 12, gap: 8 }}>
      {/* Search input */}
      <Searchbar
        placeholder={PROMPT}
        value={query}
        onChangeText={setQuery}
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
            zip ? (
              <TextInput.Icon icon="close" onPress={() => setZip("")} />
            ) : undefined
          }
        />
      </View>

      {/* Status chips */}
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

        {/* Sort Menu */}
        <Menu
          visible={sortOpen}
          onDismiss={() => setSortOpen(false)}
          anchor={
            <Button
              mode="outlined"
              onPress={() => setSortOpen(true)}
              icon="sort"
            >
              Sort: {sortBy === "distance" ? "Distance" : sortBy === "score" ? "Score" : "Name"}
            </Button>
          }
        >
          <Menu.Item
            onPress={() => {
              setSortBy("distance");
              setSortOpen(false);
            }}
            title="Distance"
          />
          <Menu.Item
            onPress={() => {
              setSortBy("score");
              setSortOpen(false);
            }}
            title="MedMatch Score"
          />
          <Menu.Item
            onPress={() => {
              setSortBy("name");
              setSortOpen(false);
            }}
            title="Name"
          />
        </Menu>
      </View>

      {/* Loading indicator for location */}
      {loadingLoc && (
        <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
          <ActivityIndicator />
          <Text>Fetching device location…</Text>
        </View>
      )}

      <Divider />

      {/* Results */}
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
                    {item.distance != null
                      ? `${item.distance.toFixed(1)} mi`
                      : "— mi"}
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
                  // Example: Linking.openURL(`tel:${item.phone}`)
                }}
              >
                Call
              </Button>
              <Button
                icon="map-marker"
                onPress={() => {
                  // Example: Linking.openURL(`https://maps.apple.com/?q=${encodeURIComponent(item.address + " " + item.city)}`)
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
    </View>
  );
}
