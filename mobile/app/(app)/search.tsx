// app/(app)/search.tsx
import { View } from "react-native";
import { TextInput, Button, Text } from "react-native-paper";
import { useState } from "react";
export default function Search() {
  const [q, setQ] = useState("");
  return (
    <View style={{ flex:1, padding:16, gap:12 }}>
      <Text variant="titleMedium">Search Providers</Text>
      <TextInput label="Specialty, name, or condition" mode="outlined" value={q} onChangeText={setQ} />
      <Button mode="contained" onPress={() => {/* call API */}}>Search</Button>
    </View>
  );
}
