export default {
  extends: ['stylelint-config-standard'],
  ignoreFiles: ['dist/**', 'src/**/*.vue'],
  rules: {
    'no-descending-specificity': null,
  },
}
