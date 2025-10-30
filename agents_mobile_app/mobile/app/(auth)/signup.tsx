// app/(auth)/signup.tsx
import { useState } from "react";
import { View, KeyboardAvoidingView, Platform } from "react-native";
import { TextInput, Button, Text, HelperText, Snackbar, Card } from "react-native-paper";
import { useRouter } from "expo-router";
import { registerAccount, loginWithPassword } from "../../lib/auth";

export default function SignupScreen() {
  const router = useRouter();
  const [first, setFirst] = useState("");
  const [last, setLast] = useState("");
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const emailInvalid = !!email && !/^\S+@\S+\.\S+$/.test(email);
  const pwWeak = !!pw && pw.length < 8;
  const pwMismatch = !!pw && !!pw2 && pw !== pw2;

  async function onCreate() {
    setErr(null);
    setMsg(null);
    if (emailInvalid || pwWeak || pwMismatch) {
      setErr("Fix the highlighted fields and try again.");
      return;
    }
    setLoading(true);
    try {
      await registerAccount({
        email: email.trim(),
        password: pw,
        first_name: first.trim(),
        last_name: last.trim(),
      });
      // optional: auto-login after successful registration
      await loginWithPassword(email.trim(), pw);
      setMsg("Account created. Welcome to MedMatch!");
      router.replace("/home"); // change to your post-login route
    } catch (e: any) {
      setErr(e.message || "Registration failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView behavior={Platform.select({ ios: "padding", android: undefined })} style={{ flex: 1 }}>
      <View style={{ flex: 1, padding: 24, justifyContent: "center" }}>
        <Card mode="elevated" style={{ padding: 16 }}>
          <Text variant="headlineMedium" style={{ marginBottom: 8, fontWeight: "700" }}>
            Create your MedMatch account
          </Text>

          <TextInput
            label="First name"
            mode="outlined"
            value={first}
            onChangeText={setFirst}
            left={<TextInput.Icon icon="account-outline" />}
            style={{ marginBottom: 8 }}
          />
          <TextInput
            label="Last name"
            mode="outlined"
            value={last}
            onChangeText={setLast}
            left={<TextInput.Icon icon="account-outline" />}
            style={{ marginBottom: 8 }}
          />

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
            {emailInvalid ? "Enter a valid email address." : "You’ll use this to sign in."}
          </HelperText>

          <TextInput
            label="Password"
            mode="outlined"
            value={pw}
            onChangeText={setPw}
            secureTextEntry={!showPw}
            left={<TextInput.Icon icon="lock-outline" />}
            right={<TextInput.Icon icon={showPw ? "eye-off-outline" : "eye-outline"} onPress={() => setShowPw((x) => !x)} />}
            error={pwWeak}
            style={{ marginBottom: 4 }}
          />
          <HelperText type={pwWeak ? "error" : "info"} visible={!!pw}>
            {pwWeak ? "Use at least 8 characters." : "Use a strong, unique password."}
          </HelperText>

          <TextInput
            label="Confirm password"
            mode="outlined"
            value={pw2}
            onChangeText={setPw2}
            secureTextEntry={!showPw}
            left={<TextInput.Icon icon="lock-check-outline" />}
            error={pwMismatch}
            style={{ marginBottom: 12 }}
          />
          <HelperText type={pwMismatch ? "error" : "info"} visible={!!pw2}>
            {pwMismatch ? "Passwords do not match." : "Re-enter your password."}
          </HelperText>

          <Button mode="contained" onPress={onCreate} loading={loading} disabled={loading}>
            Create Account
          </Button>
          <Button mode="text" onPress={() => router.back()} style={{ marginTop: 8 }}>
            Back to Sign In
          </Button>
        </Card>
      </View>

      <Snackbar visible={!!err} onDismiss={() => setErr(null)} duration={4000} action={{ label: "OK", onPress: () => setErr(null) }}>
        {err}
      </Snackbar>
      <Snackbar visible={!!msg} onDismiss={() => setMsg(null)} duration={2500}>
        {msg}
      </Snackbar>
    </KeyboardAvoidingView>
  );
}
