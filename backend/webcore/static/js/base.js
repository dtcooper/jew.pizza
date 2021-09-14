/* global Alpine, DATA */

document.addEventListener('alpine:init', () => {
  Alpine.data('bodyColors', () => ({
    randomColors: [
      // Selected from https://brainstormstra.wpengine.com/cyberpunk-design-style/
      'bg-[#9a154c]', 'bg-[#f64d54]', 'bg-[#118171]', 'bg-[#f5a439]', 'bg-[#031efd]',
      'bg-[#811278]', 'bg-[#4f3b78]', 'bg-[#cc168d]', 'bg-[#caff01]', 'bg-[#06b7ff]',
      'bg-[#ff0182]', 'bg-[#01ff11]', 'bg-[#00ffec]', 'bg-[#a403ff]', 'bg-[#be00fe]',
      'bg-[#38fbdb]', 'bg-[#fc11f5]', 'bg-[#8f52f5]', 'bg-[#fdfe00]', 'bg-[#00ffa0]',
      'bg-[#00ffd3]', 'bg-[#afff01]', 'bg-[#fd01f3]', 'bg-[#e301ff]', 'bg-[#d600fe]'
    ],
    init () {
      this.pickColor()
      if (!(DATA.is_superuser || DATA.debug)) { // Don't murder my eyes
        setInterval(() => this.pickColor(), 2000)
      }
    },
    pickColor () {
      this.currentColor = this.randomColors[Math.floor(Math.random() * this.randomColors.length)]
    }
  }))
})
