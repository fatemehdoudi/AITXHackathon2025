// app/(auth)/login.tsx
import { useState } from "react";
import { View, KeyboardAvoidingView, Platform } from "react-native";
import { TextInput, Button, Text, HelperText, IconButton, Snackbar, Card } from "react-native-paper";
import { Link, useRouter } from "expo-router";
import { loginWithPassword } from "../../lib/auth";

export default function LoginScreen() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const emailInvalid = !!email && !/^\S+@\S+\.\S+$/.test(email);

  async function onLogin() {
    setErr(null);
    if (emailInvalid || !pw) {
      setErr("Please enter a valid email and password.");
      return;
    }
    setLoading(true);
    try {
      await loginWithPassword(email.trim(), pw);
      router.replace("/home"); // change to your post-login route
    } catch (e: any) {
      setErr(e.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView behavior={Platform.select({ ios: "padding", android: undefined })} style={{ flex: 1 }}>
      <View style={{ flex: 1, padding: 24, justifyContent: "center" }}>
        <Card mode="elevated" style={{ padding: 16 }}>
          <Text variant="headlineMedium" style={{ marginBottom: 8, fontWeight: "700" }}>
            MedMatch
          </Text>
          <Text variant="titleMedium" style={{ marginBottom: 16 }}>
            Sign in to continue
          </Text>

          <TextInput
            label="Email"
            mode="outlined"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            left={<TextInput.Icon icon="email-outline" />}
            error={emailInvalid}
            style={{ marginBottom: 8 }}
          />
          <HelperText type={emailInvalid ? "error" : "info"} visible={!!email}>
            {emailInvalid ? "Enter a valid email address." : "Use the email you registered with."}
          </HelperText>

          <TextInput
            label="Password"
            mode="outlined"
            value={pw}
            onChangeText={setPw}
            secureTextEntry={!showPw}
            left={<TextInput.Icon icon="lock-outline" />}
            right={
              <TextInput.Icon
                icon={showPw ? "eye-off-outline" : "eye-outline"}
                onPress={() => setShowPw((x) => !x)}
              />
            }
            style={{ marginBottom: 16 }}
          />

          <Button mode="contained" onPress={onLogin} loading={loading} disabled={loading} style={{ marginBottom: 8 }}>
            Sign In
          </Button>
          <Button mode="text" onPress={() => router.push("/(auth)/signup")}>
            Create a MedMatch account
          </Button>
        </Card>
      </View>

      <Snackbar visible={!!err} onDismiss={() => setErr(null)} duration={4000} action={{ label: "OK", onPress: () => setErr(null) }}>
        {err}
      </Snackbar>
    </KeyboardAvoidingView>
  );
}
