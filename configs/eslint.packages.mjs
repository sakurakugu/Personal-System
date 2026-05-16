import js from "@eslint/js"
import vue from "eslint-plugin-vue"
import tseslint from "typescript-eslint"

export default [
  {
    ignores: ["packages/**/dist/**", "packages/**/node_modules/**"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...vue.configs["flat/recommended"],
  {
    files: ["packages/**/*.{ts,tsx,vue,d.ts}"],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
        ecmaVersion: "latest",
        sourceType: "module",
      },
    },
    rules: {
      "no-undef": "off",
      "no-empty": "off",
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-unused-vars": "off",
      "vue/no-mutating-props": "off",
      "vue/no-v-html": "off",
      "vue/attributes-order": "off",
      "vue/max-attributes-per-line": "off",
      "vue/singleline-html-element-content-newline": "off",
      "vue/multi-word-component-names": "off",
    },
  },
]
