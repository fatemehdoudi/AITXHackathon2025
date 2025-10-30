import { View } from "react-native";
import { Text } from "react-native-paper";
export default function Home() {
  return (
    <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
      <Text variant="headlineSmall">Welcome to MedMatch</Text>
    </View>
  );
}
