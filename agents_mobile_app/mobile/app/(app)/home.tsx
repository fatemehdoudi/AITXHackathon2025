// app/(app)/home.tsx
import { View } from "react-native";
import { Text, Button } from "react-native-paper";
export default function Home() {
  return (
    <View style={{ flex:1, padding:16 }}>
      <Text variant="headlineSmall" style={{ marginBottom: 12 }}>Welcome to MedMatch</Text>
      <Text variant="bodyMedium">Find care faster with tailored matches.</Text>
    </View>
  );
}
