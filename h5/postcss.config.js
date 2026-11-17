import pxToViewport from 'postcss-px-to-viewport-8-plugin'

export default {
  plugins: [
    pxToViewport({
      viewportWidth: 375,
      unitPrecision: 5,
      propList: ['*'],
      selectorBlackList: ['.ignore-vw'],
      minPixelValue: 2,
      mediaQuery: false,
    }),
  ],
}
