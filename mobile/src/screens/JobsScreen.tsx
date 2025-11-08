import { useEffect, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, TouchableOpacity, View } from "react-native";
import { ActivityIndicator, Text } from "react-native-paper";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../../App";
import { fetchJobs, type Job } from "../api";

export default function JobsScreen({ navigation }: NativeStackScreenProps<RootStackParamList, "Jobs">) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadJobs = async () => {
    try {
      setRefreshing(true);
      const results = await fetchJobs();
      setJobs(results);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text>Error: {error}</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={jobs}
      keyExtractor={(job) => job.jobId}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={loadJobs} />}
      renderItem={({ item }) => (
        <TouchableOpacity onPress={() => navigation.navigate("Player", { assetId: item.assetId })}>
          <View style={styles.row}>
            <View>
              <Text variant="titleMedium">Job {item.jobId.slice(0, 6)}</Text>
              <Text>{item.status} · {item.stage}</Text>
            </View>
            <Text>{Math.round(item.progress * 100)}%</Text>
          </View>
        </TouchableOpacity>
      )}
      ListEmptyComponent={<Text style={styles.empty}>No jobs yet. Start one from the Upload screen.</Text>}
      contentContainerStyle={jobs.length === 0 ? styles.center : undefined}
    />
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24
  },
  row: {
    padding: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#ccc",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center"
  },
  empty: {
    marginTop: 24
  }
});
