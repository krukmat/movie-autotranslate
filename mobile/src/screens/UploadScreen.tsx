import { useState } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { Button, Checkbox, HelperText, Text, TextInput } from "react-native-paper";
import * as DocumentPicker from "expo-document-picker";
import * as FileSystem from "expo-file-system";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../../App";
import { completeUpload, createJob, initUpload } from "../api";

const languages = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" }
];

const presets = [
  { value: "neutral", label: "Neutral" },
  { value: "female_bright", label: "Female Bright" },
  { value: "male_deep", label: "Male Deep" },
  { value: "elderly_female", label: "Elderly Female" },
  { value: "elderly_male", label: "Elderly Male" }
];

export default function UploadScreen({ navigation }: NativeStackScreenProps<RootStackParamList, "Upload">) {
  const [pickedFile, setPickedFile] = useState<DocumentPicker.DocumentPickerAsset | null>(null);
  const [targetLangs, setTargetLangs] = useState<string[]>(["es"]);
  const [preset, setPreset] = useState("neutral");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const pickFile = async () => {
    const result = await DocumentPicker.getDocumentAsync({ type: ["video/*", "audio/*"] });
    if (result.type === "success") {
      setPickedFile(result.assets[0]);
      setError(null);
    }
  };

  const toggleLanguage = (value: string) => {
    setTargetLangs((prev) => (prev.includes(value) ? prev.filter((lang) => lang !== value) : [...prev, value]));
  };

  const handleSubmit = async () => {
    if (!pickedFile) {
      setError("Select a video or audio file.");
      return;
    }
    if (targetLangs.length === 0) {
      setError("Pick at least one target language.");
      return;
    }
    setError(null);
    try {
      setStatus("Creating upload session...");
      const init = await initUpload(pickedFile.name, pickedFile.size ?? 0, pickedFile.mimeType ?? "application/octet-stream");
      const uploadUrl = init.parts[0].uploadUrl;
      setStatus("Uploading file...");
      await FileSystem.uploadAsync(uploadUrl, pickedFile.uri, {
        httpMethod: "PUT",
        headers: { "Content-Type": pickedFile.mimeType ?? "application/octet-stream" },
        uploadType: FileSystem.FileSystemUploadType.BINARY_CONTENT
      });
      setStatus("Finalizing...");
      await completeUpload(init.assetId, init.uploadId, "en", targetLangs, ["mobile-etag"]);
      setStatus("Starting job...");
      const job = await createJob(init.assetId, targetLangs, { default: preset });
      setStatus(null);
      navigation.navigate("Jobs");
    } catch (err) {
      setStatus(null);
      setError((err as Error).message);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text variant="headlineSmall">Upload & Translate</Text>
      <Button mode="contained-tonal" style={styles.pickButton} onPress={pickFile}>
        {pickedFile ? "Change File" : "Select File"}
      </Button>
      {pickedFile && (
        <Text style={styles.fileInfo}>
          {pickedFile.name} ({Math.round((pickedFile.size ?? 0) / (1024 * 1024))} MB)
        </Text>
      )}
      <View style={styles.section}>
        <Text variant="titleMedium">Target languages</Text>
        {languages.map((lang) => (
          <View key={lang.value} style={styles.checkboxRow}>
            <Checkbox status={targetLangs.includes(lang.value) ? "checked" : "unchecked"} onPress={() => toggleLanguage(lang.value)} />
            <Text>{lang.label}</Text>
          </View>
        ))}
      </View>
      <View style={styles.section}>
        <Text variant="titleMedium">Voice preset</Text>
        <TextInput
          mode="outlined"
          value={preset}
          onChangeText={setPreset}
          placeholder="neutral"
          right={<TextInput.Affix text="/ preset" />}
        />
        <HelperText type="info">Presets: {presets.map((p) => p.value).join(", ")}</HelperText>
      </View>
      {status && <Text>{status}</Text>}
      {error && <HelperText type="error">{error}</HelperText>}
      <Button mode="contained" onPress={handleSubmit} disabled={!pickedFile || targetLangs.length === 0}>
        Start dubbing job
      </Button>
      <Button mode="text" onPress={() => navigation.navigate("Jobs")}>
        View jobs
      </Button>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 24,
    gap: 16
  },
  pickButton: {
    marginTop: 12
  },
  fileInfo: {
    fontSize: 14
  },
  section: {
    marginTop: 16
  },
  checkboxRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8
  }
});
