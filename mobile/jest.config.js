module.exports = {
  preset: "react-native",
  moduleFileExtensions: ["ts", "tsx", "js"],
  transformIgnorePatterns: ["node_modules/(?!(@react-native|react-native|react-native-video|expo-.*)/)"],
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"]
};
