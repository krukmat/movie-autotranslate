import { StyleSheet, View } from "react-native";
import { Button, Text } from "react-native-paper";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import type { RootStackParamList } from "../../App";

export default function UploadScreen({ navigation }: NativeStackScreenProps<RootStackParamList, "Upload">) {
  return (
    <View style={styles.container}>
      <Text variant="headlineSmall">Upload (Coming Soon)</Text>
      <Text style={styles.copy}>
        Use the web dashboard to upload large media files. Once a job is enqueued you can monitor and play it back here.
      </Text>
      <Button mode="contained" onPress={() => navigation.navigate("Jobs")}>View Jobs</Button>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24
  },
  copy: {
    marginVertical: 16,
    textAlign: "center"
  }
});
