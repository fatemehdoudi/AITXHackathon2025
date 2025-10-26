// app/_layout.tsx
import { Stack } from "expo-router";
import { PaperProvider, MD3LightTheme, configureFonts } from "react-native-paper";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { useEffect } from "react";
import * as SplashScreen from "expo-splash-screen";

const fonts = configureFonts({ config: { fontFamily: "System" } });
const theme = {
  ...MD3LightTheme,
  fonts,
  colors: {
    ...MD3LightTheme.colors,
    primary: "#094dabff", // MedMatch green vibe
    secondary: "#3487e4ff",
  },
};

SplashScreen.preventAutoHideAsync();

export default function Layout() {
  useEffect(() => {
    // keep it simple; hide immediately after mount
    SplashScreen.hideAsync().catch(() => {});
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <PaperProvider theme={theme}>
          <Stack screenOptions={{ headerShown: false }} />
        </PaperProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
