import js from "@eslint/js";

const appsScriptGlobals = {
  ContentService: "readonly",
  DriveApp: "readonly",
  JSON: "readonly",
  PropertiesService: "readonly",
  ScriptApp: "readonly",
  Session: "readonly",
  SpreadsheetApp: "readonly",
  String: "readonly",
  UrlFetchApp: "readonly",
  Utilities: "readonly",
};

export default [
  {
    ignores: [
      "archive/**",
      "node_modules/**",
      "ov10_codex_handoff/**",
    ],
  },
  js.configs.recommended,
  {
    files: ["apps_script_debug_bridge/**/*.gs"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "script",
      globals: appsScriptGlobals,
    },
    rules: {
      "no-undef": "error",
      "no-unused-vars": [
        "error",
        {
          args: "after-used",
          caughtErrors: "all",
          caughtErrorsIgnorePattern: "^error$",
          varsIgnorePattern: "^(doGet|doPost)$",
        },
      ],
    },
  },
];
