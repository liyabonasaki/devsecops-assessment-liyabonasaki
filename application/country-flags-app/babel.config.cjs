// CommonJS Babel config (.cjs extension).
// The project's package.json sets "type": "module", which would otherwise make
// a plain babel.config.js be treated as an ES module. Create React App / Babel
// load the config synchronously, which does not support ESM config files, so we
// use the explicit .cjs extension + module.exports to force CommonJS loading.
module.exports = {
  presets: [
    '@babel/preset-env',
    '@babel/preset-react',
  ],
  plugins: [
    '@babel/plugin-transform-runtime',
  ],
};
