import { useEffect, useMemo, useState } from "react";
import { StyleSheet, View } from "react-native";
import Video from "react-native-video";
import { ActivityIndicator, Button, Text } from "react-native-paper";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../../App";
import { fetchAsset, type Asset } from "../api";

export default function PlayerScreen({ route }: NativeStackScreenProps<RootStackParamList, "Player">) {
  const { assetId } = route.params;
  const [asset, setAsset] = useState<Asset | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAsset(assetId)
      .then((data) => setAsset(data))
      .catch((err) => setError((err as Error).message));
  }, [assetId]);

  if (error) {
    return (
      <View style={styles.center}>
        <Text>Error: {error}</Text>
      </View>
    );
  }

  if (!asset) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }

  const masterUrl = asset.outputs.hls || asset.storageKeys.public;
  const availableTracks = useMemo(() => {
    return Object.entries(asset.storageKeys)
      .filter(([key]) => key.startsWith("public_"))
      .map(([key, value]) => ({ language: key.replace("public_", ""), url: value }));
  }, [asset.storageKeys]);
  const [selectedTrack, setSelectedTrack] = useState(masterUrl);
  useEffect(() => {
    setSelectedTrack(masterUrl);
  }, [masterUrl]);
  if (!masterUrl) {
    return (
      <View style={styles.center}>
        <Text>No published audio yet.</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.trackSelector}>
        <Button mode="outlined" onPress={() => setSelectedTrack(masterUrl)} compact>
          Master
        </Button>
        {availableTracks.map((track) => (
          <Button key={track.language} mode={selectedTrack === track.url ? "contained" : "outlined"} compact onPress={() => setSelectedTrack(track.url)}>
            {track.language.toUpperCase()}
          </Button>
        ))}
      </View>
      <Video source={{ uri: selectedTrack }} controls style={styles.video} resizeMode="contain" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#000"
  },
  trackSelector: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    padding: 12,
    backgroundColor: "#111"
  },
  video: {
    flex: 1
  },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center"
  }
});
