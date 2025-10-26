// app/(app)/settings.tsx
import { View } from "react-native";
import { Text, Switch, List, Divider } from "react-native-paper";
import { useState } from "react";
export default function Settings() {
  const [push, setPush] = useState(true);
  return (
    <View style={{ flex:1 }}>
      <List.Section>
        <List.Subheader>Preferences</List.Subheader>
        <List.Item
          title="Push notifications"
          right={() => <Switch value={push} onValueChange={setPush} />}
        />
        <Divider />
        <List.Item title="Account" description="Update email, password, insurance" />
        <Divider />
        <List.Item title="About MedMatch" />
      </List.Section>
    </View>
  );
}
