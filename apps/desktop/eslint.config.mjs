import js from "@eslint/js"
import vue from "eslint-plugin-vue"
import tseslint from "typescript-eslint"

export default [
  {
    // 意思是不参与 lint 的检查
    ignores: ["dist/**", "node_modules/**", "build/**", "python/**", "python-runtime/**"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...vue.configs["flat/recommended"],
  {
    files: ["**/*.{ts,tsx,vue,mjs}"],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
        sourceType: "module"
      },
      globals: {
        __dirname: "readonly",
        console: "readonly",
        document: "readonly",
        fetch: "readonly",
        globalThis: "readonly",
        localStorage: "readonly",
        process: "readonly",
        navigator: "readonly",
        URL: "readonly",
        window: "readonly"
      }
    },
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-unused-vars": "off",
      "vue/max-attributes-per-line": "off",
      "vue/singleline-html-element-content-newline": "off",
      "vue/multi-word-component-names": "off"
    }
  }
]
