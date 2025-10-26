// app/(app)/saved.tsx
import { View, FlatList } from "react-native";
import { Text, Card, Button } from "react-native-paper";
const mock = [];
export default function Saved() {
  return (
    <View style={{ flex:1, padding:16 }}>
      <Text variant="titleMedium" style={{ marginBottom: 8 }}>Saved Providers</Text>
      {mock.length === 0 ? (
        <Text variant="bodyMedium">No saved providers yet.</Text>
      ) : (
        <FlatList data={mock} keyExtractor={(i:any)=>String(i.id)} renderItem={({item})=>(
          <Card style={{ marginBottom: 10 }}>
            <Card.Title title={item.name} subtitle={item.specialty} />
            <Card.Actions>
              <Button>Remove</Button>
            </Card.Actions>
          </Card>
        )}/>
      )}
    </View>
  );
}
