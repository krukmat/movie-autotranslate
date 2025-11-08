import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { Provider as PaperProvider } from "react-native-paper";
import JobsScreen from "./src/screens/JobsScreen";
import UploadScreen from "./src/screens/UploadScreen";
import PlayerScreen from "./src/screens/PlayerScreen";

export type RootStackParamList = {
  Upload: undefined;
  Jobs: undefined;
  Player: { assetId: string };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <PaperProvider>
      <NavigationContainer>
        <Stack.Navigator>
          <Stack.Screen name="Upload" component={UploadScreen} options={{ title: "Upload" }} />
          <Stack.Screen name="Jobs" component={JobsScreen} options={{ title: "Jobs" }} />
          <Stack.Screen name="Player" component={PlayerScreen} options={{ title: "Player" }} />
        </Stack.Navigator>
      </NavigationContainer>
    </PaperProvider>
  );
}
