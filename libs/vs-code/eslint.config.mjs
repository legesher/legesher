import eslint from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["out/**", "node_modules/**", "**/*.js"] },
  {
    files: ["src/**/*.ts"],
    extends: [eslint.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: {
      parserOptions: {
        ecmaVersion: 2020,
        sourceType: "module",
      },
    },
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/no-explicit-any": "warn",
      "no-console": "off",
    },
  },
);
