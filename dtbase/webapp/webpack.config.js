const path = require("path");
const glob = require("glob");

// Dynamically generate entry points
const entries = {};
glob.sync("./app/base/static/typescript/**/*.ts").forEach((filePath) => {
  const entry = path.basename(filePath).replace(/\.[^.]+$/, ""); // remove extension
  entries[entry] = "./" + filePath;
});

module.exports = {
  entry: entries,
  devtool: "source-map",
  module: {
    rules: [
      {
        test: /\.ts$/,
        use: "ts-loader",
        exclude: /node_modules/,
      },
    ],
  },
  resolve: {
    extensions: [".ts", ".js"],
  },
  output: {
    filename: "[name].js",
    path: path.resolve(__dirname, "./app/base/static/javascript"),
  },
};
