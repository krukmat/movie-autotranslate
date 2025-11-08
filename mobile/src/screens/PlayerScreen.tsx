import { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import Video from "react-native-video";
import { ActivityIndicator, Text } from "react-native-paper";
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
  if (!masterUrl) {
    return (
      <View style={styles.center}>
        <Text>No published audio yet.</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Video source={{ uri: masterUrl }} controls style={styles.video} resizeMode="contain" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#000"
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
